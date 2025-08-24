"""
Base Strategy Class

This module provides the abstract base class for all trading strategies.
All strategies must implement the signal generation contract and follow
the Backtrader framework patterns.
"""

from abc import abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import backtrader as bt
import pandas as pd
from pydantic import BaseModel, Field, field_validator


class Signal(BaseModel):
    """Trading signal with all required parameters."""
    
    side: str = Field(..., description="Trade side: 'long' or 'short'")
    entry: float = Field(..., gt=0, description="Entry price")
    stop_loss: float = Field(..., gt=0, description="Stop loss price")
    take_profit: float = Field(..., gt=0, description="Take profit price")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence 0-1")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Signal timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional signal metadata")
    
    @field_validator('side')
    @classmethod
    def validate_side(cls, v):
        if v not in ['long', 'short']:
            raise ValueError("side must be 'long' or 'short'")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BaseStrategy(bt.Strategy):
    """
    Abstract base class for all trading strategies.
    
    This class provides the foundation for implementing trading strategies
    using the Backtrader framework. It enforces the signal generation
    contract and provides common functionality.
    """
    
    # Strategy parameters
    params = (
        ('risk_per_trade', 0.02),  # 2% risk per trade
        ('position_size', 0.1),    # 10% of available capital per trade
        ('use_stop_loss', True),   # Enable stop loss
        ('use_take_profit', True), # Enable take profit
        ('min_risk_reward', 3.0),  # Minimum risk-reward ratio
        ('max_positions', 5),      # Maximum concurrent positions
    )
    
    def __init__(self):
        """Initialize the strategy."""
        super().__init__()
        
        # Initialize tracking variables
        self.signals: List[Signal] = []
        self.current_positions = 0
        self.trade_history: List[Dict[str, Any]] = []
        
        # Validate strategy parameters
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate strategy parameters."""
        if self.params.risk_per_trade <= 0 or self.params.risk_per_trade > 0.1:
            raise ValueError("risk_per_trade must be between 0 and 0.1 (10%)")
        
        if self.params.position_size <= 0 or self.params.position_size > 1.0:
            raise ValueError("position_size must be between 0 and 1.0 (100%)")
        
        if self.params.min_risk_reward < 1.0:
            raise ValueError("min_risk_reward must be >= 1.0")
    
    @abstractmethod
    def generate_signals(self) -> List[Signal]:
        """
        Generate trading signals based on current market conditions.
        
        This method must be implemented by all concrete strategy classes.
        It should analyze the current market data and return a list of
        trading signals that meet the risk-reward requirements.
        
        Returns:
            List[Signal]: List of valid trading signals
        """
        pass
    
    def next(self):
        """
        Main strategy logic executed on each bar.
        
        This method is called by Backtrader for each new data bar.
        It implements the core strategy logic and position management.
        """
        # Generate signals
        signals = self.generate_signals()
        
        # Process signals
        for signal in signals:
            if self._validate_signal(signal):
                self._execute_signal(signal)
        
        # Update position tracking
        self._update_positions()
    
    def _validate_signal(self, signal: Signal) -> bool:
        """
        Validate a trading signal against strategy rules.
        
        Args:
            signal: The trading signal to validate
            
        Returns:
            bool: True if signal is valid, False otherwise
        """
        # Check if we can take more positions
        if self.current_positions >= self.params.max_positions:
            return False
        
        # Check risk-reward ratio
        if self.params.use_stop_loss and self.params.use_take_profit:
            entry = signal.entry
            sl = signal.stop_loss
            tp = signal.take_profit
            
            if signal.side == 'long':
                risk = entry - sl
                reward = tp - entry
            else:  # short
                risk = sl - entry
                reward = entry - tp
            
            if risk <= 0 or reward <= 0:
                return False
            
            risk_reward = reward / risk
            if risk_reward < self.params.min_risk_reward:
                return False
        
        # Check confidence threshold
        if signal.confidence < 0.5:  # Minimum 50% confidence
            return False
        
        return True
    
    def _execute_signal(self, signal: Signal):
        """
        Execute a validated trading signal.
        
        Args:
            signal: The validated trading signal to execute
        """
        # Calculate position size based on risk
        size = self._calculate_position_size(signal)
        
        if signal.side == 'long':
            self.buy(size=size, price=signal.entry)
        else:  # short
            self.sell(size=size, price=signal.entry)
        
        # Store signal
        self.signals.append(signal)
        
        # Update position count
        self.current_positions += 1
    
    def _calculate_position_size(self, signal: Signal) -> float:
        """
        Calculate position size based on risk management rules.
        
        Args:
            signal: The trading signal
            
        Returns:
            float: Position size in units
        """
        # Get available capital
        capital = self.broker.getcash()
        
        # Calculate risk amount
        risk_amount = capital * self.params.risk_per_trade
        
        # Calculate position size based on stop loss distance
        if self.params.use_stop_loss:
            entry = signal.entry
            sl = signal.stop_loss
            
            if signal.side == 'long':
                risk_per_unit = entry - sl
            else:  # short
                risk_per_unit = sl - entry
            
            if risk_per_unit > 0:
                size = risk_amount / risk_per_unit
            else:
                size = capital * self.params.position_size / entry
        else:
            # Use fixed position size if no stop loss
            size = capital * self.params.position_size / signal.entry
        
        return size
    
    def _update_positions(self):
        """Update position tracking and history."""
        # Count current positions
        self.current_positions = len([pos for pos in self.broker.positions.values() if pos.size != 0])
        
        # Update trade history
        for trade in self.broker.trades:
            if trade.status == trade.Status.Closed and trade not in self.trade_history:
                trade_info = {
                    'entry_date': trade.dtopen,
                    'exit_date': trade.dtclose,
                    'entry_price': trade.price,
                    'exit_price': trade.pclose,
                    'size': trade.size,
                    'pnl': trade.pnl,
                    'pnlcomm': trade.pnlcomm,
                    'status': 'closed'
                }
                self.trade_history.append(trade_info)
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy statistics.
        
        Returns:
            Dict[str, Any]: Strategy performance statistics
        """
        return {
            'total_signals': len(self.signals),
            'current_positions': self.current_positions,
            'total_trades': len(self.trade_history),
            'total_pnl': sum(trade['pnl'] for trade in self.trade_history),
            'winning_trades': len([t for t in self.trade_history if t['pnl'] > 0]),
            'losing_trades': len([t for t in self.trade_history if t['pnl'] < 0]),
            'parameters': {
                'risk_per_trade': self.params.risk_per_trade,
                'position_size': self.params.position_size,
                'min_risk_reward': self.params.min_risk_reward,
                'max_positions': self.params.max_positions
            }
        }
    
    def stop(self):
        """Called when the strategy stops."""
        # Log final statistics
        stats = self.get_strategy_stats()
        print(f"Strategy {self.__class__.__name__} finished:")
        print(f"  Total signals: {stats['total_signals']}")
        print(f"  Total trades: {stats['total_trades']}")
        print(f"  Total PnL: ${stats['total_pnl']:.2f}")
        print(f"  Win rate: {stats['winning_trades']}/{stats['total_trades']}")
