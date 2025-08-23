"""Settings router for application settings management."""

from fastapi import APIRouter, Depends

from ..dependencies import get_settings
from ..schemas import APIResponse, Settings

router = APIRouter(prefix="/settings", tags=["settings"])

# In-memory storage for settings (will be replaced with database)
_current_settings: Settings = Settings()


@router.get("/", response_model=Settings)
async def get_current_settings(
    settings: Settings = Depends(get_settings)
) -> Settings:
    """Get current application settings."""
    return _current_settings


@router.put("/", response_model=Settings)
async def update_settings(settings_update: Settings) -> Settings:
    """Update application settings."""
    global _current_settings
    
    # Update settings
    _current_settings = settings_update
    
    # TODO: This would save settings to the database
    # For now, just update the in-memory settings
    
    return _current_settings


@router.patch("/", response_model=Settings)
async def patch_settings(settings_update: dict) -> Settings:
    """Partially update application settings."""
    global _current_settings
    
    # Update only provided fields
    current_dict = _current_settings.dict()
    current_dict.update(settings_update)
    
    # Create new settings object
    _current_settings = Settings(**current_dict)
    
    # TODO: This would save settings to the database
    
    return _current_settings


@router.post("/reset", response_model=APIResponse)
async def reset_settings() -> APIResponse:
    """Reset settings to default values."""
    global _current_settings
    
    _current_settings = Settings()
    
    return APIResponse(
        success=True,
        message="Settings reset to default values"
    )


@router.get("/trading/status")
async def get_trading_status(
    settings: Settings = Depends(get_settings)
) -> dict:
    """Get trading status and configuration."""
    return {
        "trading_enabled": settings.trading_enabled,
        "order_confirmation_required": settings.order_confirmation_required,
        "max_open_positions": settings.max_open_positions,
        "max_risk_per_trade": settings.max_risk_per_trade,
        "min_risk_reward_ratio": settings.min_risk_reward_ratio,
        "api_keys_configured": bool(settings.trading_enabled)  # Simplified check
    }


@router.post("/trading/toggle")
async def toggle_trading() -> APIResponse:
    """Toggle trading mode on/off."""
    global _current_settings
    
    _current_settings.trading_enabled = not _current_settings.trading_enabled
    
    status = "enabled" if _current_settings.trading_enabled else "disabled"
    
    return APIResponse(
        success=True,
        message=f"Trading mode {status}"
    )


@router.post("/order-confirmation/toggle")
async def toggle_order_confirmation() -> APIResponse:
    """Toggle order confirmation requirement."""
    global _current_settings
    
    _current_settings.order_confirmation_required = not _current_settings.order_confirmation_required
    
    status = "required" if _current_settings.order_confirmation_required else "disabled"
    
    return APIResponse(
        success=True,
        message=f"Order confirmation {status}"
    )


@router.get("/notifications/status")
async def get_notifications_status(
    settings: Settings = Depends(get_settings)
) -> dict:
    """Get notifications configuration status."""
    return {
        "telegram_enabled": settings.telegram_enabled,
        "telegram_configured": bool(settings.telegram_enabled)  # Simplified check
    }


@router.post("/notifications/telegram/toggle")
async def toggle_telegram_notifications() -> APIResponse:
    """Toggle Telegram notifications on/off."""
    global _current_settings
    
    _current_settings.telegram_enabled = not _current_settings.telegram_enabled
    
    status = "enabled" if _current_settings.telegram_enabled else "disabled"
    
    return APIResponse(
        success=True,
        message=f"Telegram notifications {status}"
    )


@router.get("/risk/limits")
async def get_risk_limits(
    settings: Settings = Depends(get_settings)
) -> dict:
    """Get current risk management limits."""
    return {
        "max_open_positions": settings.max_open_positions,
        "max_risk_per_trade": settings.max_risk_per_trade,
        "min_risk_reward_ratio": settings.min_risk_reward_ratio
    }


@router.put("/risk/limits")
async def update_risk_limits(limits: dict) -> APIResponse:
    """Update risk management limits."""
    global _current_settings
    
    if "max_open_positions" in limits:
        _current_settings.max_open_positions = limits["max_open_positions"]
    
    if "max_risk_per_trade" in limits:
        _current_settings.max_risk_per_trade = limits["max_risk_per_trade"]
    
    if "min_risk_reward_ratio" in limits:
        _current_settings.min_risk_reward_ratio = limits["min_risk_reward_ratio"]
    
    return APIResponse(
        success=True,
        message="Risk limits updated successfully"
    )


@router.get("/system/info")
async def get_system_info() -> dict:
    """Get system information and configuration."""
    import os
    import platform
    
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
        "data_directory": os.getenv("DATA_DIR", "/data"),
        "database_path": os.getenv("DB_PATH", "/data/app.db"),
        "exchange": os.getenv("EXCHANGE", "binance_futures"),
        "websocket_url": os.getenv("WS_URL", "wss://fstream.binance.com/ws"),
        "rest_url": os.getenv("REST_URL", "https://fapi.binance.com")
    }


@router.get("/export")
async def export_settings() -> dict:
    """Export current settings as JSON."""
    return _current_settings.dict()


@router.post("/import")
async def import_settings(settings_data: dict) -> APIResponse:
    """Import settings from JSON."""
    global _current_settings
    
    try:
        _current_settings = Settings(**settings_data)
        return APIResponse(
            success=True,
            message="Settings imported successfully"
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Failed to import settings: {str(e)}"
        )
