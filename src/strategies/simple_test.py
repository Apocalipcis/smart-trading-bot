"""
Simple Test Strategy

A basic strategy for testing the backtest infrastructure.
"""

import backtrader as bt
try:
    from src.strategies.base import BaseStrategy
except ImportError:
    from .base import BaseStrategy


class SimpleTestStrategy(BaseStrategy):
    """
    Simple test strategy that generates signals more frequently for testing.
    """
    
    params = (
        ('risk_per_trade', 0.02),
        ('position_size', 0.1),
        ('min_risk_reward', 1.5),
        ('use_stop_loss', True),
        ('use_take_profit', True),
        ('max_positions', 1),
        ('signal_frequency', 5),  # Generate signal every N bars
    )
    
    def __init__(self):
        """Initialize the simple test strategy."""
        super().__init__()
        self.order = None
        self.bought = False
        self.bar_count = 0
        self.current_position = None
        self.trade_history = []
        
        # Add simple indicators for signal generation
        self.sma_fast = bt.indicators.SimpleMovingAverage(self.data.close, period=10)
        self.sma_slow = bt.indicators.SimpleMovingAverage(self.data.close, period=20)
        self.rsi = bt.indicators.RSI(self.data.close, period=14)
    
    def next(self):
        """Called for each new bar."""
        self.bar_count += 1
        
        # Generate signals more frequently for testing
        if self.bar_count % self.params.signal_frequency == 0:
            signals = self.generate_signals()
            if signals:
                # Execute the first signal
                signal = signals[0]
                if signal.side == 'long' and not self.bought:
                    # Calculate position size based on risk
                    entry_price = signal.entry
                    stop_loss = signal.stop_loss
                    risk_amount = self.broker.getvalue() * self.params.risk_per_trade
                    position_size = risk_amount / abs(entry_price - stop_loss)
                    
                    # Place the order
                    self.order = self.buy(size=position_size)
                    self.bought = True
                    
                    # Track position details
                    self.current_position = {
                        'entry_date': self.data.datetime.datetime(),
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': signal.take_profit,
                        'size': position_size,
                        'side': 'long',
                        'signal_metadata': signal.metadata
                    }
                    
                    print(f"Opened LONG position at {entry_price}, SL: {stop_loss}, TP: {signal.take_profit}")
                
                elif signal.side == 'short' and not self.bought:
                    # Calculate position size based on risk
                    entry_price = signal.entry
                    stop_loss = signal.stop_loss
                    risk_amount = self.broker.getvalue() * self.params.risk_per_trade
                    position_size = risk_amount / abs(entry_price - stop_loss)
                    
                    # Place the order
                    self.order = self.sell(size=position_size)
                    self.bought = True
                    
                    # Track position details
                    self.current_position = {
                        'entry_date': self.data.datetime.datetime(),
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': signal.take_profit,
                        'size': -position_size,  # Negative for short
                        'side': 'short',
                        'signal_metadata': signal.metadata
                    }
                    
                    print(f"Opened SHORT position at {entry_price}, SL: {stop_loss}, TP: {signal.take_profit}")
        
        # Check if we need to close positions
        if self.bought and self.current_position:
            self._check_exit_conditions()
    
    def _check_exit_conditions(self):
        """Check if position should be closed based on TP/SL."""
        if not self.current_position:
            return
        
        current_price = self.data.close[0]
        position = self.current_position
        
        if position['side'] == 'long':
            # Check take profit
            if current_price >= position['take_profit']:
                self._close_position("Take Profit", current_price)
            # Check stop loss
            elif current_price <= position['stop_loss']:
                self._close_position("Stop Loss", current_price)
        
        elif position['side'] == 'short':
            # Check take profit
            if current_price <= position['take_profit']:
                self._close_position("Take Profit", current_price)
            # Check stop loss
            elif current_price >= position['stop_loss']:
                self._close_position("Stop Loss", current_price)
    
    def _close_position(self, exit_reason: str, exit_price: float):
        """Close the current position and record trade details."""
        if not self.current_position:
            return
        
        position = self.current_position
        exit_date = self.data.datetime.datetime()
        
        # Calculate P&L
        if position['side'] == 'long':
            pnl = (exit_price - position['entry_price']) * abs(position['size'])
        else:  # short
            pnl = (position['entry_price'] - exit_price) * abs(position['size'])
        
        # Calculate return percentage
        return_pct = (pnl / (abs(position['size']) * position['entry_price'])) * 100
        
        # Calculate duration
        duration_hours = (exit_date - position['entry_date']).total_seconds() / 3600
        
        # Record trade
        trade_record = {
            'entry_date': position['entry_date'],
            'exit_date': exit_date,
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'size': position['size'],
            'side': position['side'],
            'pnl': pnl,
            'pnl_comm': 0,  # Would calculate from commission
            'pnl_slippage': 0,  # Would calculate from slippage
            'return_pct': return_pct,
            'exit_reason': exit_reason,
            'stop_loss': position['stop_loss'],
            'take_profit': position['take_profit'],
            'duration_hours': duration_hours,
            'metadata': {
                'signal_type': position['signal_metadata'].get('type', 'unknown'),
                'rsi': position['signal_metadata'].get('rsi', 0),
                'fast_ma': position['signal_metadata'].get('fast_ma', 0),
                'slow_ma': position['signal_metadata'].get('slow_ma', 0)
            }
        }
        
        self.trade_history.append(trade_record)
        
        # Close the position
        if position['side'] == 'long':
            self.close()
        else:
            self.close()
        
        self.bought = False
        self.current_position = None
        
        print(f"Closed {position['side']} position via {exit_reason} at {exit_price}, P&L: ${pnl:.2f} ({return_pct:.2f}%)")
    
    def generate_signals(self):
        """Generate trading signals for testing."""
        signals = []
        
        # Simple moving average crossover signal
        if len(self.data) > 20:  # Ensure we have enough data
            if self.sma_fast[0] > self.sma_slow[0] and self.sma_fast[-1] <= self.sma_slow[-1]:
                # Golden cross - bullish signal
                entry = self.data.close[0]
                stop_loss = entry * 0.98  # 2% stop loss
                take_profit = entry * 1.03  # 3% take profit
                
                signals.append(self._create_signal(
                    side='long',
                    entry=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=0.7,
                    metadata={'type': 'MA_crossover', 'fast_ma': float(self.sma_fast[0]), 'slow_ma': float(self.sma_slow[0])}
                ))
            
            elif self.sma_fast[0] < self.sma_slow[0] and self.sma_fast[-1] >= self.sma_slow[-1]:
                # Death cross - bearish signal
                entry = self.data.close[0]
                stop_loss = entry * 1.02  # 2% stop loss
                take_profit = entry * 0.97  # 3% take profit
                
                signals.append(self._create_signal(
                    side='short',
                    entry=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=0.7,
                    metadata={'type': 'MA_crossover', 'fast_ma': float(self.sma_fast[0]), 'slow_ma': float(self.sma_slow[0])}
                ))
        
        # RSI oversold/overbought signals
        if len(self.data) > 14:
            if self.rsi[0] < 30:  # Oversold - bullish signal
                entry = self.data.close[0]
                stop_loss = entry * 0.98
                take_profit = entry * 1.03
                
                signals.append(self._create_signal(
                    side='long',
                    entry=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=0.6,
                    metadata={'type': 'RSI_oversold', 'rsi': float(self.rsi[0])}
                ))
            
            elif self.rsi[0] > 70:  # Overbought - bearish signal
                entry = self.data.close[0]
                stop_loss = entry * 1.02
                take_profit = entry * 0.97
                
                signals.append(self._create_signal(
                    side='short',
                    entry=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=0.6,
                    metadata={'type': 'RSI_overbought', 'rsi': float(self.rsi[0])}
                ))
        
        return signals
    
    def _create_signal(self, side, entry, stop_loss, take_profit, confidence, metadata):
        """Create a signal object."""
        from .base import Signal
        return Signal(
            side=side,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            metadata=metadata
        )
    
    def stop(self):
        """Called when strategy stops."""
        print(f"Strategy finished. Final value: {self.broker.getvalue()}")
        if self.bought and self.current_position:
            print(f"Position was held until the end")
            # Close any remaining position
            self._close_position("Strategy End", self.data.close[0])
        
        print(f"Total trades executed: {len(self.trade_history)}")
        for i, trade in enumerate(self.trade_history, 1):
            print(f"Trade {i}: {trade['side'].upper()} {trade['exit_reason']} - Entry: ${trade['entry_price']:.2f}, Exit: ${trade['exit_price']:.2f}, P&L: ${trade['pnl']:.2f} ({trade['return_pct']:.2f}%)")
