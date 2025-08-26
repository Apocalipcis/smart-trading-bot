"""Storage package for the trading bot.

This package provides database and file management functionality for the trading bot.
"""

from .db import (
    DatabaseManager,
    close_database,
    get_db_manager,
    initialize_database,
)
from .configs import (
    Setting,
    SettingsManager,
    get_settings_manager,
    get_trading_enabled,
    get_order_confirmation_required,
    get_max_open_positions,
    get_max_risk_per_trade,
    get_min_risk_reward_ratio,
)
from .files import (
    FileManager,
    get_file_manager,
)

__all__ = [
    # Database
    "DatabaseManager",
    "initialize_database",
    "close_database",
    "get_db_manager",
    
    # Settings
    "Setting",
    "SettingsManager",
    "get_settings_manager",
    "get_trading_enabled",
    "get_order_confirmation_required",
    "get_max_open_positions",
    "get_max_risk_per_trade",
    "get_min_risk_reward_ratio",
    
    # Files
    "FileManager",
    "get_file_manager",
]
