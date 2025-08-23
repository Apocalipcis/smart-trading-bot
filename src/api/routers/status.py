"""Status router for health checks and system status."""

import time
from datetime import datetime, timezone

from fastapi import APIRouter

from ..schemas import HealthStatus

router = APIRouter(prefix="/status", tags=["status"])

# Application start time for uptime calculation
_start_time = time.time()


@router.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """Health check endpoint."""
    uptime = time.time() - _start_time
    
    # TODO: Add actual health checks for database and exchange connections
    # For now, return placeholder values
    
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
        uptime=uptime,
        database_connected=True,  # Placeholder
        exchange_connected=True   # Placeholder
    )


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status."""
    uptime = time.time() - _start_time
    
    # TODO: Implement actual health checks
    components = {
        "database": {
            "status": "healthy",
            "response_time": 0.001,  # Placeholder
            "last_check": datetime.now(timezone.utc).isoformat()
        },
        "exchange": {
            "status": "healthy",
            "response_time": 0.050,  # Placeholder
            "last_check": datetime.now(timezone.utc).isoformat()
        },
        "websocket": {
            "status": "connected",
            "last_message": datetime.now(timezone.utc).isoformat(),
            "reconnect_count": 0
        },
        "data_feed": {
            "status": "active",
            "last_update": datetime.now(timezone.utc).isoformat(),
            "candles_processed": 0  # Placeholder
        }
    }
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime,
        "uptime_formatted": _format_uptime(uptime),
        "components": components,
        "version": "1.0.0"
    }


@router.get("/metrics")
async def get_metrics():
    """Get system metrics."""
    uptime = time.time() - _start_time
    
    # TODO: Implement actual metrics collection
    # For now, return placeholder metrics
    
    return {
        "system": {
            "uptime_seconds": uptime,
            "uptime_formatted": _format_uptime(uptime),
            "memory_usage_mb": 128.5,  # Placeholder
            "cpu_usage_percent": 15.2,  # Placeholder
            "disk_usage_percent": 45.8  # Placeholder
        },
        "trading": {
            "total_signals": 0,  # Placeholder
            "total_orders": 0,   # Placeholder
            "active_positions": 0,  # Placeholder
            "total_pnl": 0.0     # Placeholder
        },
        "data": {
            "candles_processed": 0,  # Placeholder
            "websocket_messages": 0,  # Placeholder
            "last_data_update": datetime.now(timezone.utc).isoformat()
        },
        "performance": {
            "average_response_time_ms": 25.5,  # Placeholder
            "requests_per_second": 12.3,       # Placeholder
            "error_rate_percent": 0.1          # Placeholder
        }
    }


@router.get("/info")
async def get_system_info():
    """Get system information."""
    import os
    import platform
    
    # Get system information
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "hostname": platform.node()
    }
    
    # Get memory information (with fallback if psutil not available)
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent_used": memory.percent
        }
    except ImportError:
        memory_info = {
            "total_gb": "N/A",
            "available_gb": "N/A",
            "used_gb": "N/A",
            "percent_used": "N/A"
        }
    
    # Get disk information (with fallback if psutil not available)
    try:
        import psutil
        disk = psutil.disk_usage('/')
        disk_info = {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "percent_used": round((disk.used / disk.total) * 100, 2)
        }
    except ImportError:
        disk_info = {
            "total_gb": "N/A",
            "free_gb": "N/A",
            "used_gb": "N/A",
            "percent_used": "N/A"
        }
    
    # Get environment information
    env_info = {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
        "data_directory": os.getenv("DATA_DIR", "/data"),
        "database_path": os.getenv("DB_PATH", "/data/app.db"),
        "exchange": os.getenv("EXCHANGE", "binance_futures"),
        "websocket_url": os.getenv("WS_URL", "wss://fstream.binance.com/ws"),
        "rest_url": os.getenv("REST_URL", "https://fapi.binance.com")
    }
    
    return {
        "system": system_info,
        "memory": memory_info,
        "disk": disk_info,
        "environment": env_info,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/logs")
async def get_recent_logs(limit: int = 100):
    """Get recent application logs."""
    # TODO: Implement log retrieval
    # For now, return placeholder logs
    
    logs = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "message": "Application started",
            "correlation_id": "startup-001"
        },
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "message": "Health check endpoint accessed",
            "correlation_id": "health-001"
        }
    ]
    
    return {
        "logs": logs[:limit],
        "total": len(logs),
        "limit": limit
    }


def _format_uptime(seconds: float) -> str:
    """Format uptime in a human-readable format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
