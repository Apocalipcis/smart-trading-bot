"""
Binance USDT-M Futures client for REST and WebSocket operations.
"""
import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import httpx
import websockets
from pydantic import BaseModel, Field

from .validators import BinanceValidator


class BinanceConfig(BaseModel):
    """Binance API configuration."""
    rest_url: str = Field(default="https://fapi.binance.com")
    ws_url: str = Field(default="wss://fstream.binance.com")
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    timeout: int = Field(default=30)
    max_retries: int = Field(default=3)


class KlineData(BaseModel):
    """Kline/candlestick data model."""
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    trades: int
    taker_buy_base: float
    taker_buy_quote: float


class TradeData(BaseModel):
    """Trade data model."""
    id: int
    price: float
    qty: float
    quote_qty: float
    time: int
    is_buyer_maker: bool


class BookTickerData(BaseModel):
    """Book ticker data model."""
    symbol: str
    bid_price: float
    bid_qty: float
    ask_price: float
    ask_qty: float
    time: int


class BinanceClient:
    """Binance USDT-M Futures client with REST and WebSocket support."""
    
    def __init__(self, config: BinanceConfig):
        self.config = config
        self.validator = BinanceValidator()
        self._session: Optional[httpx.AsyncClient] = None
        self._ws: Optional[websockets.WebSocketServerProtocol] = None
        
    async def __aenter__(self):
        self._session = httpx.AsyncClient(
            timeout=self.config.timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.aclose()
        if self._ws:
            await self._ws.close()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """Make HTTP request with retries and error handling."""
        url = f"{self.config.rest_url}{endpoint}"
        
        if params is None:
            params = {}
            
        if signed and self.config.api_key and self.config.api_secret:
            params['timestamp'] = int(time.time() * 1000)
            # Note: In production, implement proper signature generation
            params['signature'] = "dummy_signature"  # Placeholder
            
        headers = {}
        if self.config.api_key:
            headers['X-MBX-APIKEY'] = self.config.api_key
            
        for attempt in range(self.config.max_retries):
            try:
                response = await self._session.request(
                    method, url, params=params, headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information including symbol rules."""
        return await self._make_request("GET", "/fapi/v1/exchangeInfo")
    
    async def get_klines(
        self, 
        symbol: str, 
        interval: str, 
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[KlineData]:
        """Get kline/candlestick data."""
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': min(limit, 1000)
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
            
        data = await self._make_request("GET", "/fapi/v1/klines", params)
        
        klines = []
        for item in data:
            kline = KlineData(
                open_time=item[0],
                open=float(item[1]),
                high=float(item[2]),
                low=float(item[3]),
                close=float(item[4]),
                volume=float(item[5]),
                close_time=item[6],
                quote_volume=float(item[7]),
                trades=int(item[8]),
                taker_buy_base=float(item[9]),
                taker_buy_quote=float(item[10])
            )
            klines.append(kline)
            
        return klines

    async def get_klines_multi_timeframe(
        self,
        symbol: str,
        intervals: List[str],
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Dict[str, List[KlineData]]:
        """
        Get kline data for multiple timeframes in parallel.
        
        Args:
            symbol: Trading symbol
            intervals: List of timeframe intervals
            limit: Number of klines per timeframe
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            
        Returns:
            Dict[str, List[KlineData]]: Dictionary mapping intervals to kline data
        """
        import asyncio
        
        # Create tasks for parallel execution
        tasks = []
        for interval in intervals:
            task = self.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                start_time=start_time,
                end_time=end_time
            )
            tasks.append((interval, task))
        
        # Execute all tasks in parallel
        results = {}
        for interval, task in tasks:
            try:
                klines = await task
                results[interval] = klines
            except Exception as e:
                # Log error but continue with other timeframes
                print(f"Error fetching {interval} data for {symbol}: {e}")
                results[interval] = []
        
        return results

    async def validate_timeframe(self, interval: str) -> bool:
        """
        Validate if a timeframe is supported by the exchange.
        
        Args:
            interval: Timeframe interval to validate
            
        Returns:
            bool: True if timeframe is supported, False otherwise
        """
        # Binance supported intervals
        supported_intervals = [
            '1m', '3m', '5m', '15m', '30m',
            '1h', '2h', '4h', '6h', '8h', '12h',
            '1d', '3d', '1w', '1M'
        ]
        
        return interval in supported_intervals

    async def get_timeframe_limits(self) -> Dict[str, Dict[str, int]]:
        """
        Get timeframe-specific limits and constraints.
        
        Returns:
            Dict[str, Dict[str, int]]: Limits for each timeframe
        """
        return {
            '1m': {'max_klines': 1000, 'min_klines': 1},
            '3m': {'max_klines': 1000, 'min_klines': 1},
            '5m': {'max_klines': 1000, 'min_klines': 1},
            '15m': {'max_klines': 1000, 'min_klines': 1},
            '30m': {'max_klines': 1000, 'min_klines': 1},
            '1h': {'max_klines': 1000, 'min_klines': 1},
            '2h': {'max_klines': 1000, 'min_klines': 1},
            '4h': {'max_klines': 1000, 'min_klines': 1},
            '6h': {'max_klines': 1000, 'min_klines': 1},
            '8h': {'max_klines': 1000, 'min_klines': 1},
            '12h': {'max_klines': 1000, 'min_klines': 1},
            '1d': {'max_klines': 1000, 'min_klines': 1},
            '3d': {'max_klines': 1000, 'min_klines': 1},
            '1w': {'max_klines': 1000, 'min_klines': 1},
            '1M': {'max_klines': 1000, 'min_klines': 1}
        }
    
    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[TradeData]:
        """Get recent trades for a symbol."""
        params = {
            'symbol': symbol.upper(),
            'limit': min(limit, 1000)
        }
        
        data = await self._make_request("GET", "/fapi/v1/trades", params)
        
        trades = []
        for item in data:
            trade = TradeData(
                id=int(item['id']),
                price=float(item['price']),
                qty=float(item['qty']),
                quote_qty=float(item['quoteQty']),
                time=item['time'],
                is_buyer_maker=item['isBuyerMaker']
            )
            trades.append(trade)
            
        return trades
    
    async def get_book_ticker(self, symbol: str) -> BookTickerData:
        """Get book ticker for a symbol."""
        params = {'symbol': symbol.upper()}
        data = await self._make_request("GET", "/fapi/v1/ticker/bookTicker", params)
        
        return BookTickerData(
            symbol=data['symbol'],
            bid_price=float(data['bidPrice']),
            bid_qty=float(data['bidQty']),
            ask_price=float(data['askPrice']),
            ask_qty=float(data['askQty']),
            time=int(data['time'])
        )
    
    async def get_24hr_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get 24hr ticker statistics."""
        params = {'symbol': symbol.upper()}
        return await self._make_request("GET", "/fapi/v1/ticker/24hr", params)
    
    async def get_server_time(self) -> Dict[str, Any]:
        """Get server time for synchronization."""
        return await self._make_request("GET", "/fapi/v1/time")
    
    async def connect_websocket(self, streams: List[str]) -> websockets.WebSocketServerProtocol:
        """Connect to WebSocket streams."""
        stream_param = '/'.join(streams)
        ws_url = f"{self.config.ws_url}/stream?streams={stream_param}"
        
        self._ws = await websockets.connect(ws_url)
        return self._ws
    
    async def subscribe_kline_stream(self, symbol: str, interval: str) -> str:
        """Subscribe to kline stream."""
        stream_name = f"{symbol.lower()}@kline_{interval}"
        return stream_name
    
    async def subscribe_trade_stream(self, symbol: str) -> str:
        """Subscribe to trade stream."""
        stream_name = f"{symbol.lower()}@trade"
        return stream_name
    
    async def subscribe_book_ticker_stream(self, symbol: str) -> str:
        """Subscribe to book ticker stream."""
        stream_name = f"{symbol.lower()}@bookTicker"
        return stream_name
