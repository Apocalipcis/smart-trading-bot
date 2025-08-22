"""Web interface for the SMC Signal Service."""

from fastapi import APIRouter
from .endpoints import dashboard, backtest, settings

# Create main web router
router = APIRouter()

# Include web endpoint routers
router.include_router(dashboard.router, tags=["web"])
router.include_router(backtest.router, tags=["web"])
router.include_router(settings.router, prefix="/settings", tags=["web"])
