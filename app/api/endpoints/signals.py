"""Signals API endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from app.models.signal import Signal
from app.storage.parquet_storage import ParquetStorage
from app.storage.cache_manager import cache

router = APIRouter()
storage = ParquetStorage()


@router.get("/", response_model=List[Signal])
async def get_signals(
    symbol: Optional[str] = Query(None, description="Trading pair symbol"),
    timeframe: Optional[str] = Query(None, description="Timeframe"),
    signal_kind: Optional[str] = Query(None, description="Signal type"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering")
) -> List[Signal]:
    """Get signals with optional filtering."""
    try:
        # Check cache first
        cache_key = f"signals:{symbol}:{timeframe}:{signal_kind}:{start_date}:{end_date}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Load from storage
        signals = storage.load_signals(
            symbol=symbol or "",
            timeframe=timeframe or "",
            start_date=start_date,
            end_date=end_date,
            signal_kind=signal_kind
        )
        
        # Cache the result
        cache.set(cache_key, signals, ttl=300)  # Cache for 5 minutes
        
        return signals
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading signals: {str(e)}")


@router.get("/latest", response_model=List[Signal])
async def get_latest_signals(
    limit: int = Query(10, description="Number of latest signals to return")
) -> List[Signal]:
    """Get the latest signals across all symbols and timeframes."""
    try:
        # Check cache first
        cache_key = f"latest_signals:{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get available symbols and timeframes
        symbols = storage.get_available_symbols()
        all_signals = []
        
        # Load recent signals from each symbol/timeframe combination
        for symbol in symbols[:5]:  # Limit to first 5 symbols for performance
            timeframes = storage.get_available_timeframes(symbol)
            for timeframe in timeframes[:3]:  # Limit to first 3 timeframes
                signals = storage.load_signals(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit
                )
                all_signals.extend(signals)
        
        # Sort by timestamp and take the latest
        all_signals.sort(key=lambda x: x.timestamp, reverse=True)
        latest_signals = all_signals[:limit]
        
        # Cache the result
        cache.set(cache_key, latest_signals, ttl=60)  # Cache for 1 minute
        
        return latest_signals
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading latest signals: {str(e)}")


@router.get("/{symbol}/{timeframe}", response_model=List[Signal])
async def get_signals_by_symbol_timeframe(
    symbol: str,
    timeframe: str,
    signal_kind: Optional[str] = Query(None, description="Signal type"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering")
) -> List[Signal]:
    """Get signals for a specific symbol and timeframe."""
    try:
        # Check cache first
        cache_key = f"signals:{symbol}:{timeframe}:{signal_kind}:{start_date}:{end_date}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Load from storage
        signals = storage.load_signals(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            signal_kind=signal_kind
        )
        
        # Cache the result
        cache.set(cache_key, signals, ttl=300)  # Cache for 5 minutes
        
        return signals
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading signals: {str(e)}")


@router.get("/stats/summary")
async def get_signals_summary() -> dict:
    """Get summary statistics for all signals."""
    try:
        # Check cache first
        cache_key = "signals_summary"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get available symbols
        symbols = storage.get_available_symbols()
        total_signals = 0
        signal_types = {}
        directions = {}
        
        # Aggregate statistics
        for symbol in symbols:
            timeframes = storage.get_available_timeframes(symbol)
            for timeframe in timeframes:
                signals = storage.load_signals(symbol=symbol, timeframe=timeframe)
                total_signals += len(signals)
                
                for signal in signals:
                    # Count signal types
                    signal_types[signal.kind.value] = signal_types.get(signal.kind.value, 0) + 1
                    
                    # Count directions
                    directions[signal.direction.value] = directions.get(signal.direction.value, 0) + 1
        
        summary = {
            "total_signals": total_signals,
            "total_symbols": len(symbols),
            "signal_types": signal_types,
            "directions": directions,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Cache the result
        cache.set(cache_key, summary, ttl=600)  # Cache for 10 minutes
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting signals summary: {str(e)}")
