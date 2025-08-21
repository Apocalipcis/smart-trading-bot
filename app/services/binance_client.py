"""Binance client for REST API and WebSocket data."""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable
import httpx
import websockets
from binance.client import Client
from binance.exceptions import BinanceAPIException
from app.config import settings
from app.models.candle import Candle


class BinanceClient:
    """Binance client for data retrieval and WebSocket streaming."""
    
    def __init__(self):
        """Initialize Binance client."""
        self.api_key = settings.binance_api_key
        self.secret_key = settings.binance_secret_key
        self.testnet = settings.binance_testnet
        
        # Initialize REST client
        self.client = Client(
            api_key=self.api_key,
            api_secret=self.secret_key,
            testnet=self.testnet
        )
        
        # WebSocket connection
        self.ws_connection: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = settings.ws_max_reconnect_attempts
        self.reconnect_delay = settings.ws_reconnect_delay
        
        # Callbacks
        self.candle_callbacks: List[Callable[[Candle], None]] = []
        self.error_callbacks: List[Callable[[str], None]] = []
        
        # Rate limiting
        self.request_count = 0
        self.request_window_start = time.time()
        self.max_requests_per_minute = 1200  # Binance limit
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        current_time = time.time()
        
        # Reset window if needed
        if current_time - self.request_window_start >= 60:
            self.request_count = 0
            self.request_window_start = current_time
        
        # Check if we can make a request
        if self.request_count >= self.max_requests_per_minute:
            return False
        
        self.request_count += 1
        return True
    
    def _wait_for_rate_limit(self) -> None:
        """Wait until we can make another request."""
        while not self._check_rate_limit():
            time.sleep(1)
    
    async def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Candle]:
        """Get historical kline data from Binance."""
        try:
            self._wait_for_rate_limit()
            
            # Convert timeframe to Binance format
            interval_map = {
                '1m': Client.KLINE_INTERVAL_1MINUTE,
                '5m': Client.KLINE_INTERVAL_5MINUTE,
                '15m': Client.KLINE_INTERVAL_15MINUTE,
                '30m': Client.KLINE_INTERVAL_30MINUTE,
                '1h': Client.KLINE_INTERVAL_1HOUR,
                '4h': Client.KLINE_INTERVAL_4HOUR,
                '1d': Client.KLINE_INTERVAL_1DAY,
            }
            
            binance_interval = interval_map.get(interval, interval)
            
            # Get klines
            klines = self.client.get_klines(
                symbol=symbol,
                interval=binance_interval,
                start_str=start_date.isoformat() if start_date else None,
                end_str=end_date.isoformat() if end_date else None,
                limit=limit
            )
            
            # Convert to Candle objects
            candles = []
            for kline in klines:
                candle = Candle(
                    symbol=symbol,
                    timeframe=interval,
                    timestamp=datetime.fromtimestamp(kline[0] / 1000),
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                    source='binance'
                )
                
                # Calculate additional fields
                candle.body_size = abs(candle.close - candle.open)
                candle.upper_shadow = candle.high - max(candle.open, candle.close)
                candle.lower_shadow = min(candle.open, candle.close) - candle.low
                candle.is_bullish = candle.close > candle.open
                candle.is_bearish = candle.close < candle.open
                candle.is_doji = abs(candle.close - candle.open) < (candle.high - candle.low) * 0.1
                
                candles.append(candle)
            
            return candles
            
        except BinanceAPIException as e:
            print(f"Binance API error: {e}")
            return []
        except Exception as e:
            print(f"Error getting historical klines: {e}")
            return []
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information including available symbols."""
        try:
            self._wait_for_rate_limit()
            return self.client.get_exchange_info()
        except Exception as e:
            print(f"Error getting exchange info: {e}")
            return {}
    
    async def get_ticker_24hr(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get 24hr ticker statistics."""
        try:
            self._wait_for_rate_limit()
            if symbol:
                return [self.client.get_ticker(symbol=symbol)]
            else:
                return self.client.get_ticker()
        except Exception as e:
            print(f"Error getting ticker: {e}")
            return []
    
    def add_candle_callback(self, callback: Callable[[Candle], None]) -> None:
        """Add callback for new candle data."""
        self.candle_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]) -> None:
        """Add callback for error handling."""
        self.error_callbacks.append(callback)
    
    async def connect_websocket(self, symbols: List[str], intervals: List[str]) -> None:
        """Connect to Binance WebSocket for real-time data."""
        try:
            # Create stream names
            streams = []
            for symbol in symbols:
                for interval in intervals:
                    # Convert timeframe to Binance format
                    interval_map = {
                        '1m': '1m',
                        '5m': '5m',
                        '15m': '15m',
                        '30m': '30m',
                        '1h': '1h',
                        '4h': '4h',
                        '1d': '1d',
                    }
                    binance_interval = interval_map.get(interval, interval)
                    streams.append(f"{symbol.lower()}@kline_{binance_interval}")
            
            # Connect to WebSocket
            stream_url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}"
            
            self.ws_connection = await websockets.connect(stream_url)
            self.is_connected = True
            self.reconnect_attempts = 0
            
            print(f"Connected to Binance WebSocket for {len(streams)} streams")
            
            # Start listening
            await self._listen_websocket()
            
        except Exception as e:
            print(f"Error connecting to WebSocket: {e}")
            await self._handle_connection_error()
    
    async def _listen_websocket(self) -> None:
        """Listen for WebSocket messages."""
        try:
            async for message in self.ws_connection:
                await self._process_websocket_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
            await self._handle_connection_error()
        except Exception as e:
            print(f"Error in WebSocket listener: {e}")
            await self._handle_connection_error()
    
    async def _process_websocket_message(self, message: str) -> None:
        """Process incoming WebSocket message."""
        try:
            data = json.loads(message)
            
            if 'data' in data and 'k' in data['data']:
                kline_data = data['data']['k']
                
                # Create Candle object
                candle = Candle(
                    symbol=data['data']['s'],
                    timeframe=kline_data['i'],
                    timestamp=datetime.fromtimestamp(kline_data['t'] / 1000),
                    open=float(kline_data['o']),
                    high=float(kline_data['h']),
                    low=float(kline_data['l']),
                    close=float(kline_data['c']),
                    volume=float(kline_data['v']),
                    source='binance'
                )
                
                # Calculate additional fields
                candle.body_size = abs(candle.close - candle.open)
                candle.upper_shadow = candle.high - max(candle.open, candle.close)
                candle.lower_shadow = min(candle.open, candle.close) - candle.low
                candle.is_bullish = candle.close > candle.open
                candle.is_bearish = candle.close < candle.open
                candle.is_doji = abs(candle.close - candle.open) < (candle.high - candle.low) * 0.1
                
                # Notify callbacks
                for callback in self.candle_callbacks:
                    try:
                        callback(candle)
                    except Exception as e:
                        print(f"Error in candle callback: {e}")
        
        except json.JSONDecodeError as e:
            print(f"Error decoding WebSocket message: {e}")
        except Exception as e:
            print(f"Error processing WebSocket message: {e}")
    
    async def _handle_connection_error(self) -> None:
        """Handle WebSocket connection errors."""
        self.is_connected = False
        
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            print(f"Attempting to reconnect ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            
            await asyncio.sleep(self.reconnect_delay)
            # Reconnection logic would go here
        else:
            print("Max reconnection attempts reached")
            for callback in self.error_callbacks:
                try:
                    callback("Max reconnection attempts reached")
                except Exception as e:
                    print(f"Error in error callback: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        if self.ws_connection:
            await self.ws_connection.close()
            self.is_connected = False
            print("Disconnected from Binance WebSocket")
    
    def is_websocket_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.is_connected
