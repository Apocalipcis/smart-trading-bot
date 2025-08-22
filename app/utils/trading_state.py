"""Trading state management for the SMC Signal Service."""

import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class TradingState:
    """Global trading state manager."""
    
    _instance: Optional['TradingState'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._check_trading_status()
    
    def _check_trading_status(self):
        """Check and log trading status on initialization."""
        if self.trading_enabled:
            logger.info("Trading mode: ENABLED - API keys configured and execution enabled")
        elif self.has_api_keys:
            logger.warning("Trading mode: DISABLED - API keys present but execution disabled")
        else:
            logger.warning("Trading mode: VIEW-ONLY - No API keys configured")
        
        if not self.security_configured:
            logger.warning("Security: No shared secret configured - running in basic mode")
    
    @property
    def trading_enabled(self) -> bool:
        """Check if trading is fully enabled."""
        return settings.trading_enabled
    
    @property
    def has_api_keys(self) -> bool:
        """Check if API keys are configured."""
        return settings.has_api_keys
    
    @property
    def security_configured(self) -> bool:
        """Check if security is properly configured."""
        return settings.security_configured
    
    @property
    def execution_enabled(self) -> bool:
        """Check if trading execution is enabled."""
        return settings.execution_enabled
    
    @property
    def mode(self) -> str:
        """Get current trading mode as string."""
        if self.trading_enabled:
            return "Trading Mode"
        elif self.has_api_keys:
            return "Trading Disabled"
        else:
            return "View-Only Mode"
    
    def can_trade(self) -> bool:
        """Check if trading operations are allowed."""
        return self.trading_enabled
    
    def can_place_orders(self) -> bool:
        """Check if order placement is allowed."""
        return self.trading_enabled
    
    def can_manage_positions(self) -> bool:
        """Check if position management is allowed."""
        return self.trading_enabled
    
    def log_trade_attempt(self, operation: str, details: str = ""):
        """Log a blocked trading operation attempt."""
        if not self.trading_enabled:
            logger.warning(
                f"Trade attempt blocked ({operation}): {details} - "
                f"Trading disabled (no API keys or execution disabled)"
            )
    
    def get_status_info(self) -> dict:
        """Get comprehensive trading status information."""
        return {
            "trading_enabled": self.trading_enabled,
            "has_api_keys": self.has_api_keys,
            "security_configured": self.security_configured,
            "mode": self.mode,
            "execution_enabled": settings.execution_enabled,
            "api_keys_configured": bool(settings.binance_api_key and settings.binance_secret_key),
            "message": self._get_status_message(),
            "setup_required": self._get_setup_requirements()
        }
    
    def _get_status_message(self) -> str:
        """Get user-friendly status message."""
        if self.trading_enabled:
            return "Trading is fully enabled and operational"
        elif self.has_api_keys:
            return "API keys are configured but trading execution is disabled"
        else:
            return "Trading is unavailable. Add API keys in settings to enable trading mode."
    
    def _get_setup_requirements(self) -> list:
        """Get list of setup requirements for full functionality."""
        requirements = []
        
        if not self.has_api_keys:
            requirements.append("Configure Binance API keys")
        
        if not self.execution_enabled:
            requirements.append("Enable trading execution")
        
        if not self.security_configured:
            requirements.append("Configure shared secret for enhanced security")
        
        return requirements


# Global trading state instance
trading_state = TradingState()
