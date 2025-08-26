"""Simulation configuration management."""

import os
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class SimulationConfig(BaseModel):
    """Configuration for simulation mode."""
    
    # Mode settings
    trading_mode: str = Field(default="simulation", description="Trading mode: simulation or live")
    trading_approved: bool = Field(default=False, description="Whether live trading is approved")
    
    # Simulation settings
    initial_capital: Decimal = Field(default=Decimal("10000.0"), description="Initial capital for simulation")
    commission: Decimal = Field(default=Decimal("0.001"), description="Commission rate")
    slippage: Decimal = Field(default=Decimal("0.0001"), description="Slippage rate")
    
    # Engine settings
    tick_interval: float = Field(default=5.0, description="Engine tick interval in seconds")
    strategy_interval: float = Field(default=60.0, description="Strategy evaluation interval in seconds")
    
    # Risk settings
    max_positions: int = Field(default=5, description="Maximum concurrent positions")
    max_risk_per_trade: Decimal = Field(default=Decimal("0.02"), description="Maximum risk per trade")
    min_risk_reward_ratio: Decimal = Field(default=Decimal("3.0"), description="Minimum risk-reward ratio")
    
    @classmethod
    def from_env(cls) -> "SimulationConfig":
        """Create configuration from environment variables."""
        return cls(
            trading_mode=os.getenv("TRADING_MODE", "simulation"),
            trading_approved=os.getenv("TRADING_APPROVED", "false").lower() == "true",
            initial_capital=Decimal(os.getenv("SIMULATION_INITIAL_CAPITAL", "10000.0")),
            commission=Decimal(os.getenv("SIMULATION_COMMISSION", "0.001")),
            slippage=Decimal(os.getenv("SIMULATION_SLIPPAGE", "0.0001")),
            tick_interval=float(os.getenv("SIMULATION_TICK_INTERVAL", "5.0")),
            strategy_interval=float(os.getenv("SIMULATION_STRATEGY_INTERVAL", "60.0")),
            max_positions=int(os.getenv("MAX_OPEN_POSITIONS", "5")),
            max_risk_per_trade=Decimal(os.getenv("MAX_RISK_PER_TRADE", "0.02")),
            min_risk_reward_ratio=Decimal(os.getenv("MIN_RISK_REWARD_RATIO", "3.0")),
        )
    
    def is_simulation_mode(self) -> bool:
        """Check if running in simulation mode."""
        return self.trading_mode == "simulation" or not self.trading_approved
    
    def is_live_mode(self) -> bool:
        """Check if running in live mode."""
        return self.trading_mode == "live" and self.trading_approved
    
    def can_trade_live(self) -> bool:
        """Check if live trading is allowed."""
        return self.is_live_mode()
