"""Main FastAPI application for the SMC Signal Service."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

from app.config import settings
from app.api import router as api_router
from app.web import router as web_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting SMC Signal Service...")
    
    # Startup tasks
    logger.info("Service started successfully")
    
    yield
    
    # Shutdown tasks
    logger.info("Shutting down SMC Signal Service...")


# Create FastAPI app
app = FastAPI(
    title="SMC Signal Service",
    description="Smart Money Concepts (SMC) Signal Service with local storage",
    version="0.1.0",
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

# Mount static files
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(web_router, prefix="/web")


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SMC Signal Service",
        "version": "0.1.0",
        "environment": settings.environment
    }


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "service": "SMC Signal Service",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development"
    )
