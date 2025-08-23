"""Dependency injection for FastAPI."""

import os
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from .schemas import Settings

# Security scheme for API authentication (if needed in future)
security = HTTPBearer(auto_error=False)


def get_settings() -> Settings:
    """Get application settings from environment variables."""
    return Settings(
        trading_enabled=os.getenv("TRADING_ENABLED", "false").lower() == "true",
        order_confirmation_required=os.getenv("ORDER_CONFIRMATION_REQUIRED", "true").lower() == "true",
        max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", "5")),
        max_risk_per_trade=float(os.getenv("MAX_RISK_PER_TRADE", "2.0")),
        min_risk_reward_ratio=float(os.getenv("MIN_RISK_REWARD_RATIO", "3.0")),
        telegram_enabled=os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
        debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
    )


def get_trading_enabled(settings: Settings = Depends(get_settings)) -> bool:
    """Check if trading is enabled."""
    return settings.trading_enabled


def require_trading_enabled(
    trading_enabled: bool = Depends(get_trading_enabled)
) -> bool:
    """Require trading to be enabled for certain endpoints."""
    if not trading_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trading is not enabled. Please configure API keys in environment variables."
        )
    return trading_enabled


def get_api_keys() -> tuple[Optional[str], Optional[str]]:
    """Get API keys from environment variables."""
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    return api_key, api_secret


def require_api_keys(
    api_keys: tuple[Optional[str], Optional[str]] = Depends(get_api_keys)
) -> tuple[str, str]:
    """Require API keys to be configured."""
    api_key, api_secret = api_keys
    if not api_key or not api_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys not configured. Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables."
        )
    return api_key, api_secret


def get_telegram_config() -> tuple[Optional[str], Optional[str]]:
    """Get Telegram configuration from environment variables."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    return bot_token, chat_id


def require_telegram_config(
    telegram_config: tuple[Optional[str], Optional[str]] = Depends(get_telegram_config),
    settings: Settings = Depends(get_settings)
) -> tuple[str, str]:
    """Require Telegram configuration to be set up."""
    if not settings.telegram_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram notifications are not enabled."
        )
    
    bot_token, chat_id = telegram_config
    if not bot_token or not chat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram configuration incomplete. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
        )
    return bot_token, chat_id
