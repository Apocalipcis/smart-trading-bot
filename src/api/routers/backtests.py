"""Backtests router for backtest management."""

from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from ..schemas import APIResponse, BacktestRequest, BacktestResult, PaginatedResponse

router = APIRouter(prefix="/backtests", tags=["backtests"])

# In-memory storage for backtest results (will be replaced with database)
_backtest_results: List[BacktestResult] = []


@router.get("/", response_model=PaginatedResponse)
async def get_backtests(
    pair: Optional[str] = None,
    strategy: Optional[str] = None,
    page: int = 1,
    size: int = 50
) -> PaginatedResponse:
    """Get all backtest results with optional filtering and pagination."""
    # Filter backtests
    filtered_backtests = _backtest_results.copy()
    
    if pair:
        filtered_backtests = [b for b in filtered_backtests if b.pair.upper() == pair.upper()]
    
    if strategy:
        filtered_backtests = [b for b in filtered_backtests if b.strategy.lower() == strategy.lower()]
    
    # Sort by creation date (newest first)
    filtered_backtests.sort(key=lambda x: x.created_at, reverse=True)
    
    # Apply pagination
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    
    total = len(filtered_backtests)
    items = filtered_backtests[start_idx:end_idx]
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{backtest_id}", response_model=BacktestResult)
async def get_backtest(backtest_id: str) -> BacktestResult:
    """Get a specific backtest result by ID."""
    for backtest in _backtest_results:
        if str(backtest.id) == backtest_id:
            return backtest
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Backtest {backtest_id} not found"
    )


@router.post("/", response_model=BacktestResult)
async def create_backtest(backtest_request: BacktestRequest) -> BacktestResult:
    """Create and run a new backtest."""
    # Generate backtest ID
    backtest_id = uuid4()
    
    # Track deprecation warnings
    deprecation_warnings = []
    
    # Handle legacy requests for backward compatibility
    if backtest_request.timeframe and not backtest_request.timeframes:
        # Convert legacy single timeframe to new format
        backtest_request.timeframes = [backtest_request.timeframe]
        
        # Smart role assignment based on timeframe
        if backtest_request.timeframe in ["1h", "4h", "1d"]:
            # Higher timeframes get HTF role
            backtest_request.tf_roles = {backtest_request.timeframe: "HTF"}
        else:
            # Lower timeframes get LTF role
            backtest_request.tf_roles = {backtest_request.timeframe: "LTF"}
        
        backtest_request.pairs = [backtest_request.pair] if backtest_request.pair else []
        backtest_request.initial_balance = backtest_request.initial_capital or 10000.0
        backtest_request.risk_per_trade = 2.0
        backtest_request.leverage = 1.0
        
        deprecation_warnings.append("Legacy 'timeframe' field is deprecated. Use 'timeframes' array instead.")
        deprecation_warnings.append("Legacy 'pair' field is deprecated. Use 'pairs' array instead.")
        if backtest_request.initial_capital:
            deprecation_warnings.append("Legacy 'initial_capital' field is deprecated. Use 'initial_balance' instead.")
    
    # Validate strategy requirements
    strategy_validation = await _validate_strategy_requirements(
        backtest_request.strategy,
        backtest_request.timeframes,
        backtest_request.tf_roles
    )
    
    # For legacy single-timeframe requests, be more lenient with validation
    is_legacy_request = backtest_request.timeframe and len(backtest_request.timeframes) == 1
    
    if not strategy_validation["valid"]:
        if is_legacy_request:
            # For legacy requests, only fail on constraint violations, not missing roles
            constraint_errors = [error for error in strategy_validation["errors"] 
                               if "too small" in error.lower() or "too large" in error.lower()]
            if constraint_errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Strategy validation failed",
                        "errors": constraint_errors,
                        "warnings": strategy_validation["warnings"]
                    }
                )
            # For missing roles in legacy requests, just add warnings
            deprecation_warnings.extend([f"Warning: {error}" for error in strategy_validation["errors"] 
                                       if "required role" in error.lower()])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Strategy validation failed",
                    "errors": strategy_validation["errors"],
                    "warnings": strategy_validation["warnings"]
                }
            )
    
    # Add strategy validation warnings to deprecation warnings
    deprecation_warnings.extend(strategy_validation["warnings"])
    
    # TODO: This is a placeholder implementation
    # In the actual implementation, this would:
    # 1. Validate the request
    # 2. Run the backtest using Backtrader
    # 3. Calculate metrics
    # 4. Save results and artifacts
    
    # Placeholder metrics calculation
    import random
    
    # Simulate backtest results
    initial_balance = backtest_request.initial_balance
    final_balance = initial_balance * (1 + random.uniform(-0.1, 0.3))  # -10% to +30%
    total_return = ((final_balance - initial_balance) / initial_balance) * 100
    
    total_trades = random.randint(10, 100)
    profitable_trades = int(total_trades * random.uniform(0.3, 0.7))
    win_rate = (profitable_trades / total_trades) * 100
    
    max_drawdown = random.uniform(5, 25)
    sharpe_ratio = random.uniform(-1, 2)
    
    # Create backtest result
    backtest_result = BacktestResult(
        id=backtest_id,
        pairs=backtest_request.pairs,
        strategy=backtest_request.strategy,
        timeframes=backtest_request.timeframes,
        tf_roles=backtest_request.tf_roles,
        start_date=backtest_request.start_date,
        end_date=backtest_request.end_date,
        initial_balance=initial_balance,
        final_balance=final_balance,
        total_return=total_return,
        win_rate=win_rate,
        total_trades=total_trades,
        profitable_trades=profitable_trades,
        max_drawdown=max_drawdown,
        sharpe_ratio=sharpe_ratio,
        parameters=backtest_request.parameters,
        artifacts_path=f"/data/artifacts/{backtest_id}",
        # Legacy support
        pair=backtest_request.pairs[0] if backtest_request.pairs else None,
        timeframe=backtest_request.timeframes[0] if backtest_request.timeframes else None,
        initial_capital=initial_balance
    )
    
    # Add to storage
    _backtest_results.append(backtest_result)
    
    return backtest_result


