"""Candles API endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from app.models.candle import Candle
from app.storage.parquet_storage import ParquetStorage
from app.storage.cache_manager import cache

router = APIRouter()
storage = ParquetStorage()


@router.get("/", response_model=List[Candle])
async def get_candles(
    symbol: str = Query(..., description="Trading pair symbol"),
    timeframe: str = Query(..., description="Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: Optional[int] = Query(100, description="Maximum number of candles to return")
) -> List[Candle]:
    """Get candles for a symbol and timeframe."""
    try:
        # Check cache first
        cache_key = f"candles:{symbol}:{timeframe}:{start_date}:{end_date}:{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Load from storage
        candles = storage.load_candles(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        # Cache the result
        cache.set(cache_key, candles, ttl=60)  # Cache for 1 minute
        
        return candles
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading candles: {str(e)}")


@router.get("/latest", response_model=Candle)
async def get_latest_candle(
    symbol: str = Query(..., description="Trading pair symbol"),
    timeframe: str = Query(..., description="Timeframe")
) -> Candle:
    """Get the latest candle for a symbol and timeframe."""
    try:
        candles = storage.load_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=1
        )
        
        if not candles:
            raise HTTPException(status_code=404, detail="No candles found")
        
        return candles[-1]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading latest candle: {str(e)}")


@router.get("/count")
async def get_candle_count(
    symbol: str = Query(..., description="Trading pair symbol"),
    timeframe: str = Query(..., description="Timeframe")
) -> dict:
    """Get the count of available candles for a symbol and timeframe."""
    try:
        candles = storage.load_candles(symbol=symbol, timeframe=timeframe)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(candles),
            "first_candle": candles[0].timestamp if candles else None,
            "last_candle": candles[-1].timestamp if candles else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting candle count: {str(e)}")
