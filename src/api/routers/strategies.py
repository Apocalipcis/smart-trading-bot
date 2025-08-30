"""Strategies router for strategy management and metadata."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status

from ..schemas import (
    StrategyInfo, 
    TimeframeRole, 
    TimeframeConstraint,
    APIResponse
)

router = APIRouter(prefix="/strategies", tags=["strategies"])

# Strategy metadata with role requirements
STRATEGIES_METADATA = [
    StrategyInfo(
        name="SMC",
        description="Smart Money Concepts Strategy - Uses order blocks, fair value gaps, and market structure for entry/exit decisions",
        version="1.0.0",
        required_roles=[TimeframeRole.HTF, TimeframeRole.LTF],
        role_constraints=[
            TimeframeConstraint(
                role=TimeframeRole.HTF,
                min_timeframe="1h",
                max_timeframe="1d",
                description="HTF for trend direction and market structure"
            ),
            TimeframeConstraint(
                role=TimeframeRole.LTF,
                min_timeframe="5m",
                max_timeframe="30m",
                description="LTF for entry/exit timing and order block identification"
            )
        ],
        parameters={
            "rsi_period": {"type": "int", "default": 14, "min": 1, "max": 50, "description": "RSI period"},
            "ma_period": {"type": "int", "default": 20, "min": 5, "max": 200, "description": "Moving average period"},
            "stop_loss_pct": {"type": "float", "default": 2.0, "min": 0.5, "max": 10.0, "description": "Stop loss percentage"},
            "take_profit_ratio": {"type": "float", "default": 3.0, "min": 1.0, "max": 10.0, "description": "Risk-reward ratio"},
            "min_volume_ratio": {"type": "float", "default": 1.5, "min": 1.0, "max": 5.0, "description": "Minimum volume ratio for confirmation"}
        },
        is_active=True
    ),
    StrategyInfo(
        name="SIMPLE_TEST",
        description="Simple test strategy for basic functionality validation",
        version="1.0.0",
        required_roles=[TimeframeRole.LTF],
        role_constraints=[
            TimeframeConstraint(
                role=TimeframeRole.LTF,
                min_timeframe="1m",
                max_timeframe="1h",
                description="Single timeframe for simple testing"
            )
        ],
        parameters={
            "ma_fast": {"type": "int", "default": 10, "min": 5, "max": 50, "description": "Fast moving average period"},
            "ma_slow": {"type": "int", "default": 20, "min": 10, "max": 100, "description": "Slow moving average period"},
            "stop_loss_pct": {"type": "float", "default": 1.0, "min": 0.1, "max": 5.0, "description": "Stop loss percentage"}
        },
        is_active=True
    ),
    StrategyInfo(
        name="MEAN_REVERSION",
        description="Mean reversion strategy using Bollinger Bands and RSI",
        version="1.0.0",
        required_roles=[TimeframeRole.HTF, TimeframeRole.LTF],
        role_constraints=[
            TimeframeConstraint(
                role=TimeframeRole.HTF,
                min_timeframe="4h",
                max_timeframe="1d",
                description="HTF for trend context and mean calculation"
            ),
            TimeframeConstraint(
                role=TimeframeRole.LTF,
                min_timeframe="15m",
                max_timeframe="1h",
                description="LTF for entry/exit signals"
            )
        ],
        parameters={
            "bb_period": {"type": "int", "default": 20, "min": 10, "max": 50, "description": "Bollinger Bands period"},
            "bb_std": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0, "description": "Bollinger Bands standard deviation"},
            "rsi_period": {"type": "int", "default": 14, "min": 10, "max": 30, "description": "RSI period"},
            "rsi_oversold": {"type": "int", "default": 30, "min": 20, "max": 40, "description": "RSI oversold threshold"},
            "rsi_overbought": {"type": "int", "default": 70, "min": 60, "max": 80, "description": "RSI overbought threshold"}
        },
        is_active=True
    ),
    StrategyInfo(
        name="BREAKOUT",
        description="Breakout strategy using support/resistance levels and volume confirmation",
        version="1.0.0",
        required_roles=[TimeframeRole.HTF, TimeframeRole.LTF],
        role_constraints=[
            TimeframeConstraint(
                role=TimeframeRole.HTF,
                min_timeframe="1h",
                max_timeframe="1d",
                description="HTF for support/resistance identification"
            ),
            TimeframeConstraint(
                role=TimeframeRole.LTF,
                min_timeframe="5m",
                max_timeframe="30m",
                description="LTF for breakout confirmation and entry"
            )
        ],
        parameters={
            "support_resistance_period": {"type": "int", "default": 20, "min": 10, "max": 50, "description": "Period for S/R calculation"},
            "breakout_threshold": {"type": "float", "default": 0.5, "min": 0.1, "max": 2.0, "description": "Breakout threshold percentage"},
            "volume_multiplier": {"type": "float", "default": 1.5, "min": 1.0, "max": 5.0, "description": "Volume confirmation multiplier"},
            "retest_enabled": {"type": "bool", "default": True, "description": "Enable retest entries"},
            "stop_loss_atr": {"type": "float", "default": 2.0, "min": 1.0, "max": 5.0, "description": "Stop loss in ATR multiples"}
        },
        is_active=True
    )
]


@router.get("/", response_model=List[StrategyInfo])
async def get_strategies() -> List[StrategyInfo]:
    """Get all available strategies with their metadata and role requirements."""
    return [s for s in STRATEGIES_METADATA if s.is_active]


@router.get("/{strategy_name}", response_model=StrategyInfo)
async def get_strategy(strategy_name: str) -> StrategyInfo:
    """Get information about a specific strategy."""
    for strategy in STRATEGIES_METADATA:
        if strategy.name.upper() == strategy_name.upper() and strategy.is_active:
            return strategy
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Strategy '{strategy_name}' not found"
    )


@router.post("/{strategy_name}/validate")
async def validate_strategy_requirements(
    strategy_name: str,
    timeframes: List[str],
    tf_roles: dict
) -> APIResponse:
    """Validate that timeframe role assignments meet strategy requirements."""
    # Find strategy
    strategy = None
    for s in STRATEGIES_METADATA:
        if s.name.upper() == strategy_name.upper() and s.is_active:
            strategy = s
            break
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_name}' not found"
        )
    
    errors = []
    warnings = []
    
    # Check required roles
    assigned_roles = set(tf_roles.values())
    required_roles = set(strategy.required_roles)
    
    missing_roles = required_roles - assigned_roles
    extra_roles = assigned_roles - required_roles
    
    if missing_roles:
        errors.append(f"Missing required roles: {', '.join(missing_roles)}")
    
    if extra_roles:
        warnings.append(f"Extra roles assigned: {', '.join(extra_roles)}")
    
    # Check role constraints
    for constraint in strategy.role_constraints:
        for tf, role in tf_roles.items():
            if role == constraint.role:
                # Validate timeframe against constraint
                tf_minutes = _timeframe_to_minutes(tf)
                min_minutes = _timeframe_to_minutes(constraint.min_timeframe)
                max_minutes = _timeframe_to_minutes(constraint.max_timeframe)
                
                if tf_minutes < min_minutes:
                    errors.append(f"Timeframe '{tf}' is too small for role '{role}' in strategy '{strategy_name}'. Minimum: {constraint.min_timeframe}")
                elif tf_minutes > max_minutes:
                    errors.append(f"Timeframe '{tf}' is too large for role '{role}' in strategy '{strategy_name}'. Maximum: {constraint.max_timeframe}")
    
    return APIResponse(
        success=len(errors) == 0,
        data={
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "strategy": strategy.name,
            "required_roles": list(required_roles),
            "assigned_roles": list(assigned_roles)
        },
        message=f"Strategy '{strategy_name}' validation completed"
    )


@router.get("/{strategy_name}/parameters")
async def get_strategy_parameters(strategy_name: str) -> APIResponse:
    """Get parameters for a specific strategy."""
    for strategy in STRATEGIES_METADATA:
        if strategy.name.upper() == strategy_name.upper() and strategy.is_active:
            return APIResponse(
                success=True,
                data=strategy.parameters,
                message=f"Parameters for strategy '{strategy_name}'"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Strategy '{strategy_name}' not found"
    )


def _timeframe_to_minutes(timeframe: str) -> int:
    """Convert timeframe string to minutes."""
    if timeframe.endswith('m'):
        return int(timeframe[:-1])
    elif timeframe.endswith('h'):
        return int(timeframe[:-1]) * 60
    elif timeframe.endswith('d'):
        return int(timeframe[:-1]) * 1440
    elif timeframe.endswith('w'):
        return int(timeframe[:-1]) * 10080
    elif timeframe.endswith('M'):
        return int(timeframe[:-1]) * 43200
    else:
        raise ValueError(f"Invalid timeframe format: {timeframe}")