@router.delete("/{backtest_id}", response_model=APIResponse)
async def delete_backtest(backtest_id: str) -> APIResponse:
    """Delete a backtest result."""
    for i, backtest in enumerate(_backtest_results):
        if str(backtest.id) == backtest_id:
            del _backtest_results[i]
            return APIResponse(
                success=True,
                message=f"Backtest {backtest_id} deleted successfully"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Backtest {backtest_id} not found"
    )


@router.delete("/", response_model=APIResponse)
async def delete_all_backtests() -> APIResponse:
    """Delete all backtest results."""
    _backtest_results.clear()
    return APIResponse(
        success=True,
        message="All backtest results deleted successfully"
    )


@router.get("/stats/summary")
async def get_backtest_stats():
    """Get backtest statistics."""
    if not _backtest_results:
        return {
            "total_backtests": 0,
            "average_return": 0.0,
            "average_win_rate": 0.0,
            "best_strategy": None,
            "by_strategy": {},
            "by_pair": {}
        }
    
    total_backtests = len(_backtest_results)
    total_return = sum(b.total_return for b in _backtest_results)
    total_win_rate = sum(b.win_rate for b in _backtest_results)
    
    average_return = total_return / total_backtests
    average_win_rate = total_win_rate / total_backtests
    
    # Find best strategy by average return
    strategy_returns = {}
    for backtest in _backtest_results:
        strategy = backtest.strategy
        if strategy not in strategy_returns:
            strategy_returns[strategy] = []
        strategy_returns[strategy].append(backtest.total_return)
    
    best_strategy = None
    best_avg_return = float('-inf')
    for strategy, returns in strategy_returns.items():
        avg_return = sum(returns) / len(returns)
        if avg_return > best_avg_return:
            best_avg_return = avg_return
            best_strategy = strategy
    
    # Count by strategy and pair
    by_strategy = {}
    by_pair = {}
    
    for backtest in _backtest_results:
        strategy = backtest.strategy
        by_strategy[strategy] = by_strategy.get(strategy, 0) + 1
        
        pair = backtest.pair
        by_pair[pair] = by_pair.get(pair, 0) + 1
    
    return {
        "total_backtests": total_backtests,
        "average_return": average_return,
        "average_win_rate": average_win_rate,
        "best_strategy": best_strategy,
        "by_strategy": by_strategy,
        "by_pair": by_pair
    }


@router.get("/{backtest_id}/detailed")
async def get_backtest_detailed(backtest_id: str):
    """Get detailed backtest results including trade history."""
    # Find the backtest
    backtest = None
    for b in _backtest_results:
        if str(b.id) == backtest_id:
            backtest = b
            break
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest {backtest_id} not found"
        )
    
    # TODO: This would load detailed results from the artifacts file
    # For now, return a placeholder response
    return {
        "backtest": backtest,
        "trades": [],  # Would contain detailed trade history
        "equity_curve": [],  # Would contain equity curve data
        "drawdown_periods": [],  # Would contain drawdown periods
        "monthly_returns": {},  # Would contain monthly return breakdown
        "risk_metrics": {
            "var_95": 0.0,  # Value at Risk (95%)
            "max_drawdown_duration": 0,  # Maximum drawdown duration in days
            "calmar_ratio": 0.0,  # Calmar ratio
            "sortino_ratio": 0.0,  # Sortino ratio
        }
    }


@router.get("/available/strategies")
async def get_available_strategies():
    """Get list of available strategies for backtesting."""
    # TODO: This would query the strategy registry
    return [
        {
            "name": "SMC",
            "description": "Smart Money Concepts Strategy",
            "version": "1.0.0",
            "parameters": {
                "rsi_period": {"type": "int", "default": 14, "min": 1, "max": 50},
                "ma_period": {"type": "int", "default": 20, "min": 5, "max": 200},
                "stop_loss_pct": {"type": "float", "default": 2.0, "min": 0.5, "max": 10.0}
            }
        }
    ]


@router.get("/available/timeframes")
async def get_available_timeframes():
    """Get list of available timeframes for backtesting."""
    return [
        {"value": "1m", "label": "1 Minute"},
        {"value": "5m", "label": "5 Minutes"},
        {"value": "15m", "label": "15 Minutes"},
        {"value": "30m", "label": "30 Minutes"},
        {"value": "1h", "label": "1 Hour"},
        {"value": "4h", "label": "4 Hours"},
        {"value": "1d", "label": "1 Day"},
        {"value": "1w", "label": "1 Week"}
    ]


async def _validate_strategy_requirements(
    strategy_name: str,
    timeframes: List[str],
    tf_roles: dict
) -> dict:
    """Validate that timeframe role assignments meet strategy requirements."""
    # Import here to avoid circular imports
    from .strategies import STRATEGIES_METADATA
    
    # Find strategy
    strategy = None
    for s in STRATEGIES_METADATA:
        if s.name.upper() == strategy_name.upper() and s.is_active:
            strategy = s
            break
    
    if not strategy:
        return {
            "valid": False,
            "errors": [f"Strategy '{strategy_name}' not found"],
            "warnings": []
        }
    
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
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


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
