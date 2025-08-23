"""Backtesting package for the trading bot."""

__version__ = "1.0.0"

# Import components that don't require backtrader
from .storage import BacktestStorage
from .metrics import BacktestMetrics
from .integrity import DataIntegrityChecker

# Import runner conditionally to avoid backtrader dependency issues
try:
    from .runner import BacktestRunner
    __all__ = [
        "BacktestRunner",
        "BacktestStorage", 
        "BacktestMetrics",
        "DataIntegrityChecker",
    ]
except ImportError:
    # If backtrader is not available, exclude runner from exports
    __all__ = [
        "BacktestStorage", 
        "BacktestMetrics",
        "DataIntegrityChecker",
    ]
