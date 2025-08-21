"""WebSocket worker for real-time data ingestion."""

import asyncio
import logging
import signal
import sys
from typing import List
from app.config import settings
from app.services.binance_client import BinanceClient
from app.storage.parquet_storage import ParquetStorage
from app.storage.cache_manager import cache

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketWorker:
    """Worker for handling real-time WebSocket data."""
    
    def __init__(self):
        """Initialize the WebSocket worker."""
        self.binance_client = BinanceClient()
        self.storage = ParquetStorage()
        self.running = False
        
        # Default symbols and timeframes
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        self.timeframes = ['1m', '5m', '15m']
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Register callbacks
        self.binance_client.add_candle_callback(self._on_new_candle)
        self.binance_client.add_error_callback(self._on_error)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def _on_new_candle(self, candle):
        """Handle new candle data from WebSocket."""
        try:
            logger.debug(f"New candle: {candle.symbol} {candle.timeframe} {candle.timestamp}")
            
            # Store in cache for immediate access
            cache_key = f"latest_candle:{candle.symbol}:{candle.timeframe}"
            cache.set(cache_key, candle, ttl=300)
            
            # Store in persistent storage
            await self._store_candle(candle)
            
        except Exception as e:
            logger.error(f"Error handling new candle: {e}")
    
    async def _on_error(self, error_msg: str):
        """Handle WebSocket errors."""
        logger.error(f"WebSocket error: {error_msg}")
    
    async def _store_candle(self, candle):
        """Store candle in persistent storage."""
        try:
            # Load existing candles to append
            existing_candles = self.storage.load_candles(
                symbol=candle.symbol,
                timeframe=candle.timeframe,
                limit=1000  # Load recent candles
            )
            
            # Check if we already have this candle
            if existing_candles and existing_candles[-1].timestamp >= candle.timestamp:
                logger.debug(f"Candle already exists: {candle.symbol} {candle.timeframe} {candle.timestamp}")
                return
            
            # Add new candle and save
            all_candles = existing_candles + [candle]
            success = self.storage.save_candles(all_candles)
            
            if success:
                logger.debug(f"Stored candle: {candle.symbol} {candle.timeframe} {candle.timestamp}")
            else:
                logger.error(f"Failed to store candle: {candle.symbol} {candle.timeframe}")
                
        except Exception as e:
            logger.error(f"Error storing candle: {e}")
    
    async def start(self):
        """Start the WebSocket worker."""
        try:
            logger.info("Starting WebSocket worker...")
            self.running = True
            
            # Connect to WebSocket
            await self.binance_client.connect_websocket(
                symbols=self.symbols,
                intervals=self.timeframes
            )
            
            # Keep running until shutdown signal
            while self.running:
                await asyncio.sleep(1)
                
                # Check connection status
                if not self.binance_client.is_websocket_connected():
                    logger.warning("WebSocket disconnected, attempting to reconnect...")
                    await self._reconnect()
            
        except Exception as e:
            logger.error(f"Error in WebSocket worker: {e}")
        finally:
            await self.stop()
    
    async def _reconnect(self):
        """Attempt to reconnect to WebSocket."""
        try:
            await self.binance_client.disconnect()
            await asyncio.sleep(5)  # Wait before reconnecting
            
            await self.binance_client.connect_websocket(
                symbols=self.symbols,
                intervals=self.timeframes
            )
            
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            await asyncio.sleep(10)  # Wait longer before next attempt
    
    async def stop(self):
        """Stop the WebSocket worker."""
        logger.info("Stopping WebSocket worker...")
        self.running = False
        
        try:
            await self.binance_client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
        
        logger.info("WebSocket worker stopped")


async def main():
    """Main entry point for the WebSocket worker."""
    worker = WebSocketWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await worker.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
