"""
SMC Strategy Configuration Classes

This module provides configuration classes for the Smart Money Concepts strategy,
allowing dynamic configuration of indicators, filters, and SMC elements without code changes.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class RSIConfig(BaseModel):
    """RSI indicator configuration."""
    enabled: bool = True
    period: int = Field(default=14, ge=1, le=100)
    overbought: float = Field(default=70.0, ge=50.0, le=100.0)
    oversold: float = Field(default=30.0, ge=0.0, le=50.0)


class MACDConfig(BaseModel):
    """MACD indicator configuration."""
    enabled: bool = False
    fast_period: int = Field(default=12, ge=1, le=50)
    slow_period: int = Field(default=26, ge=1, le=100)
    signal_period: int = Field(default=9, ge=1, le=50)


class BollingerBandsConfig(BaseModel):
    """Bollinger Bands indicator configuration."""
    enabled: bool = False
    period: int = Field(default=20, ge=1, le=100)
    deviation: float = Field(default=2.0, ge=0.5, le=5.0)


class StochasticConfig(BaseModel):
    """Stochastic oscillator configuration."""
    enabled: bool = False
    k_period: int = Field(default=14, ge=1, le=50)
    d_period: int = Field(default=3, ge=1, le=20)
    overbought: float = Field(default=80.0, ge=50.0, le=100.0)
    oversold: float = Field(default=20.0, ge=0.0, le=50.0)


class VolumeConfig(BaseModel):
    """Volume indicator configuration."""
    enabled: bool = True
    period: int = Field(default=20, ge=1, le=100)


class ATRConfig(BaseModel):
    """ATR indicator configuration."""
    enabled: bool = True
    period: int = Field(default=14, ge=1, le=100)


class IndicatorsConfig(BaseModel):
    """Complete indicators configuration."""
    rsi: RSIConfig = Field(default_factory=RSIConfig)
    macd: MACDConfig = Field(default_factory=MACDConfig)
    bbands: BollingerBandsConfig = Field(default_factory=BollingerBandsConfig)
    stochastic: StochasticConfig = Field(default_factory=StochasticConfig)
    volume: VolumeConfig = Field(default_factory=VolumeConfig)
    atr: ATRConfig = Field(default_factory=ATRConfig)


class RSIFilterConfig(BaseModel):
    """RSI filter configuration."""
    enabled: bool = True
    min_confidence: float = Field(default=0.3, ge=0.0, le=1.0)
    overbought: float = Field(default=70.0, ge=50.0, le=100.0)
    oversold: float = Field(default=30.0, ge=0.0, le=50.0)


class VolumeFilterConfig(BaseModel):
    """Volume filter configuration."""
    enabled: bool = True
    min_volume_ratio: float = Field(default=0.8, ge=0.1, le=10.0)


class BBFilterConfig(BaseModel):
    """Bollinger Bands filter configuration."""
    enabled: bool = False
    position_threshold: float = Field(default=0.1, ge=0.0, le=1.0)


class MACDFilterConfig(BaseModel):
    """MACD filter configuration."""
    enabled: bool = False
    signal_cross: bool = True


class StochasticFilterConfig(BaseModel):
    """Stochastic filter configuration."""
    enabled: bool = False
    overbought: float = Field(default=80.0, ge=50.0, le=100.0)
    oversold: float = Field(default=20.0, ge=0.0, le=50.0)


class FiltersConfig(BaseModel):
    """Complete filters configuration."""
    rsi: RSIFilterConfig = Field(default_factory=RSIFilterConfig)
    volume: VolumeFilterConfig = Field(default_factory=VolumeFilterConfig)
    bbands: BBFilterConfig = Field(default_factory=BBFilterConfig)
    macd: MACDFilterConfig = Field(default_factory=MACDFilterConfig)
    stochastic: StochasticFilterConfig = Field(default_factory=StochasticFilterConfig)
    min_filters_required: int = Field(default=2, ge=1, le=5)


class OrderBlocksConfig(BaseModel):
    """Order Blocks SMC element configuration."""
    enabled: bool = True
    lookback_bars: int = Field(default=20, ge=5, le=100)
    volume_threshold: float = Field(default=1.5, ge=0.5, le=5.0)


class FairValueGapsConfig(BaseModel):
    """Fair Value Gaps SMC element configuration."""
    enabled: bool = True
    min_gap_pct: float = Field(default=0.5, ge=0.1, le=10.0)


class LiquidityPoolsConfig(BaseModel):
    """Liquidity Pools SMC element configuration."""
    enabled: bool = True
    swing_threshold: float = Field(default=0.02, ge=0.005, le=0.1)


class BreakOfStructureConfig(BaseModel):
    """Break of Structure SMC element configuration."""
    enabled: bool = True
    confirmation_bars: int = Field(default=2, ge=1, le=10)


class SMCElementsConfig(BaseModel):
    """Complete SMC elements configuration."""
    order_blocks: OrderBlocksConfig = Field(default_factory=OrderBlocksConfig)
    fair_value_gaps: FairValueGapsConfig = Field(default_factory=FairValueGapsConfig)
    liquidity_pools: LiquidityPoolsConfig = Field(default_factory=LiquidityPoolsConfig)
    break_of_structure: BreakOfStructureConfig = Field(default_factory=BreakOfStructureConfig)


class RiskManagementConfig(BaseModel):
    """Risk management configuration."""
    risk_per_trade: float = Field(default=0.01, ge=0.001, le=0.1)
    min_risk_reward: float = Field(default=3.0, ge=1.0, le=10.0)
    max_positions: int = Field(default=3, ge=1, le=10)
    sl_buffer_atr: float = Field(default=0.15, ge=0.05, le=1.0)


class SMCStrategyConfig(BaseModel):
    """Complete SMC strategy configuration."""
    
    # Basic parameters
    name: str = "SMC Strategy"
    description: str = "Smart Money Concepts Strategy"
    htf_timeframe: str = "4h"
    ltf_timeframe: str = "15m"
    scalping_mode: bool = False
    
    # Configurations
    indicators: IndicatorsConfig = Field(default_factory=IndicatorsConfig)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    smc_elements: SMCElementsConfig = Field(default_factory=SMCElementsConfig)
    risk_management: RiskManagementConfig = Field(default_factory=RiskManagementConfig)
    
    @field_validator('htf_timeframe', 'ltf_timeframe')
    @classmethod
    def validate_timeframe(cls, v):
        """Validate timeframe format."""
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        if v not in valid_timeframes:
            raise ValueError(f"Invalid timeframe: {v}. Valid timeframes: {valid_timeframes}")
        return v
    
    def get_default_config() -> 'SMCStrategyConfig':
        """Get default configuration."""
        return SMCStrategyConfig()
    
    def get_conservative_config() -> 'SMCStrategyConfig':
        """Get conservative configuration (low risk, high quality)."""
        return SMCStrategyConfig(
            name="Conservative SMC",
            description="Low risk, high quality signals",
            indicators=IndicatorsConfig(
                rsi=RSIConfig(enabled=True, period=14, overbought=75, oversold=25),
                macd=MACDConfig(enabled=True, fast_period=12, slow_period=26, signal_period=9),
                bbands=BollingerBandsConfig(enabled=True, period=20, deviation=2.0),
                stochastic=StochasticConfig(enabled=False),
                volume=VolumeConfig(enabled=True, period=20),
                atr=ATRConfig(enabled=True, period=14)
            ),
            filters=FiltersConfig(
                rsi=RSIFilterConfig(enabled=True, min_confidence=0.6),
                volume=VolumeFilterConfig(enabled=True, min_volume_ratio=1.2),
                bbands=BBFilterConfig(enabled=True, position_threshold=0.2),
                macd=MACDFilterConfig(enabled=True, signal_cross=True),
                stochastic=StochasticFilterConfig(enabled=False),
                min_filters_required=3
            ),
            smc_elements=SMCElementsConfig(
                order_blocks=OrderBlocksConfig(enabled=True, lookback_bars=25, volume_threshold=2.0),
                fair_value_gaps=FairValueGapsConfig(enabled=True, min_gap_pct=1.0),
                liquidity_pools=LiquidityPoolsConfig(enabled=True, swing_threshold=0.03),
                break_of_structure=BreakOfStructureConfig(enabled=True, confirmation_bars=3)
            ),
            risk_management=RiskManagementConfig(
                risk_per_trade=0.01,
                min_risk_reward=4.0,
                max_positions=2,
                sl_buffer_atr=0.2
            )
        )
    
    def get_aggressive_config() -> 'SMCStrategyConfig':
        """Get aggressive configuration (high frequency, more signals)."""
        return SMCStrategyConfig(
            name="Aggressive SMC",
            description="High frequency, more signals",
            indicators=IndicatorsConfig(
                rsi=RSIConfig(enabled=True, period=10, overbought=80, oversold=20),
                macd=MACDConfig(enabled=False),
                bbands=BollingerBandsConfig(enabled=False),
                stochastic=StochasticConfig(enabled=False),
                volume=VolumeConfig(enabled=True, period=15),
                atr=ATRConfig(enabled=True, period=10)
            ),
            filters=FiltersConfig(
                rsi=RSIFilterConfig(enabled=True, min_confidence=0.3),
                volume=VolumeFilterConfig(enabled=True, min_volume_ratio=0.8),
                bbands=BBFilterConfig(enabled=False),
                macd=MACDFilterConfig(enabled=False),
                stochastic=StochasticFilterConfig(enabled=False),
                min_filters_required=2
            ),
            smc_elements=SMCElementsConfig(
                order_blocks=OrderBlocksConfig(enabled=True, lookback_bars=15, volume_threshold=1.2),
                fair_value_gaps=FairValueGapsConfig(enabled=True, min_gap_pct=0.3),
                liquidity_pools=LiquidityPoolsConfig(enabled=True, swing_threshold=0.01),
                break_of_structure=BreakOfStructureConfig(enabled=True, confirmation_bars=1)
            ),
            risk_management=RiskManagementConfig(
                risk_per_trade=0.02,
                min_risk_reward=2.5,
                max_positions=5,
                sl_buffer_atr=0.1
            )
        )
    
    def get_scalping_config() -> 'SMCStrategyConfig':
        """Get scalping configuration (fast entries, tight stops)."""
        return SMCStrategyConfig(
            name="Scalping SMC",
            description="Fast entries, tight stops",
            indicators=IndicatorsConfig(
                rsi=RSIConfig(enabled=True, period=7, overbought=70, oversold=30),
                macd=MACDConfig(enabled=False),
                bbands=BollingerBandsConfig(enabled=False),
                stochastic=StochasticConfig(enabled=True, k_period=5, d_period=3, overbought=80, oversold=20),
                volume=VolumeConfig(enabled=True, period=10),
                atr=ATRConfig(enabled=True, period=7)
            ),
            filters=FiltersConfig(
                rsi=RSIFilterConfig(enabled=True, min_confidence=0.4),
                volume=VolumeFilterConfig(enabled=True, min_volume_ratio=1.0),
                bbands=BBFilterConfig(enabled=False),
                macd=MACDFilterConfig(enabled=False),
                stochastic=StochasticFilterConfig(enabled=True, overbought=80, oversold=20),
                min_filters_required=2
            ),
            smc_elements=SMCElementsConfig(
                order_blocks=OrderBlocksConfig(enabled=True, lookback_bars=10, volume_threshold=1.5),
                fair_value_gaps=FairValueGapsConfig(enabled=True, min_gap_pct=0.2),
                liquidity_pools=LiquidityPoolsConfig(enabled=True, swing_threshold=0.005),
                break_of_structure=BreakOfStructureConfig(enabled=True, confirmation_bars=1)
            ),
            risk_management=RiskManagementConfig(
                risk_per_trade=0.005,
                min_risk_reward=2.0,
                max_positions=8,
                sl_buffer_atr=0.05
            )
        )


def load_config_from_dict(config_dict: Dict[str, Any]) -> SMCStrategyConfig:
    """Load configuration from dictionary."""
    return SMCStrategyConfig(**config_dict)


def load_config_from_json(json_path: str) -> SMCStrategyConfig:
    """Load configuration from JSON file."""
    import json
    with open(json_path, 'r') as f:
        config_dict = json.load(f)
    return load_config_from_dict(config_dict)


def save_config_to_json(config: SMCStrategyConfig, json_path: str) -> None:
    """Save configuration to JSON file."""
    import json
    with open(json_path, 'w') as f:
        json.dump(config.model_dump(), f, indent=2)
