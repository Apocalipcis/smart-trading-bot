"""Web interface for the SMC Signal Service."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from .endpoints import dashboard, backtest, settings

# Create main web router
router = APIRouter()

# Root redirect to dashboard
@router.get("/")
async def root_redirect():
    """Redirect root web path to dashboard."""
    return RedirectResponse(url="/web/dashboard", status_code=302)

# Include web endpoint routers
router.include_router(dashboard.router, prefix="/dashboard", tags=["web"])
router.include_router(backtest.router, prefix="/backtest", tags=["web"])
router.include_router(settings.router, prefix="/settings", tags=["web"])
