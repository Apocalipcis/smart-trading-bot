"""Signals router for signal management and streaming."""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from ..schemas import APIResponse, PaginatedResponse, Signal, SignalSide

router = APIRouter(prefix="/signals", tags=["signals"])

# In-memory storage for signals (will be replaced with database)
_signals: List[Signal] = []

# Store for active SSE connections
_active_connections: List[Request] = []


@router.get("/", response_model=PaginatedResponse)
async def get_signals(
    pair: Optional[str] = None,
    strategy: Optional[str] = None,
    side: Optional[SignalSide] = None,
    limit: int = 100,
    page: int = 1
) -> PaginatedResponse:
    """Get signals with optional filtering and pagination."""
    # Filter signals
    filtered_signals = _signals.copy()
    
    if pair:
        filtered_signals = [s for s in filtered_signals if s.pair.upper() == pair.upper()]
    
    if strategy:
        filtered_signals = [s for s in filtered_signals if s.strategy.lower() == strategy.lower()]
    
    if side:
        filtered_signals = [s for s in filtered_signals if s.side == side]
    
    # Sort by timestamp (newest first)
    filtered_signals.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Apply pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    total = len(filtered_signals)
    items = filtered_signals[start_idx:end_idx]
    pages = (total + limit - 1) // limit
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get("/{signal_id}", response_model=Signal)
async def get_signal(signal_id: str) -> Signal:
    """Get a specific signal by ID."""
    for signal in _signals:
        if str(signal.id) == signal_id:
            return signal
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Signal {signal_id} not found"
    )


@router.get("/stream/sse")
async def stream_signals_sse(request: Request):
    """Stream signals using Server-Sent Events."""
    async def event_generator():
        # Add connection to active list
        _active_connections.append(request)
        
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                # Send heartbeat every 30 seconds
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": datetime.now(timezone.utc).isoformat()})
                }
                
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            pass
        finally:
            # Remove connection from active list
            if request in _active_connections:
                _active_connections.remove(request)
    
    return EventSourceResponse(event_generator())


@router.get("/stream")
async def stream_signals(request: Request):
    """Alias endpoint for signals stream - redirects to SSE endpoint."""
    # This is an alias for the SSE endpoint to match frontend expectations
    async def event_generator():
        # Add connection to active list
        _active_connections.append(request)
        
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                # Send heartbeat every 30 seconds
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": datetime.now(timezone.utc).isoformat()})
                }
                
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            pass
        finally:
            # Remove connection from active list
            if request in _active_connections:
                _active_connections.remove(request)
    
    return EventSourceResponse(event_generator())


@router.get("/stream/websocket")
async def stream_signals_websocket():
    """Stream signals using WebSocket (placeholder for future implementation)."""
    # This will be implemented when WebSocket support is added
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="WebSocket streaming not yet implemented"
    )


@router.post("/", response_model=Signal)
async def create_signal(signal: Signal) -> Signal:
    """Create a new signal."""
    # Generate ID if not provided
    if not signal.id:
        signal.id = uuid4()
    
    # Add timestamp if not provided
    if not signal.timestamp:
        signal.timestamp = datetime.now(timezone.utc)
    
    # Add to storage
    _signals.append(signal)
    
    # Notify active SSE connections
    await _notify_sse_connections(signal)
    
    return signal


@router.delete("/{signal_id}", response_model=APIResponse)
async def delete_signal(signal_id: str) -> APIResponse:
    """Delete a signal."""
    for i, signal in enumerate(_signals):
        if str(signal.id) == signal_id:
            del _signals[i]
            return APIResponse(
                success=True,
                message=f"Signal {signal_id} deleted successfully"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Signal {signal_id} not found"
    )


@router.delete("/", response_model=APIResponse)
async def delete_all_signals() -> APIResponse:
    """Delete all signals."""
    _signals.clear()
    return APIResponse(
        success=True,
        message="All signals deleted successfully"
    )


@router.get("/stats/summary")
async def get_signal_stats():
    """Get signal statistics."""
    if not _signals:
        return {
            "total_signals": 0,
            "signals_today": 0,
            "signals_this_week": 0,
            "by_side": {"buy": 0, "sell": 0},
            "by_strategy": {},
            "by_pair": {}
        }
    
    now = datetime.now(timezone.utc)
    today = now.date()
    week_ago = now - timedelta(days=7)
    
    signals_today = [s for s in _signals if s.timestamp.date() == today]
    signals_this_week = [s for s in _signals if s.timestamp >= week_ago]
    
    by_side = {"buy": 0, "sell": 0}
    by_strategy = {}
    by_pair = {}
    
    for signal in _signals:
        # Count by side
        by_side[signal.side.value] += 1
        
        # Count by strategy
        strategy = signal.strategy
        by_strategy[strategy] = by_strategy.get(strategy, 0) + 1
        
        # Count by pair
        pair = signal.pair
        by_pair[pair] = by_pair.get(pair, 0) + 1
    
    return {
        "total_signals": len(_signals),
        "signals_today": len(signals_today),
        "signals_this_week": len(signals_this_week),
        "by_side": by_side,
        "by_strategy": by_strategy,
        "by_pair": by_pair
    }


async def _notify_sse_connections(signal: Signal):
    """Notify all active SSE connections about a new signal."""
    # This would be implemented to send the signal to all active connections
    # For now, it's a placeholder
    pass


# Helper function to add test signals (for development)
def add_test_signal(
    pair: str = "BTCUSDT",
    side: SignalSide = SignalSide.BUY,
    entry_price: float = 50000.0,
    stop_loss: float = 49000.0,
    take_profit: float = 52000.0,
    confidence: float = 0.8,
    strategy: str = "SMC",
    timeframe: str = "1h"
) -> Signal:
    """Add a test signal for development purposes."""
    signal = Signal(
        id=uuid4(),
        pair=pair,
        side=side,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        confidence=confidence,
        strategy=strategy,
        timeframe=timeframe,
        timestamp=datetime.now(timezone.utc)
    )
    
    _signals.append(signal)
    return signal
