"""Mock Parquet storage for view-only mode."""

import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MockParquetStorage:
    """Mock Parquet storage for view-only mode."""
    
    def __init__(self):
        self.cache = {}
        logger.info("Initialized mock Parquet storage for view-only mode")
    
    def save_candles(self, candles: List) -> bool:
        """Mock save operation - always succeeds in view-only mode."""
        if not candles:
            return True
            
        # Cache the candles in memory
        symbol = candles[0].symbol
        timeframe = candles[0].timeframe
        cache_key = f"{symbol}_{timeframe}"
        
        self.cache[cache_key] = candles
        logger.debug(f"Mock saved {len(candles)} candles for {symbol} {timeframe}")
        return True
    
    def load_candles(self, symbol: str, timeframe: str, limit: Optional[int] = None) -> List:
        """Mock load operation - returns cached data or empty list."""
        cache_key = f"{symbol}_{timeframe}"
        
        if cache_key in self.cache:
            candles = self.cache[cache_key]
            if limit:
                candles = candles[-limit:]
            logger.debug(f"Mock loaded {len(candles)} candles for {symbol} {timeframe}")
            return candles
        
        logger.debug(f"No cached candles found for {symbol} {timeframe}")
        return []
    
    def save_signals(self, signals: List) -> bool:
        """Mock save operation for signals."""
        if not signals:
            return True
            
        symbol = signals[0].get('symbol', 'unknown')
        timeframe = signals[0].get('timeframe', 'unknown')
        cache_key = f"signals_{symbol}_{timeframe}"
        
        self.cache[cache_key] = signals
        logger.debug(f"Mock saved {len(signals)} signals for {symbol} {timeframe}")
        return True
    
    def load_signals(self, symbol: str, timeframe: str, limit: Optional[int] = None) -> List:
        """Mock load operation for signals."""
        cache_key = f"signals_{symbol}_{timeframe}"
        
        if cache_key in self.cache:
            signals = self.cache[cache_key]
            if limit:
                signals = signals[-limit:]
            logger.debug(f"Mock loaded {len(signals)} signals for {symbol} {timeframe}")
            return signals
        
        logger.debug(f"No cached signals found for {symbol} {timeframe}")
        return []
    
    def save_backtest_result(self, result: dict) -> bool:
        """Mock save operation for backtest results."""
        result_id = result.get('id', 'unknown')
        self.cache[f"backtest_{result_id}"] = result
        logger.debug(f"Mock saved backtest result {result_id}")
        return True
    
    def load_backtest_result(self, result_id: str) -> Optional[dict]:
        """Mock load operation for backtest results."""
        cache_key = f"backtest_{result_id}"
        
        if cache_key in self.cache:
            logger.debug(f"Mock loaded backtest result {result_id}")
            return self.cache[cache_key]
        
        logger.debug(f"No cached backtest result found for {result_id}")
        return None


# Use mock implementation for view-only mode
ParquetStorage = MockParquetStorage
