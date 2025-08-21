"""API endpoints for the SMC Signal Service."""

from fastapi import APIRouter
from .endpoints import candles, signals, backtest, volatility, pairs

# Create main API router
router = APIRouter()

# Include endpoint routers
router.include_router(candles.router, prefix="/candles", tags=["candles"])
router.include_router(signals.router, prefix="/signals", tags=["signals"])
router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
router.include_router(volatility.router, prefix="/scan", tags=["volatility"])
router.include_router(pairs.router, prefix="/pairs", tags=["pairs"])
