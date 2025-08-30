"""Trading pair validator using Binance API."""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set

from .binance_client import BinanceClient, BinanceConfig

logger = logging.getLogger(__name__)


class PairValidator:
    """Validates trading pairs against Binance exchange."""
    
    def __init__(self, binance_config: Optional[BinanceConfig] = None):
        self.binance_config = binance_config or BinanceConfig()
        self._valid_symbols_cache: Optional[Set[str]] = None
        self._cache_expiry: Optional[float] = None
        self._cache_ttl = 3600  # 1 hour cache
        self._last_error: Optional[str] = None
        self._last_error_time: Optional[float] = None
        self._error_retry_interval = 300  # 5 minutes between retries after errors
        
        # Common trading pairs that are likely to exist on Binance Futures
        self._common_pairs = {
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT',
            'LINKUSDT', 'MATICUSDT', 'AVAXUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT',
            'BCHUSDT', 'XRPUSDT', 'DOGEUSDT', 'SHIBUSDT', 'TRXUSDT', 'ETCUSDT',
            'FILUSDT', 'NEARUSDT', 'ALGOUSDT', 'VETUSDT', 'ICPUSDT', 'FTMUSDT',
            'MANAUSDT', 'SANDUSDT', 'AXSUSDT', 'GALAUSDT', 'CHZUSDT', 'HOTUSDT'
        }
    
    async def is_valid_pair(self, symbol: str) -> bool:
        """
        Check if a trading pair symbol is valid on Binance.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            bool: True if the pair exists and is active on Binance
        """
        try:
            symbol_upper = symbol.upper()
            
            # First check common pairs for quick validation
            if symbol_upper in self._common_pairs:
                logger.debug(f"Symbol {symbol_upper} found in common pairs")
                return True
            
            # Check if we should retry after a recent error
            if self._should_skip_api_call():
                logger.warning(f"Skipping API call for {symbol_upper} due to recent errors, using fallback validation")
                return self._fallback_validation(symbol_upper)
            
            valid_symbols = await self._get_valid_symbols()
            is_valid = symbol_upper in valid_symbols
            
            if is_valid:
                logger.debug(f"Symbol {symbol_upper} validated successfully via API")
            else:
                logger.warning(f"Symbol {symbol_upper} not found in valid symbols from API")
                
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating pair {symbol}: {e}")
            self._record_error(str(e))
            return self._fallback_validation(symbol.upper())
    
    def _fallback_validation(self, symbol: str) -> bool:
        """
        Fallback validation when API is unavailable.
        
        Args:
            symbol: Trading pair symbol to validate
            
        Returns:
            bool: True if symbol looks like a valid trading pair
        """
        # Check if it's in our common pairs
        if symbol in self._common_pairs:
            return True
        
        # Basic pattern validation
        if len(symbol) < 6:
            return False
        
        # Check for common quote assets
        quote_assets = ['USDT', 'BTC', 'ETH', 'BNB', 'BUSD']
        for quote in quote_assets:
            if symbol.endswith(quote) and len(symbol) > len(quote):
                return True
        
        return False
    
    def _should_skip_api_call(self) -> bool:
        """Check if we should skip API calls due to recent errors."""
        if self._last_error_time is None:
            return False
        
        time_since_error = time.time() - self._last_error_time
        return time_since_error < self._error_retry_interval
    
    def _record_error(self, error_msg: str) -> None:
        """Record an error for rate limiting purposes."""
        self._last_error = error_msg
        self._last_error_time = time.time()
        logger.warning(f"API error recorded: {error_msg}")
    
    async def get_valid_symbols(self) -> Set[str]:
        """
        Get all valid trading pair symbols from Binance.
        
        Returns:
            Set[str]: Set of valid trading pair symbols
        """
        return await self._get_valid_symbols()
    
    async def _get_valid_symbols(self) -> Set[str]:
        """Get valid symbols with caching and error handling."""
        current_time = time.time()
        
        # Return cached symbols if still valid
        if (self._valid_symbols_cache is not None and 
            self._cache_expiry is not None and 
            current_time < self._cache_expiry):
            return self._valid_symbols_cache
        
        try:
            logger.info("Fetching valid symbols from Binance API...")
            async with BinanceClient(self.binance_config) as client:
                exchange_info = await client.get_exchange_info()
                
                # Extract active symbols
                valid_symbols = set()
                for symbol_info in exchange_info.get('symbols', []):
                    if symbol_info.get('status') == 'TRADING':
                        symbol = symbol_info.get('symbol', '').upper()
                        if symbol:
                            valid_symbols.add(symbol)
                
                # Update cache
                self._valid_symbols_cache = valid_symbols
                self._cache_expiry = current_time + self._cache_ttl
                
                logger.info(f"Successfully updated valid symbols cache: {len(valid_symbols)} symbols")
                return valid_symbols
                
        except Exception as e:
            error_msg = f"Failed to fetch valid symbols from Binance: {e}"
            logger.error(error_msg)
            self._record_error(error_msg)
            
            # Return cached symbols if available, otherwise common pairs
            if self._valid_symbols_cache:
                logger.info("Using cached symbols due to API error")
                return self._valid_symbols_cache
            else:
                logger.warning("No cached symbols available, using common pairs fallback")
                return self._common_pairs.copy()
    
    async def validate_multiple_pairs(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Validate multiple trading pair symbols.
        
        Args:
            symbols: List of trading pair symbols
            
        Returns:
            Dict[str, bool]: Dictionary mapping symbols to validation results
        """
        try:
            valid_symbols = await self._get_valid_symbols()
            results = {}
            
            for symbol in symbols:
                symbol_upper = symbol.upper()
                results[symbol] = symbol_upper in valid_symbols
            
            return results
        except Exception as e:
            logger.error(f"Error validating multiple pairs: {e}")
            # Fallback to individual validation
            results = {}
            for symbol in symbols:
                results[symbol] = await self.is_valid_pair(symbol)
            return results
    
    def clear_cache(self) -> None:
        """Clear the symbols cache."""
        self._valid_symbols_cache = None
        self._cache_expiry = None
        self._last_error = None
        self._last_error_time = None
        logger.info("Symbols cache and error state cleared")
    
    def get_last_error(self) -> Optional[str]:
        """Get the last error message."""
        return self._last_error
    
    def is_api_healthy(self) -> bool:
        """Check if the API is healthy (no recent errors)."""
        return not self._should_skip_api_call()


# Global validator instance
_pair_validator: Optional[PairValidator] = None


async def get_pair_validator() -> PairValidator:
    """Get the global pair validator instance."""
    global _pair_validator
    if _pair_validator is None:
        _pair_validator = PairValidator()
    return _pair_validator


async def clear_pair_validator_cache() -> None:
    """Clear the global pair validator cache."""
    global _pair_validator
    if _pair_validator:
        _pair_validator.clear_cache()


async def get_pair_validator_health() -> Dict[str, any]:
    """Get health status of the pair validator."""
    global _pair_validator
    if _pair_validator is None:
        return {"status": "not_initialized"}
    
    return {
        "status": "healthy" if _pair_validator.is_api_healthy() else "degraded",
        "last_error": _pair_validator.get_last_error(),
        "cache_valid": _pair_validator._valid_symbols_cache is not None,
        "cache_size": len(_pair_validator._valid_symbols_cache) if _pair_validator._valid_symbols_cache else 0
    }
