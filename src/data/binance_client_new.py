"""
Binance USDT-M Futures client using python-binance library.

This module provides a simplified interface to Binance API using the official
python-binance library instead of custom HTTP client implementation.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from binance import AsyncClient
from binance.exceptions import BinanceAPIException, BinanceRequestException

logger = logging.getLogger(__name__)


class BinanceConfig(BaseModel):
    """Binance API configuration."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    testnet: bool = Field(default=False)
    tld: str = Field(default="com")  # com, us, jp, etc.
    timeout: int = Field(default=30)


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


class BinanceClient:
    """Binance client using python-binance library."""
    
    def __init__(self, config: BinanceConfig):
        self.config = config
        self._client: Optional[AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = await AsyncClient.create(
            api_key=self.config.api_key,
            api_secret=self.config.api_secret,
            testnet=self.config.testnet,
            tld=self.config.tld
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.close_connection()
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information including symbol rules."""
        try:
            info = await self._client.futures_exchange_info()
            return info
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise
    
    async def get_klines(
        self, 
        symbol: str, 
        interval: str, 
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[KlineData]:
        """Get kline/candlestick data."""
        try:
            klines = await self._client.futures_klines(
                symbol=symbol.upper(),
                interval=interval,
                limit=min(limit, 1000),
                startTime=start_time,
                endTime=end_time
            )
            
            result = []
            for item in klines:
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
                result.append(kline)
            
            return result
            
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Failed to get klines for {symbol} {interval}: {e}")
            raise
    
    async def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_str: str,
        end_str: Optional[str] = None,
        limit: int = 1000
    ) -> List[KlineData]:
        """Get historical kline data using Binance Vision API equivalent."""
        try:
            klines = await self._client.get_historical_klines(
                symbol=symbol.upper(),
                interval=interval,
                start_str=start_str,
                end_str=end_str,
                limit=limit
            )
            
            result = []
            for item in klines:
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
                result.append(kline)
            
            return result
            
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Failed to get historical klines for {symbol} {interval}: {e}")
            raise
    
    async def get_symbol_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a symbol."""
        try:
            ticker = await self._client.futures_symbol_ticker(symbol=symbol.upper())
            return ticker
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    async def get_all_prices(self) -> List[Dict[str, Any]]:
        """Get all symbol prices."""
        try:
            tickers = await self._client.futures_ticker()
            return tickers
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Failed to get all prices: {e}")
            raise
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book for a symbol."""
        try:
            depth = await self._client.futures_order_book(
                symbol=symbol.upper(),
                limit=limit
            )
            return depth
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            raise
    
    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get recent trades for a symbol."""
        try:
            trades = await self._client.futures_recent_trades(
                symbol=symbol.upper(),
                limit=limit
            )
            return trades
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Failed to get recent trades for {symbol}: {e}")
            raise
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information (requires API key)."""
        if not self.config.api_key or not self.config.api_secret:
            raise ValueError("API key and secret required for account info")
        
        try:
            account = await self._client.futures_account()
            return account
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    async def get_position_info(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get position information (requires API key)."""
        if not self.config.api_key or not self.config.api_secret:
            raise ValueError("API key and secret required for position info")
        
        try:
            positions = await self._client.futures_position_information(symbol=symbol)
            return positions
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Failed to get position info: {e}")
            raise
    
    async def ping(self) -> bool:
        """Test connectivity to Binance API."""
        try:
            await self._client.futures_ping()
            return True
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False
    
    async def get_server_time(self) -> Dict[str, Any]:
        """Get server time."""
        try:
            time_info = await self._client.futures_time()
            return time_info
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Failed to get server time: {e}")
            raise
