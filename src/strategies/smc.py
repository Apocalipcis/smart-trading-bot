"""
Smart Money Concepts (SMC) Strategy

This strategy implements Smart Money Concepts trading methodology,
focusing on institutional order flow, liquidity zones, and market structure.
It identifies key levels and generates signals based on price action
and volume analysis.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import pandas as pd
import backtrader as bt

from .base import BaseStrategy, Signal


class SMCStrategy(BaseStrategy):
    """
    Smart Money Concepts (SMC) Trading Strategy.
    
    This strategy implements institutional trading concepts including:
    - Liquidity zones identification
    - Market structure analysis
    - Order block detection
    - Fair value gaps
    - Volume profile analysis
    
    Parameters:
        lookback_period: Number of bars to look back for analysis
        volume_threshold: Minimum volume increase for signal confirmation
        swing_threshold: Minimum swing size for trend identification
        order_block_lookback: Bars to look back for order block detection
        fair_value_gap_threshold: Minimum gap size for FVG detection
    """
    
    # Strategy version
    version = "1.0.0"
    
    # Strategy parameters
    params = (
        ('lookback_period', 20),           # 20 bars lookback
        ('volume_threshold', 1.5),         # 1.5x average volume
        ('swing_threshold', 0.02),         # 2% minimum swing
        ('order_block_lookback', 10),      # 10 bars for order blocks
        ('fair_value_gap_threshold', 0.01), # 1% minimum gap
        ('liquidity_zone_threshold', 0.005), # 0.5% liquidity zone
        ('trend_confirmation_bars', 3),    # 3 bars for trend confirmation
        ('risk_per_trade', 0.02),          # 2% risk per trade
        ('min_risk_reward', 3.0),          # Minimum 3:1 risk-reward
        ('use_stop_loss', True),
        ('use_take_profit', True),
        ('max_positions', 3),              # Maximum 3 concurrent positions
    )
    
    def __init__(self):
        """Initialize the SMC strategy."""
        super().__init__()
        
        # Initialize indicators
        self._init_indicators()
        
        # Strategy state
        self.trend = 'neutral'  # 'bullish', 'bearish', 'neutral'
        self.last_swing_high = None
        self.last_swing_low = None
        self.order_blocks = []
        self.fair_value_gaps = []
        self.liquidity_zones = []
        
        # Performance tracking
        self.total_signals = 0
        self.successful_signals = 0
    
    def _init_indicators(self):
        """Initialize technical indicators."""
        # Volume indicators
        self.volume_sma = bt.indicators.SimpleMovingAverage(
            self.data.volume, period=self.params.lookback_period
        )
        self.volume_ratio = self.data.volume / self.volume_sma
        
        # Price indicators
        self.price_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.lookback_period
        )
        self.price_std = bt.indicators.StandardDeviation(
            self.data.close, period=self.params.lookback_period
        )
        
        # Momentum indicators
        self.rsi = bt.indicators.RSI(period=14)
        self.macd = bt.indicators.MACD()
        
        # Support/Resistance
        self.highest = bt.indicators.Highest(period=self.params.lookback_period)
        self.lowest = bt.indicators.Lowest(period=self.params.lookback_period)
    
    def generate_signals(self) -> List[Signal]:
        """
        Generate trading signals based on SMC analysis.
        
        Returns:
            List[Signal]: List of valid trading signals
        """
        signals = []
        
        # Update strategy state
        self._update_market_structure()
        self._detect_order_blocks()
        self._detect_fair_value_gaps()
        self._identify_liquidity_zones()
        
        # Generate signals based on current conditions
        if self._is_bullish_setup():
            signal = self._generate_bullish_signal()
            if signal:
                signals.append(signal)
        
        elif self._is_bearish_setup():
            signal = self._generate_bearish_signal()
            if signal:
                signals.append(signal)
        
        # Update performance tracking
        self.total_signals += len(signals)
        
        return signals
    
    def _update_market_structure(self):
        """Update market structure analysis."""
        current_price = self.data.close[0]
        current_high = self.data.high[0]
        current_low = self.data.low[0]
        
        # Update swing highs and lows
        if self.last_swing_high is None or current_high > self.last_swing_high:
            self.last_swing_high = current_high
        
        if self.last_swing_low is None or current_low < self.last_swing_low:
            self.last_swing_low = current_low
        
        # Determine trend
        if self._is_trend_confirmed('bullish'):
            self.trend = 'bullish'
        elif self._is_trend_confirmed('bearish'):
            self.trend = 'bearish'
        else:
            self.trend = 'neutral'
    
    def _is_trend_confirmed(self, direction: str) -> bool:
        """Check if trend is confirmed by price action."""
        if len(self.data) < self.params.trend_confirmation_bars:
            return False
        
        if direction == 'bullish':
            # Check if last N bars are consistently higher
            for i in range(1, self.params.trend_confirmation_bars + 1):
                if self.data.close[-i] <= self.data.close[-i-1]:
                    return False
            return True
        
        elif direction == 'bearish':
            # Check if last N bars are consistently lower
            for i in range(1, self.params.trend_confirmation_bars + 1):
                if self.data.close[-i] >= self.data.close[-i-1]:
                    return False
            return True
        
        return False
    
    def _detect_order_blocks(self):
        """Detect institutional order blocks."""
        if len(self.data) < self.params.order_block_lookback:
            return
        
        # Look for order blocks in recent bars
        for i in range(1, self.params.order_block_lookback + 1):
            bar_idx = -i
            
            # Bullish order block: strong volume + price rejection
            if (self.volume_ratio[bar_idx] > self.params.volume_threshold and
                self.data.close[bar_idx] > self.data.open[bar_idx] and
                self.data.low[bar_idx] < self.data.low[bar_idx-1]):
                
                order_block = {
                    'type': 'bullish',
                    'high': self.data.high[bar_idx],
                    'low': self.data.low[bar_idx],
                    'volume': self.data.volume[bar_idx],
                    'bar_index': bar_idx
                }
                self.order_blocks.append(order_block)
            
            # Bearish order block: strong volume + price rejection
            elif (self.volume_ratio[bar_idx] > self.params.volume_threshold and
                  self.data.close[bar_idx] < self.data.open[bar_idx] and
                  self.data.high[bar_idx] > self.data.high[bar_idx-1]):
                
                order_block = {
                    'type': 'bearish',
                    'high': self.data.high[bar_idx],
                    'low': self.data.low[bar_idx],
                    'volume': self.data.volume[bar_idx],
                    'bar_index': bar_idx
                }
                self.order_blocks.append(order_block)
        
        # Keep only recent order blocks
        max_blocks = 10
        if len(self.order_blocks) > max_blocks:
            self.order_blocks = self.order_blocks[-max_blocks:]
    
    def _detect_fair_value_gaps(self):
        """Detect fair value gaps in price action."""
        if len(self.data) < 3:
            return
        
        # Look for gaps between bars
        for i in range(2, len(self.data)):
            current_low = self.data.low[i]
            previous_high = self.data.high[i-1]
            gap_size = (current_low - previous_high) / previous_high
            
            if gap_size > self.params.fair_value_gap_threshold:
                # Bullish FVG
                fvg = {
                    'type': 'bullish',
                    'high': previous_high,
                    'low': current_low,
                    'gap_size': gap_size,
                    'bar_index': i
                }
                self.fair_value_gaps.append(fvg)
            
            current_high = self.data.high[i]
            previous_low = self.data.low[i-1]
            gap_size = (previous_low - current_high) / current_high
            
            if gap_size > self.params.fair_value_gap_threshold:
                # Bearish FVG
                fvg = {
                    'type': 'bearish',
                    'high': current_high,
                    'low': previous_low,
                    'gap_size': gap_size,
                    'bar_index': i
                }
                self.fair_value_gaps.append(fvg)
        
        # Keep only recent FVGs
        max_fvgs = 10
        if len(self.fair_value_gaps) > max_fvgs:
            self.fair_value_gaps = self.fair_value_gaps[-max_fvgs:]
    
    def _identify_liquidity_zones(self):
        """Identify liquidity zones (support/resistance levels)."""
        if len(self.data) < self.params.lookback_period:
            return
        
        current_price = self.data.close[0]
        
        # Look for recent swing highs and lows
        for i in range(1, self.params.lookback_period):
            bar_idx = -i
            
            # Swing high
            if (self.data.high[bar_idx] > self.data.high[bar_idx-1] and
                self.data.high[bar_idx] > self.data.high[bar_idx+1]):
                
                zone = {
                    'type': 'resistance',
                    'price': self.data.high[bar_idx],
                    'strength': self.data.volume[bar_idx],
                    'bar_index': bar_idx
                }
                self.liquidity_zones.append(zone)
            
            # Swing low
            if (self.data.low[bar_idx] < self.data.low[bar_idx-1] and
                self.data.low[bar_idx] < self.data.low[bar_idx+1]):
                
                zone = {
                    'type': 'support',
                    'price': self.data.low[bar_idx],
                    'strength': self.data.volume[bar_idx],
                    'bar_index': bar_idx
                }
                self.liquidity_zones.append(zone)
        
        # Keep only relevant liquidity zones
        max_zones = 20
        if len(self.liquidity_zones) > max_zones:
            self.liquidity_zones = self.liquidity_zones[-max_zones:]
    
    def _is_bullish_setup(self) -> bool:
        """Check if conditions are favorable for bullish signals."""
        if self.trend != 'bullish':
            return False
        
        # Check for bullish order blocks
        bullish_blocks = [b for b in self.order_blocks if b['type'] == 'bullish']
        if not bullish_blocks:
            return False
        
        # Check for bullish FVGs
        bullish_fvgs = [f for f in self.fair_value_gaps if f['type'] == 'bullish']
        if not bullish_fvgs:
            return False
        
        # Check RSI for oversold conditions
        if self.rsi[0] > 70:  # Overbought, not ideal for new longs
            return False
        
        # Check volume confirmation
        if self.volume_ratio[0] < 1.0:  # Below average volume
            return False
        
        return True
    
    def _is_bearish_setup(self) -> bool:
        """Check if conditions are favorable for bearish signals."""
        if self.trend != 'bearish':
            return False
        
        # Check for bearish order blocks
        bearish_blocks = [b for b in self.order_blocks if b['type'] == 'bearish']
        if not bearish_blocks:
            return False
        
        # Check for bearish FVGs
        bearish_fvgs = [f for f in self.fair_value_gaps if f['type'] == 'bearish']
        if not bearish_fvgs:
            return False
        
        # Check RSI for overbought conditions
        if self.rsi[0] < 30:  # Oversold, not ideal for new shorts
            return False
        
        # Check volume confirmation
        if self.volume_ratio[0] < 1.0:  # Below average volume
            return False
        
        return True
    
    def _generate_bullish_signal(self) -> Optional[Signal]:
        """Generate a bullish trading signal."""
        current_price = self.data.close[0]
        
        # Find nearest support level
        support_levels = [z['price'] for z in self.liquidity_zones if z['type'] == 'support']
        if not support_levels:
            return None
        
        # Use closest support below current price
        support_levels = [s for s in support_levels if s < current_price]
        if not support_levels:
            return None
        
        nearest_support = max(support_levels)
        
        # Calculate entry, stop loss, and take profit
        entry = current_price
        stop_loss = nearest_support * 0.995  # 0.5% below support
        take_profit = entry + (entry - stop_loss) * self.params.min_risk_reward
        
        # Calculate confidence based on multiple factors
        confidence = self._calculate_signal_confidence('bullish')
        
        if confidence < 0.5:
            return None
        
        return Signal(
            side='long',
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            metadata={
                'strategy': 'SMC',
                'trend': self.trend,
                'rsi': float(self.rsi[0]),
                'volume_ratio': float(self.volume_ratio[0]),
                'order_blocks': len([b for b in self.order_blocks if b['type'] == 'bullish']),
                'fair_value_gaps': len([f for f in self.fair_value_gaps if f['type'] == 'bullish'])
            }
        )
    
    def _generate_bearish_signal(self) -> Optional[Signal]:
        """Generate a bearish trading signal."""
        current_price = self.data.close[0]
        
        # Find nearest resistance level
        resistance_levels = [z['price'] for z in self.liquidity_zones if z['type'] == 'resistance']
        if not resistance_levels:
            return None
        
        # Use closest resistance above current price
        resistance_levels = [r for r in resistance_levels if r > current_price]
        if not resistance_levels:
            return None
        
        nearest_resistance = min(resistance_levels)
        
        # Calculate entry, stop loss, and take profit
        entry = current_price
        stop_loss = nearest_resistance * 1.005  # 0.5% above resistance
        take_profit = entry - (stop_loss - entry) * self.params.min_risk_reward
        
        # Calculate confidence based on multiple factors
        confidence = self._calculate_signal_confidence('bearish')
        
        if confidence < 0.5:
            return None
        
        return Signal(
            side='short',
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            metadata={
                'strategy': 'SMC',
                'trend': self.trend,
                'rsi': float(self.rsi[0]),
                'volume_ratio': float(self.volume_ratio[0]),
                'order_blocks': len([b for b in self.order_blocks if b['type'] == 'bearish']),
                'fair_value_gaps': len([f for f in self.fair_value_gaps if f['type'] == 'bearish'])
            }
        )
    
    def _calculate_signal_confidence(self, direction: str) -> float:
        """Calculate signal confidence based on multiple factors."""
        confidence = 0.5  # Base confidence
        
        # Volume factor
        if self.volume_ratio[0] > self.params.volume_threshold:
            confidence += 0.2
        
        # Trend alignment
        if self.trend == direction:
            confidence += 0.15
        
        # RSI factor
        if direction == 'bullish' and 30 < self.rsi[0] < 70:
            confidence += 0.1
        elif direction == 'bearish' and 30 < self.rsi[0] < 70:
            confidence += 0.1
        
        # Order block confirmation
        if direction == 'bullish':
            bullish_blocks = [b for b in self.order_blocks if b['type'] == 'bullish']
            if bullish_blocks:
                confidence += 0.1
        else:
            bearish_blocks = [b for b in self.order_blocks if b['type'] == 'bearish']
            if bearish_blocks:
                confidence += 0.1
        
        # Fair value gap confirmation
        if direction == 'bullish':
            bullish_fvgs = [f for f in self.fair_value_gaps if f['type'] == 'bullish']
            if bullish_fvgs:
                confidence += 0.1
        else:
            bearish_fvgs = [f for f in self.fair_value_gaps if f['type'] == 'bearish']
            if bearish_fvgs:
                confidence += 0.1
        
        # Cap confidence at 1.0
        return min(confidence, 1.0)
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get SMC-specific strategy statistics."""
        base_stats = super().get_strategy_stats()
        
        # Add SMC-specific stats
        smc_stats = {
            'trend': self.trend,
            'order_blocks_count': len(self.order_blocks),
            'fair_value_gaps_count': len(self.fair_value_gaps),
            'liquidity_zones_count': len(self.liquidity_zones),
            'last_swing_high': self.last_swing_high,
            'last_swing_low': self.last_swing_low,
            'current_rsi': float(self.rsi[0]) if len(self.rsi) > 0 else None,
            'current_volume_ratio': float(self.volume_ratio[0]) if len(self.volume_ratio) > 0 else None,
        }
        
        base_stats.update(smc_stats)
        return base_stats
    
    def stop(self):
        """Called when the strategy stops."""
        super().stop()
        
        # Log SMC-specific information
        print(f"SMC Strategy Statistics:")
        print(f"  Market Trend: {self.trend}")
        print(f"  Order Blocks Detected: {len(self.order_blocks)}")
        print(f"  Fair Value Gaps: {len(self.fair_value_gaps)}")
        print(f"  Liquidity Zones: {len(self.liquidity_zones)}")
        print(f"  Last Swing High: {self.last_swing_high}")
        print(f"  Last Swing Low: {self.last_swing_low}")


# Strategy can be manually registered if needed
# from .registry import register_strategy
# register_strategy('SMC', SMCStrategy, __file__, SMCStrategy.version)
