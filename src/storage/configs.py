"""Settings management for the trading bot."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import structlog
from pydantic import BaseModel, Field

from .db import get_db_manager

logger = structlog.get_logger(__name__)


class Setting(BaseModel):
    """Represents a setting in the database."""
    
    key: str = Field(..., description="Setting key")
    value: str = Field(..., description="Setting value as string")
    type: str = Field(..., description="Setting type (string, int, float, bool, json)")
    description: Optional[str] = Field(None, description="Setting description")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SettingValue(BaseModel):
    """Represents a setting value with proper typing."""
    
    value: Union[str, int, float, bool, Dict[str, Any]]
    type: str
    description: Optional[str] = None


class SettingsManager:
    """Manages application settings with CRUD operations."""
    
    def __init__(self):
        self._cache: Dict[str, Setting] = {}
        self._cache_loaded = False
    
    async def _load_cache(self) -> None:
        """Load settings into memory cache."""
        if self._cache_loaded:
            return
        
        db = await get_db_manager()
        results = await db.execute_query("SELECT * FROM settings")
        
        self._cache.clear()
        for row in results:
            setting = Setting(**row)
            self._cache[setting.key] = setting
        
        self._cache_loaded = True
        logger.info("Settings cache loaded", count=len(self._cache))
    
    async def get_setting(self, key: str) -> Optional[Setting]:
        """Get a setting by key."""
        await self._load_cache()
        return self._cache.get(key)
    
    async def get_setting_value(self, key: str, default: Any = None) -> Any:
        """Get a setting value with proper type conversion."""
        setting = await self.get_setting(key)
        if not setting:
            return default
        
        try:
            if setting.type == "string":
                return setting.value
            elif setting.type == "int":
                return int(setting.value)
            elif setting.type == "float":
                return float(setting.value)
            elif setting.type == "bool":
                return setting.value.lower() in ("true", "1", "yes", "on")
            elif setting.type == "json":
                return json.loads(setting.value)
            else:
                logger.warning("Unknown setting type", key=key, type=setting.type)
                return setting.value
        except (ValueError, json.JSONDecodeError) as e:
            logger.error("Failed to convert setting value", key=key, value=setting.value, type=setting.type, error=str(e))
            return default
    
    async def set_setting(self, key: str, value: Any, type_name: str = None, description: str = None) -> Setting:
        """Set a setting value."""
        # Determine type if not provided
        if type_name is None:
            if isinstance(value, bool):
                type_name = "bool"
            elif isinstance(value, int):
                type_name = "int"
            elif isinstance(value, float):
                type_name = "float"
            elif isinstance(value, dict):
                type_name = "json"
                value = json.dumps(value)
            else:
                type_name = "string"
                value = str(value)
        
        # Convert value to string for storage
        if type_name == "json" and not isinstance(value, str):
            value = json.dumps(value)
        else:
            value = str(value)
        
        db = await get_db_manager()
        
        # Check if setting exists
        existing = await self.get_setting(key)
        
        if existing:
            # Update existing setting
            await db.execute_update(
                """
                UPDATE settings 
                SET value = ?, type = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = ?
                """,
                (value, type_name, description, key)
            )
            logger.info("Setting updated", key=key, type=type_name)
        else:
            # Insert new setting
            await db.execute_insert(
                """
                INSERT INTO settings (key, value, type, description)
                VALUES (?, ?, ?, ?)
                """,
                (key, value, type_name, description)
            )
            logger.info("Setting created", key=key, type=type_name)
        
        # Update cache
        setting = Setting(
            key=key,
            value=value,
            type=type_name,
            description=description,
            updated_at=datetime.now(timezone.utc)
        )
        self._cache[key] = setting
        
        return setting
    
    async def delete_setting(self, key: str) -> bool:
        """Delete a setting."""
        db = await get_db_manager()
        
        affected_rows = await db.execute_update(
            "DELETE FROM settings WHERE key = ?",
            (key,)
        )
        
        if affected_rows > 0:
            # Remove from cache
            self._cache.pop(key, None)
            logger.info("Setting deleted", key=key)
            return True
        
        return False
    
    async def get_all_settings(self) -> List[Setting]:
        """Get all settings."""
        await self._load_cache()
        return list(self._cache.values())
    
    async def get_settings_by_prefix(self, prefix: str) -> List[Setting]:
        """Get all settings with a specific prefix."""
        await self._load_cache()
        return [setting for key, setting in self._cache.items() if key.startswith(prefix)]
    
    async def bulk_update_settings(self, settings: Dict[str, Any]) -> List[Setting]:
        """Update multiple settings at once."""
        updated_settings = []
        
        for key, value in settings.items():
            setting = await self.set_setting(key, value)
            updated_settings.append(setting)
        
        logger.info("Bulk settings update completed", count=len(updated_settings))
        return updated_settings
    
    async def reset_to_defaults(self) -> List[Setting]:
        """Reset all settings to their default values."""
        default_settings = {
            "TRADING_ENABLED": False,
            "ORDER_CONFIRMATION_REQUIRED": True,
            "MAX_OPEN_POSITIONS": 5,
            "MAX_RISK_PER_TRADE": 2.0,
            "MIN_RISK_REWARD_RATIO": 3.0,
            "DEFAULT_COMMISSION": 0.001,
            "DEFAULT_SLIPPAGE": 0.0001,
            "DEFAULT_INITIAL_CAPITAL": 10000.0,
            "DATA_STORAGE_FORMAT": "parquet",
            "DATA_RETENTION_DAYS": 365,
            "DATA_COMPRESSION": True,
            "LOG_LEVEL": "INFO",
            "DEBUG_MODE": False,
        }
        
        return await self.bulk_update_settings(default_settings)
    
    async def export_settings(self) -> Dict[str, Any]:
        """Export all settings as a dictionary."""
        await self._load_cache()
        
        exported = {}
        for key, setting in self._cache.items():
            exported[key] = await self.get_setting_value(key)
        
        return exported
    
    async def import_settings(self, settings: Dict[str, Any]) -> List[Setting]:
        """Import settings from a dictionary."""
        return await self.bulk_update_settings(settings)
    
    async def validate_settings(self) -> Dict[str, List[str]]:
        """Validate all settings and return any errors."""
        errors = {}
        
        # Validate trading settings
        trading_enabled = await self.get_setting_value("TRADING_ENABLED", False)
        max_positions = await self.get_setting_value("MAX_OPEN_POSITIONS", 5)
        max_risk = await self.get_setting_value("MAX_RISK_PER_TRADE", 2.0)
        min_rr = await self.get_setting_value("MIN_RISK_REWARD_RATIO", 3.0)
        
        if max_positions <= 0:
            errors.setdefault("MAX_OPEN_POSITIONS", []).append("Must be greater than 0")
        
        if max_risk <= 0 or max_risk > 100:
            errors.setdefault("MAX_RISK_PER_TRADE", []).append("Must be between 0 and 100")
        
        if min_rr < 1:
            errors.setdefault("MIN_RISK_REWARD_RATIO", []).append("Must be at least 1.0")
        
        # Validate data settings
        retention_days = await self.get_setting_value("DATA_RETENTION_DAYS", 365)
        if retention_days <= 0:
            errors.setdefault("DATA_RETENTION_DAYS", []).append("Must be greater than 0")
        
        # Validate commission and slippage
        commission = await self.get_setting_value("DEFAULT_COMMISSION", 0.001)
        slippage = await self.get_setting_value("DEFAULT_SLIPPAGE", 0.0001)
        
        if commission < 0 or commission > 1:
            errors.setdefault("DEFAULT_COMMISSION", []).append("Must be between 0 and 1")
        
        if slippage < 0 or slippage > 1:
            errors.setdefault("DEFAULT_SLIPPAGE", []).append("Must be between 0 and 1")
        
        return errors


# Global settings manager instance
_settings_manager: Optional[SettingsManager] = None


async def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


# Convenience functions for common settings
async def get_trading_enabled() -> bool:
    """Get trading enabled setting."""
    manager = await get_settings_manager()
    return await manager.get_setting_value("TRADING_ENABLED", False)


async def get_order_confirmation_required() -> bool:
    """Get order confirmation required setting."""
    manager = await get_settings_manager()
    return await manager.get_setting_value("ORDER_CONFIRMATION_REQUIRED", True)


async def get_max_open_positions() -> int:
    """Get maximum open positions setting."""
    manager = await get_settings_manager()
    return await manager.get_setting_value("MAX_OPEN_POSITIONS", 5)


async def get_max_risk_per_trade() -> float:
    """Get maximum risk per trade setting."""
    manager = await get_settings_manager()
    return await manager.get_setting_value("MAX_RISK_PER_TRADE", 2.0)


async def get_min_risk_reward_ratio() -> float:
    """Get minimum risk-reward ratio setting."""
    manager = await get_settings_manager()
    return await manager.get_setting_value("MIN_RISK_REWARD_RATIO", 3.0)
