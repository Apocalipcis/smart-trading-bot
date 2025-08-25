"""
Startup script for the trading bot application.
Handles initialization of all components including logging, database, and configuration.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

from .logging_config import setup_logging, get_logger
from .storage.db import initialize_database, close_database
from .storage.configs import SettingsManager


class TradingBotApp:
    """Main application class for the trading bot."""
    
    def __init__(self):
        self.logger = None
        self.settings_manager = None
        self.db_manager = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all application components."""
        if self._initialized:
            return
        
        try:
            # Setup logging first
            await self._setup_logging()
            
            # Initialize settings
            await self._setup_settings()
            
            # Initialize database
            await self._setup_database()
            
            # Create data directories
            await self._create_data_directories()
            
            self._initialized = True
            self.logger.info("Trading bot application initialized successfully")
            
        except Exception as e:
            if self.logger:
                self.logger.error("Failed to initialize trading bot", error=str(e))
            raise
    
    async def shutdown(self) -> None:
        """Shutdown all application components."""
        if not self._initialized:
            return
        
        try:
            # Close database connections
            if self.db_manager:
                await close_database()
            
            self.logger.info("Trading bot application shutdown completed")
            
        except Exception as e:
            if self.logger:
                self.logger.error("Error during shutdown", error=str(e))
        finally:
            self._initialized = False
    
    async def _setup_logging(self) -> None:
        """Setup structured logging configuration."""
        log_level = os.getenv("LOG_LEVEL", "INFO")
        debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        json_format = os.getenv("LOG_FORMAT", "json").lower() == "json"
        
        setup_logging(
            log_level=log_level,
            json_format=json_format,
            debug_mode=debug_mode
        )
        
        self.logger = get_logger(__name__)
        self.logger.info(
            "Logging initialized",
            log_level=log_level,
            json_format=json_format,
            debug_mode=debug_mode
        )
    
    async def _setup_settings(self) -> None:
        """Initialize settings manager."""
        data_dir = os.getenv("DATA_DIR", "/data")
        db_path = os.getenv("DB_PATH", "/data/app.db")
        
        self.settings_manager = SettingsManager()
        
        self.logger.info(
            "Settings manager initialized",
            data_dir=data_dir,
            db_path=db_path
        )
    
    async def _setup_database(self) -> None:
        """Initialize database connection."""
        db_path = os.getenv("DB_PATH", "/data/app.db")
        
        self.db_manager = await initialize_database(db_path)
        
        self.logger.info(
            "Database initialized",
            db_path=db_path
        )
    
    async def _create_data_directories(self) -> None:
        """Create necessary data directories."""
        data_dir = Path(os.getenv("DATA_DIR", "/data"))
        
        directories = [
            data_dir / "candles",
            data_dir / "backtests",
            data_dir / "artifacts",
            data_dir / "reports",
            data_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(
            "Data directories created",
            directories=[str(d) for d in directories]
        )


# Global application instance
_app_instance: Optional[TradingBotApp] = None


async def get_app() -> TradingBotApp:
    """Get the global application instance."""
    global _app_instance
    if _app_instance is None:
        raise RuntimeError("Application not initialized")
    return _app_instance


async def initialize_app() -> TradingBotApp:
    """Initialize the global application instance."""
    global _app_instance
    if _app_instance is None:
        _app_instance = TradingBotApp()
        await _app_instance.initialize()
    return _app_instance


async def shutdown_app() -> None:
    """Shutdown the global application instance."""
    global _app_instance
    if _app_instance:
        await _app_instance.shutdown()
        _app_instance = None


def create_startup_event_handler():
    """Create FastAPI startup event handler."""
    async def startup_event():
        await initialize_app()
    
    return startup_event


def create_shutdown_event_handler():
    """Create FastAPI shutdown event handler."""
    async def shutdown_event():
        await shutdown_app()
    
    return shutdown_event
