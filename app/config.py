"""Configuration management for the SMC Signal Service."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Binance API Configuration
    binance_api_key: Optional[str] = Field(None, env='BINANCE_API_KEY')
    binance_secret_key: Optional[str] = Field(None, env='BINANCE_SECRET_KEY')
    binance_testnet: bool = Field(False, env='BINANCE_TESTNET')
    
    # Service Configuration
    execution_enabled: bool = Field(False, env='EXECUTION_ENABLED')
    log_level: str = Field('INFO', env='LOG_LEVEL')
    environment: str = Field('development', env='ENVIRONMENT')
    
    # Data Configuration
    data_dir: str = Field('./data', env='DATA_DIR')
    reports_dir: str = Field('./reports', env='REPORTS_DIR')
    cache_ttl: int = Field(300, env='CACHE_TTL')
    
    # WebSocket Configuration
    ws_reconnect_delay: int = Field(5, env='WS_RECONNECT_DELAY')
    ws_max_reconnect_attempts: int = Field(10, env='WS_MAX_RECONNECT_ATTEMPTS')
    ws_heartbeat_interval: int = Field(30, env='WS_HEARTBEAT_INTERVAL')
    
    # API Configuration
    api_host: str = Field('0.0.0.0', env='API_HOST')
    api_port: int = Field(8000, env='API_PORT')
    worker_host: str = Field('0.0.0.0', env='WORKER_HOST')
    worker_port: int = Field(8001, env='WORKER_PORT')
    
    # Rate Limiting
    rate_limit_requests: int = Field(100, env='RATE_LIMIT_REQUESTS')
    rate_limit_window: int = Field(60, env='RATE_LIMIT_WINDOW')
    
    # Security (optional for view-only mode)
    shared_secret: Optional[str] = Field(None, env='SHARED_SECRET')
    
    # Indicators Configuration
    indicators: List[str] = Field(['BOS', 'CHOCH', 'FVG', 'SWEEP'], env='INDICATORS')
    
    # Timeframes
    timeframes: List[str] = Field(
        ['1m', '5m', '15m', '30m', '1h', '4h', '1d'], 
        env='TIMEFRAMES'
    )
    
    # Backtest Configuration
    backtest_max_lookback_days: int = Field(365, env='BACKTEST_MAX_LOOKBACK_DAYS')
    backtest_default_sl_percent: float = Field(2.0, env='BACKTEST_DEFAULT_SL_PERCENT')
    backtest_default_tp_percent: float = Field(4.0, env='BACKTEST_DEFAULT_TP_PERCENT')
    
    @property
    def trading_enabled(self) -> bool:
        """Check if trading is enabled based on API keys and execution setting."""
        return (
            self.binance_api_key is not None 
            and self.binance_secret_key is not None 
            and self.execution_enabled
        )
    
    @property
    def has_api_keys(self) -> bool:
        """Check if API keys are configured."""
        return (
            self.binance_api_key is not None 
            and self.binance_secret_key is not None
        )
    
    @property
    def security_configured(self) -> bool:
        """Check if security is properly configured."""
        return self.shared_secret is not None
    
    class Config:
        env_file = '.env'
        case_sensitive = False


# Global settings instance
settings = Settings()
