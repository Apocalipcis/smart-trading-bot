"""
Trading Strategies Package

This package contains trading strategy implementations for the trading bot.
All strategies inherit from a base class that provides the signal generation contract.
"""

from .base import BaseStrategy
from .registry import StrategyRegistry
# SMCStrategy removed - using SMCSignalStrategy instead
from .smc_signal import SMCSignalStrategy

__version__ = "1.0.0"
__all__ = ["BaseStrategy", "StrategyRegistry", "SMCSignalStrategy"]
