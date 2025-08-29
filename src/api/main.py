"""Main FastAPI application."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .middleware import (
    CorrelationIdMiddleware,
    StructuredLoggingMiddleware
)
from .routers import (
    backtests,
    markets,
    notifications,
    orders,
    pairs,
    settings,
    signals,
    status,
    strategies,
    simulation
)
from ..startup import create_startup_event_handler, create_shutdown_event_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting Trading Bot API...")
    
    # Initialize application components
    startup_handler = create_startup_event_handler()
    await startup_handler()
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Trading Bot API...")
    
    # Shutdown application components
    shutdown_handler = create_shutdown_event_handler()
    await shutdown_handler()


# Create FastAPI application
app = FastAPI(
    title="Trading Bot API",
    description="API for the Smart Trading Bot with Backtrader integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(StructuredLoggingMiddleware)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    import structlog
    
    logger = structlog.get_logger()
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.error(
        "Unhandled exception",
        correlation_id=correlation_id,
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url),
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "correlation_id": correlation_id
        }
    )


# Include routers
app.include_router(pairs.router, prefix="/api/v1")
app.include_router(signals.router, prefix="/api/v1")
app.include_router(backtests.router, prefix="/api/v1")
app.include_router(markets.router, prefix="/api/v1")
app.include_router(strategies.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(status.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Trading Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/api/v1")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Trading Bot API v1",
        "endpoints": {
            "pairs": "/api/v1/pairs",
            "signals": "/api/v1/signals",
            "backtests": "/api/v1/backtests",
            "markets": "/api/v1/markets",
            "strategies": "/api/v1/strategies",
            "orders": "/api/v1/orders",
            "settings": "/api/v1/settings",
            "status": "/api/v1/status",
            "notifications": "/api/v1/notifications",
            "simulation": "/api/v1/simulation"
        },
        "docs": "/docs"
    }


@app.get("/status/health")
async def health_check_redirect():
    """Redirect for Docker healthcheck compatibility."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/status/health")


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    print(f"🌐 Starting server on {host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔄 Auto-reload: {reload}")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
