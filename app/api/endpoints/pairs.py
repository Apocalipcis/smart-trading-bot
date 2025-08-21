"""Pairs API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException
from app.storage.parquet_storage import ParquetStorage
from app.storage.cache_manager import cache

router = APIRouter()
storage = ParquetStorage()


@router.get("/", response_model=List[str])
async def get_available_pairs() -> List[str]:
    """Get list of available trading pairs."""
    try:
        # Check cache first
        cache_key = "available_pairs"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get from storage
        pairs = storage.get_available_symbols()
        
        # Cache the result
        cache.set(cache_key, pairs, ttl=300)  # Cache for 5 minutes
        
        return pairs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available pairs: {str(e)}")


@router.get("/{symbol}/timeframes", response_model=List[str])
async def get_pair_timeframes(symbol: str) -> List[str]:
    """Get available timeframes for a specific pair."""
    try:
        # Check cache first
        cache_key = f"timeframes:{symbol}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get from storage
        timeframes = storage.get_available_timeframes(symbol)
        
        # Cache the result
        cache.set(cache_key, timeframes, ttl=300)  # Cache for 5 minutes
        
        return timeframes
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting timeframes: {str(e)}")


@router.get("/{symbol}/info")
async def get_pair_info(symbol: str) -> dict:
    """Get information about a specific pair."""
    try:
        # Get available timeframes
        timeframes = storage.get_available_timeframes(symbol)
        
        # Get candle counts for each timeframe
        timeframe_info = {}
        for tf in timeframes:
            candles = storage.load_candles(symbol=symbol, timeframe=tf, limit=1)
            if candles:
                timeframe_info[tf] = {
                    "available": True,
                    "first_candle": candles[0].timestamp,
                    "last_candle": candles[-1].timestamp if len(candles) > 1 else candles[0].timestamp
                }
            else:
                timeframe_info[tf] = {"available": False}
        
        return {
            "symbol": symbol,
            "timeframes": timeframe_info,
            "total_timeframes": len(timeframes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting pair info: {str(e)}")
