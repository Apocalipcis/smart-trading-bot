"""
Trading Strategies Package

This package contains trading strategy implementations for the trading bot.
All strategies inherit from a base class that provides the signal generation contract.
"""

from .base import BaseStrategy
from .registry import StrategyRegistry
from .smc import SMCStrategy

__version__ = "1.0.0"
__all__ = ["BaseStrategy", "StrategyRegistry", "SMCStrategy"]
