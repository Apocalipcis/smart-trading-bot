"""Volatility scanner API endpoint."""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from app.storage.parquet_storage import ParquetStorage
from app.storage.cache_manager import cache
import pandas as pd
import numpy as np

router = APIRouter()
storage = ParquetStorage()


@router.get("/volatility")
async def scan_volatility(
    tf: str = Query("15m", description="Timeframe for analysis"),
    window: int = Query(288, description="Number of candles to analyze"),
    top: int = Query(20, description="Number of top pairs to return")
) -> dict:
    """Scan pairs by volatility metrics."""
    try:
        # Check cache first
        cache_key = f"volatility_scan:{tf}:{window}:{top}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get available symbols
        symbols = storage.get_available_symbols()
        volatility_data = []
        
        for symbol in symbols:
            try:
                # Load candles for analysis
                candles = storage.load_candles(
                    symbol=symbol,
                    timeframe=tf,
                    limit=window
                )
                
                if len(candles) < window // 2:  # Need at least half the requested data
                    continue
                
                # Calculate volatility metrics
                metrics = _calculate_volatility_metrics(candles)
                if metrics:
                    volatility_data.append({
                        "symbol": symbol,
                        **metrics
                    })
                    
            except Exception as e:
                # Skip symbols with errors
                continue
        
        if not volatility_data:
            return {
                "timeframe": tf,
                "window": window,
                "pairs": [],
                "message": "No volatility data available"
            }
        
        # Sort by volatility score and take top pairs
        volatility_data.sort(key=lambda x: x['volatility_score'], reverse=True)
        top_pairs = volatility_data[:top]
        
        result = {
            "timeframe": tf,
            "window": window,
            "pairs": top_pairs,
            "total_analyzed": len(volatility_data),
            "last_updated": pd.Timestamp.now().isoformat()
        }
        
        # Cache the result
        cache.set(cache_key, result, ttl=300)  # Cache for 5 minutes
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scanning volatility: {str(e)}")


def _calculate_volatility_metrics(candles: List) -> Optional[dict]:
    """Calculate volatility metrics for a list of candles."""
    try:
        if len(candles) < 2:
            return None
        
        # Convert to pandas DataFrame for easier calculations
        df = pd.DataFrame([{
            'timestamp': c.timestamp,
            'open': c.open,
            'high': c.high,
            'low': c.low,
            'close': c.close,
            'volume': c.volume
        } for c in candles])
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        
        # Calculate True Range (TR)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # Calculate Average True Range (ATR)
        atr = df['tr'].mean()
        
        # Calculate volatility metrics
        returns_volatility = df['returns'].std()
        price_volatility = df['close'].std() / df['close'].mean()
        
        # Calculate volume metrics
        avg_volume = df['volume'].mean()
        volume_volatility = df['volume'].std() / df['volume'].mean()
        
        # Calculate price range metrics
        price_range = (df['high'].max() - df['low'].min()) / df['close'].mean()
        
        # Calculate composite volatility score
        volatility_score = (
            returns_volatility * 0.4 +
            price_volatility * 0.3 +
            (atr / df['close'].mean()) * 0.2 +
            volume_volatility * 0.1
        )
        
        return {
            "atr": float(atr),
            "returns_volatility": float(returns_volatility),
            "price_volatility": float(price_volatility),
            "volume_volatility": float(volume_volatility),
            "price_range": float(price_range),
            "avg_volume": float(avg_volume),
            "volatility_score": float(volatility_score),
            "candles_analyzed": len(candles)
        }
        
    except Exception as e:
        return None
