"""Mock Binance client for view-only mode and testing."""

import asyncio
import logging
from typing import List, Callable, Optional
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class MockCandle:
    """Mock candle data for testing."""
    
    def __init__(self, symbol: str, timeframe: str, timestamp: datetime):
        self.symbol = symbol
        self.timeframe = timeframe
        self.timestamp = timestamp
        
        # Generate mock OHLCV data
        base_price = 50000 if symbol == 'BTCUSDT' else 3000 if symbol == 'ETHUSDT' else 300
        variation = random.uniform(0.95, 1.05)
        
        self.open = base_price * variation
        self.high = self.open * random.uniform(1.0, 1.02)
        self.low = self.open * random.uniform(0.98, 1.0)
        self.close = self.open * random.uniform(0.98, 1.02)
        self.volume = random.uniform(100, 1000)


class BinanceClient:
    """Mock Binance client for view-only mode."""
    
    def __init__(self):
        self.websocket_connected = False
        self.candle_callbacks = []
        self.error_callbacks = []
        self.mock_data_task = None
        
    def add_candle_callback(self, callback: Callable):
        """Add callback for new candle data."""
        self.candle_callbacks.append(callback)
        
    def add_error_callback(self, callback: Callable):
        """Add callback for error handling."""
        self.error_callbacks.append(callback)
        
    async def connect_websocket(self, symbols: List[str], intervals: List[str]):
        """Connect to mock WebSocket for market data."""
        logger.info(f"Connecting to mock WebSocket for {symbols} on {intervals}")
        self.websocket_connected = True
        
        # Start mock data generation
        if not self.mock_data_task:
            self.mock_data_task = asyncio.create_task(self._generate_mock_data(symbols, intervals))
        
        logger.info("Mock WebSocket connected successfully")
        
    async def disconnect(self):
        """Disconnect from mock WebSocket."""
        logger.info("Disconnecting from mock WebSocket")
        self.websocket_connected = False
        
        if self.mock_data_task:
            self.mock_data_task.cancel()
            self.mock_data_task = None
            
        logger.info("Mock WebSocket disconnected")
        
    def is_websocket_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.websocket_connected
        
    async def _generate_mock_data(self, symbols: List[str], intervals: List[str]):
        """Generate mock candle data for testing."""
        try:
            while self.websocket_connected:
                for symbol in symbols:
                    for interval in intervals:
                        # Generate mock candle
                        now = datetime.utcnow()
                        candle = MockCandle(symbol, interval, now)
                        
                        # Call all registered callbacks
                        for callback in self.candle_callbacks:
                            try:
                                await callback(candle)
                            except Exception as e:
                                logger.error(f"Error in candle callback: {e}")
                                
                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds
                
        except asyncio.CancelledError:
            logger.info("Mock data generation cancelled")
        except Exception as e:
            logger.error(f"Error generating mock data: {e}")
            # Notify error callbacks
            for callback in self.error_callbacks:
                try:
                    await callback(f"Mock data error: {e}")
                except Exception as callback_error:
                    logger.error(f"Error in error callback: {callback_error}")
                    
    async def get_account_info(self):
        """Get mock account information."""
        if not self.websocket_connected:
            raise Exception("Not connected to Binance")
            
        return {
            "makerCommission": 15,
            "takerCommission": 15,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": False,  # Always false in view-only mode
            "canWithdraw": False,
            "canDeposit": False,
            "updateTime": 0,
            "accountType": "SPOT",
            "balances": []
        }
        
    async def place_order(self, symbol: str, side: str, order_type: str, quantity: float, **kwargs):
        """Mock order placement (always fails in view-only mode)."""
        raise Exception("Trading is disabled in view-only mode")
        
    async def cancel_order(self, symbol: str, order_id: str):
        """Mock order cancellation (always fails in view-only mode)."""
        raise Exception("Trading is disabled in view-only mode")
        
    async def get_open_orders(self, symbol: str = None):
        """Get mock open orders (always empty in view-only mode)."""
        return []
        
    async def get_positions(self):
        """Get mock positions (always empty in view-only mode)."""
        return []
