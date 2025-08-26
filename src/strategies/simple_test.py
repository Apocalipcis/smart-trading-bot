"""
Simple Test Strategy

A basic strategy for testing the backtest infrastructure.
"""

import backtrader as bt
from .base import BaseStrategy


class SimpleTestStrategy(BaseStrategy):
    """
    Simple test strategy that just holds the position.
    """
    
    params = (
        ('risk_per_trade', 0.02),
        ('position_size', 0.1),
        ('min_risk_reward', 1.5),
        ('use_stop_loss', False),
        ('use_take_profit', False),
        ('max_positions', 1),
    )
    
    def __init__(self):
        """Initialize the simple test strategy."""
        super().__init__()
        self.order = None
        self.bought = False
    
    def next(self):
        """Called for each new bar."""
        # Simple strategy: buy on first bar, hold
        if not self.bought and len(self.data) > 0:
            self.order = self.buy()
            self.bought = True
            print(f"Bought at {self.data.close[0]}")
    
    def stop(self):
        """Called when strategy stops."""
        print(f"Strategy finished. Final value: {self.broker.getvalue()}")
