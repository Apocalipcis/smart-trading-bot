"""Trading configuration management."""

import os
from typing import Optional
from pydantic import BaseModel, Field

from ..simulation.config import SimulationConfig


class TradingConfig(BaseModel):
    """Trading configuration with mode management."""
    
    # Mode settings
    trading_mode: str = Field(default="simulation", description="Trading mode: simulation or live")
    trading_approved: bool = Field(default=False, description="Whether live trading is approved")
    
    # API credentials
    binance_api_key: Optional[str] = Field(None, description="Binance API key")
    binance_api_secret: Optional[str] = Field(None, description="Binance API secret")
    
    # Simulation configuration
    simulation_config: SimulationConfig = Field(default_factory=SimulationConfig)
    
    @classmethod
    def from_env(cls) -> "TradingConfig":
        """Create configuration from environment variables."""
        # Get simulation config
        sim_config = SimulationConfig.from_env()
        
        # Get trading mode and approval
        trading_mode = os.getenv("TRADING_MODE", "simulation")
        trading_approved = os.getenv("TRADING_APPROVED", "false").lower() == "true"
        
        # Get API credentials
        binance_api_key = os.getenv("BINANCE_API_KEY")
        binance_api_secret = os.getenv("BINANCE_API_SECRET")
        
        return cls(
            trading_mode=trading_mode,
            trading_approved=trading_approved,
            binance_api_key=binance_api_key,
            binance_api_secret=binance_api_secret,
            simulation_config=sim_config
        )
    
    def is_simulation_mode(self) -> bool:
        """Check if running in simulation mode."""
        return self.trading_mode == "simulation" or not self.trading_approved
    
    def is_live_mode(self) -> bool:
        """Check if running in live mode."""
        return self.trading_mode == "live" and self.trading_approved
    
    def can_trade_live(self) -> bool:
        """Check if live trading is allowed."""
        return self.is_live_mode() and self.has_api_credentials()
    
    def has_api_credentials(self) -> bool:
        """Check if API credentials are configured."""
        return bool(self.binance_api_key and self.binance_api_secret)
    
    def get_effective_mode(self) -> str:
        """Get the effective trading mode (simulation or live)."""
        if self.is_live_mode():
            return "live"
        else:
            return "simulation"
    
    def approve_live_trading(self) -> None:
        """Approve live trading."""
        self.trading_approved = True
    
    def revoke_live_trading(self) -> None:
        """Revoke live trading approval."""
        self.trading_approved = False
    
    def set_trading_mode(self, mode: str) -> None:
        """Set the trading mode."""
        if mode not in ["simulation", "live"]:
            raise ValueError("Trading mode must be 'simulation' or 'live'")
        self.trading_mode = mode
