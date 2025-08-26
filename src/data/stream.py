"""
WebSocket stream manager with auto-reconnect, resync, and deduplication.
"""
import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

import websockets
from pydantic import BaseModel

from .binance_client import BinanceClient, BinanceConfig


class StreamStatus(Enum):
    """WebSocket stream status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class StreamConfig:
    """Configuration for WebSocket streams."""
    max_reconnect_attempts: int = 10
    base_reconnect_delay: float = 1.0
    max_reconnect_delay: float = 300.0
    jitter_factor: float = 0.1
    heartbeat_interval: float = 30.0
    resync_threshold: int = 1000  # Sequence gap threshold for resync


class StreamEvent(BaseModel):
    """Base stream event model."""
    stream: str
    data: Dict[str, Any]
    timestamp: int
    sequence: Optional[int] = None


class KlineEvent(StreamEvent):
    """Kline/candlestick stream event."""
    symbol: str
    interval: str
    open_time: int
    close_time: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float
    trades: int


class TradeEvent(StreamEvent):
    """Trade stream event."""
    symbol: str
    trade_id: int
    price: float
    quantity: float
    quote_quantity: float
    trade_time: int
    is_buyer_maker: bool


class BookTickerEvent(StreamEvent):
    """Book ticker stream event."""
    symbol: str
    bid_price: float
    bid_quantity: float
    ask_price: float
    ask_quantity: float
    timestamp: int


class WebSocketStreamManager:
    """Manages WebSocket streams with auto-reconnect and resync capabilities."""
    
    def __init__(self, config: StreamConfig, binance_client: BinanceClient):
        self.config = config
        self.binance_client = binance_client
        self.status = StreamStatus.DISCONNECTED
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.reconnect_attempts = 0
        self.last_heartbeat = 0
        self.sequence_numbers: Dict[str, int] = {}
        self.processed_events: Set[str] = set()
        self.event_handlers: Dict[str, List[Callable]] = {}
        self._reconnect_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()
        
        # Logging
        self.logger = logging.getLogger(__name__)
    
    async def start(self) -> None:
        """Start the WebSocket stream manager."""
        self._running = True
        await self._connect()
        
        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self) -> None:
        """Stop the WebSocket stream manager."""
        self._running = False
        
        # Cancel background tasks
        if self._reconnect_task:
            self._reconnect_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        
        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
        
        self.status = StreamStatus.DISCONNECTED
    
    async def _connect(self) -> None:
        """Establish WebSocket connection."""
        async with self._lock:
            if self.status in [StreamStatus.CONNECTING, StreamStatus.CONNECTED]:
                return
            
            self.status = StreamStatus.CONNECTING
            
            try:
                # Get exchange info to validate symbols
                exchange_info = await self.binance_client.get_exchange_info()
                
                # Subscribe to streams
                streams = []
                for symbol_info in exchange_info.get('symbols', []):
                    if symbol_info['status'] == 'TRADING':
                        symbol = symbol_info['symbol']
                        # Subscribe to kline, trade, and book ticker streams
                        streams.extend([
                            await self.binance_client.subscribe_kline_stream(symbol, '1m'),
                            await self.binance_client.subscribe_trade_stream(symbol),
                            await self.binance_client.subscribe_book_ticker_stream(symbol)
                        ])
                
                # Connect to WebSocket
                self.websocket = await self.binance_client.connect_websocket(streams)
                self.status = StreamStatus.CONNECTED
                self.reconnect_attempts = 0
                self.last_heartbeat = time.time()
                
                self.logger.info(f"WebSocket connected to {len(streams)} streams")
                
                # Start message processing
                asyncio.create_task(self._process_messages())
                
            except Exception as e:
                self.logger.error(f"Failed to connect WebSocket: {e}")
                self.status = StreamStatus.ERROR
                await self._schedule_reconnect()
    
    async def _process_messages(self) -> None:
        """Process incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                if not self._running:
                    break
                
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Invalid JSON message: {e}")
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
            await self._handle_disconnection()
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
            await self._handle_disconnection()
    
    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """Handle individual WebSocket message."""
        stream = data.get('stream', '')
        event_data = data.get('data', {})
        
        # Check for sequence number (if available)
        sequence = event_data.get('E')  # Event time
        if sequence and stream in self.sequence_numbers:
            # Check for sequence gaps
            expected_sequence = self.sequence_numbers[stream] + 1
            if sequence > expected_sequence + self.config.resync_threshold:
                self.logger.warning(f"Large sequence gap detected for {stream}: {expected_sequence} -> {sequence}")
                await self._resync_stream(stream)
                return
        
        # Update sequence number
        if sequence:
            self.sequence_numbers[stream] = sequence
        
        # Create event object
        event = await self._create_event(stream, event_data)
        if not event:
            return
        
        # Check for duplicates
        event_id = f"{stream}_{sequence}_{event_data.get('t', '')}"
        if event_id in self.processed_events:
            return
        
        self.processed_events.add(event_id)
        
        # Clean up old processed events (keep last 10000)
        if len(self.processed_events) > 10000:
            self.processed_events.clear()
        
        # Emit event to handlers
        await self._emit_event(stream, event)
    
    async def _create_event(self, stream: str, data: Dict[str, Any]) -> Optional[StreamEvent]:
        """Create appropriate event object from stream data."""
        try:
            if 'kline' in stream:
                kline = data['k']
                return KlineEvent(
                    stream=stream,
                    data=data,
                    timestamp=data.get('E', int(time.time() * 1000)),
                    sequence=data.get('E'),
                    symbol=kline['s'],
                    interval=kline['i'],
                    open_time=kline['t'],
                    close_time=kline['T'],
                    open_price=float(kline['o']),
                    high_price=float(kline['h']),
                    low_price=float(kline['l']),
                    close_price=float(kline['c']),
                    volume=float(kline['v']),
                    quote_volume=float(kline['q']),
                    trades=int(kline['n'])
                )
            elif 'trade' in stream:
                return TradeEvent(
                    stream=stream,
                    data=data,
                    timestamp=data.get('E', int(time.time() * 1000)),
                    sequence=data.get('E'),
                    symbol=data['s'],
                    trade_id=data['t'],
                    price=float(data['p']),
                    quantity=float(data['q']),
                    quote_quantity=float(data['Q']),
                    trade_time=data['T'],
                    is_buyer_maker=data['m']
                )
            elif 'bookTicker' in stream:
                return BookTickerEvent(
                    stream=stream,
                    data=data,
                    timestamp=data.get('E', int(time.time() * 1000)),
                    sequence=data.get('E'),
                    symbol=data['s'],
                    bid_price=float(data['b']),
                    bid_quantity=float(data['B']),
                    ask_price=float(data['a']),
                    ask_quantity=float(data['A'])
                )
            
            return None
            
        except (KeyError, ValueError, TypeError) as e:
            self.logger.warning(f"Failed to create event for {stream}: {e}")
            return None
    
    async def _emit_event(self, stream: str, event: StreamEvent) -> None:
        """Emit event to registered handlers."""
        handlers = self.event_handlers.get(stream, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"Error in event handler: {e}")
    
    async def _handle_disconnection(self) -> None:
        """Handle WebSocket disconnection."""
        async with self._lock:
            if self.status != StreamStatus.DISNECTED:
                self.status = StreamStatus.DISCONNECTED
                await self._schedule_reconnect()
    
    async def _schedule_reconnect(self) -> None:
        """Schedule reconnection attempt."""
        if self._reconnect_task and not self._reconnect_task.done():
            return
        
        self._reconnect_task = asyncio.create_task(self._reconnect())
    
    async def _reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        if not self._running:
            return
        
        self.status = StreamStatus.RECONNECTING
        
        while self._running and self.reconnect_attempts < self.config.max_reconnect_attempts:
            self.reconnect_attempts += 1
            
            # Calculate delay with exponential backoff and jitter
            delay = min(
                self.config.base_reconnect_delay * (2 ** (self.reconnect_attempts - 1)),
                self.config.max_reconnect_delay
            )
            
            # Add jitter
            jitter = delay * self.config.jitter_factor * (2 * time.time() % 1 - 1)
            delay = max(0.1, delay + jitter)
            
            self.logger.info(f"Reconnecting in {delay:.2f} seconds (attempt {self.reconnect_attempts})")
            await asyncio.sleep(delay)
            
            try:
                await self._connect()
                if self.status == StreamStatus.CONNECTED:
                    return
            except Exception as e:
                self.logger.error(f"Reconnection attempt {self.reconnect_attempts} failed: {e}")
        
        if self._running:
            self.logger.error("Max reconnection attempts reached")
            self.status = StreamStatus.ERROR
    
    async def _resync_stream(self, stream: str) -> None:
        """Resync stream data via REST API."""
        try:
            self.logger.info(f"Resyncing stream {stream}")
            
            # Extract symbol and interval from stream name
            if 'kline' in stream:
                # Parse kline stream: btcusdt@kline_1m
                parts = stream.split('@')
                if len(parts) == 2:
                    symbol = parts[0].upper()
                    interval = parts[1].split('_')[1]
                    
                    # Get recent klines via REST
                    klines = await self.binance_client.get_klines(symbol, interval, limit=100)
                    
                    # Update sequence number
                    if klines:
                        self.sequence_numbers[stream] = klines[-1].close_time
                        
                        self.logger.info(f"Resynced {stream} with {len(klines)} klines")
            
        except Exception as e:
            self.logger.error(f"Failed to resync stream {stream}: {e}")
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat to keep connection alive."""
        while self._running:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                
                if (self.websocket and 
                    self.status == StreamStatus.CONNECTED and 
                    time.time() - self.last_heartbeat > self.config.heartbeat_interval):
                    
                    # Send ping
                    try:
                        pong_waiter = await self.websocket.ping()
                        await asyncio.wait_for(pong_waiter, timeout=10)
                        self.last_heartbeat = time.time()
                    except Exception as e:
                        self.logger.warning(f"Heartbeat failed: {e}")
                        await self._handle_disconnection()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
    
    def add_handler(self, stream: str, handler: Callable) -> None:
        """Add event handler for a specific stream."""
        if stream not in self.event_handlers:
            self.event_handlers[stream] = []
        self.event_handlers[stream].append(handler)
    
    def remove_handler(self, stream: str, handler: Callable) -> None:
        """Remove event handler for a specific stream."""
        if stream in self.event_handlers:
            try:
                self.event_handlers[stream].remove(handler)
            except ValueError:
                pass
    
    def get_status(self) -> StreamStatus:
        """Get current stream status."""
        return self.status
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stream statistics."""
        return {
            'status': self.status.value,
            'reconnect_attempts': self.reconnect_attempts,
            'active_streams': len(self.event_handlers),
            'sequence_numbers': len(self.sequence_numbers),
            'processed_events': len(self.processed_events)
        }
