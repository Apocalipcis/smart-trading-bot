
"""
Signal-Only Smart Money Concepts (SMC) Strategy

This strategy implements Smart Money Concepts trading methodology,
focusing on institutional order flow, liquidity zones, and market structure.
It generates trading signals but does NOT auto-manage stops or move them to breakeven.
The trader manually decides how to manage trades after entry.

Features:
- Multi-timeframe analysis (HTF bias + LTF entries)
- Order Block, FVG, and Liquidity Pool detection
- Liquidity sweep and BoS/ChoCH confirmation
- Configurable indicator filters
- Fixed risk management (no auto-adjustment)
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
import backtrader as bt

try:
    from src.strategies.base import BaseStrategy, Signal
except ImportError:
    from .base import BaseStrategy, Signal


def handle_errors(func):
    """Error handling decorator to reduce repetitive try-catch blocks."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"SMC Strategy Error in {func.__name__}: {e}")
            return None if func.__name__.startswith('detect_') else [] if func.__name__.startswith('_get_') else False
    return wrapper


class SMCSignalStrategy(BaseStrategy):
    """
    Signal-Only Smart Money Concepts Strategy.
    
    Generates entry signals with fixed stop-loss and take-profit levels.
    Does NOT auto-manage stops or move them to breakeven.
    Trader manually manages trades after entry.
    """
    
    version = "1.0.0"
    
    params = (
        # Timeframe Configuration
        ('htf_timeframe', '4H'),           # Higher timeframe (1D/4H)
        ('ltf_timeframe', '15m'),          # Lower timeframe (15M)
        ('scalping_mode', False),          # Enable M1-M5 scalping
        
        # SMC Detection
        ('volume_ratio_threshold', 1.5),   # Volume expansion threshold
        ('fvg_min_pct', 0.5),             # Minimum FVG gap (0.5%)
        ('ob_lookback_bars', 20),         # Bars to look back for OBs
        ('swing_threshold', 0.02),         # Minimum swing size (2%)
        
        # Risk Management
        ('risk_per_trade', 0.01),          # 1% risk per trade
        ('min_risk_reward', 3.0),          # Minimum 3:1 R:R
        ('max_positions', 3),              # Max concurrent positions
        ('sl_buffer_atr', 0.15),           # SL buffer in ATR multiples
        
        # Indicator Filters
        ('use_rsi', True),                 # Enable RSI filter
        ('use_obv', True),                 # Enable OBV filter
        ('use_bbands', False),             # Enable Bollinger Bands filter
        ('rsi_overbought', 70),            # RSI overbought threshold
        ('rsi_oversold', 30),              # RSI oversold threshold
    )
    
    required_roles = ['HTF', 'LTF']
    
    role_constraints = [
        {
            'role': 'HTF',
            'min_timeframe': '1h',
            'max_timeframe': '1d',
            'description': 'Higher timeframe for bias and key zones'
        },
        {
            'role': 'LTF',
            'min_timeframe': '1m',
            'max_timeframe': '30m',
            'description': 'Lower timeframe for entry timing'
        }
    ]
    
    def __init__(self):
        """Initialize the SMC Signal Strategy."""
        super().__init__()
        self._init_indicators()
        
        # HTF State
        self.htf_trend = 'neutral'
        self.htf_order_blocks = []
        self.htf_fair_value_gaps = []
        self.htf_liquidity_pools = []
        
        # LTF State
        self.ltf_swings = []
        self.ltf_bos_events = []
        self.ltf_liquidity_sweeps = []
        
        # Performance tracking
        self.total_signals = 0
        self.successful_signals = 0
        
        if not self.validate_multi_timeframe_setup():
            raise ValueError("Invalid multi-timeframe setup. Need HTF and LTF data feeds.")
    
    def _init_indicators(self):
        """Initialize technical indicators for both HTF and LTF."""
        htf_data = self.get_htf_data()
        ltf_data = self.get_ltf_data()
        
        if htf_data is None or ltf_data is None:
            raise ValueError("HTF and LTF data feeds not available")
        
        # HTF Indicators
        self.htf_ema_50 = bt.indicators.ExponentialMovingAverage(htf_data.close, period=50)
        self.htf_volume_sma = bt.indicators.SimpleMovingAverage(htf_data.volume, period=20)
        self.htf_atr = bt.indicators.ATR(htf_data, period=14)
        
        # LTF Indicators
        self.ltf_rsi = bt.indicators.RSI(ltf_data.close, period=14)
        self.ltf_volume_sma = bt.indicators.SimpleMovingAverage(ltf_data.volume, period=20)
        self.ltf_atr = bt.indicators.ATR(ltf_data, period=14)
        
        # Optional Bollinger Bands
        if self.params.use_bbands:
            self.ltf_bbands = bt.indicators.BollingerBands(ltf_data.close, period=20, devfactor=2)
    
    def _convert_to_dataframe(self, data_feed, max_bars=500) -> pd.DataFrame:
        """Convert backtrader data to pandas DataFrame."""
        if not data_feed or len(data_feed) == 0:
            return pd.DataFrame()
        
        available_bars = min(len(data_feed), max_bars)
        data = []
        
        for i in range(available_bars):
            try:
                data.append({
                    'timestamp': data_feed.datetime.datetime(i),
                    'open': float(data_feed.open[i]),
                    'high': float(data_feed.high[i]),
                    'low': float(data_feed.low[i]),
                    'close': float(data_feed.close[i]),
                    'volume': float(data_feed.volume[i])
                })
            except (IndexError, ValueError, TypeError):
                continue
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    @handle_errors
    def detect_market_bias_htf(self) -> str:
        """Detect market bias using HTF structure and EMA."""
        htf_data = self.get_htf_data()
        if not htf_data or len(htf_data) < 50 or len(self.htf_ema_50) == 0:
            return 'neutral'
        
        current_price = htf_data.close[0]
        ema_50 = self.htf_ema_50[0]
        return 'bullish' if current_price > ema_50 else 'bearish'
    
    @handle_errors
    def detect_order_blocks_htf(self) -> List[Dict]:
        """Detect order blocks on HTF."""
        df = self._convert_to_dataframe(self.get_htf_data(), 100)
        if df.empty or len(df) < 5:
            return []
        
        obs = []
        lookback = min(self.params.ob_lookback_bars, len(df) - 1)
        
        for i in range(lookback, len(df) - 1):
            try:
                current_bar = df.iloc[i]
                next_bar = df.iloc[i + 1]
                
                # Calculate volume ratio
                avg_volume = df['volume'].rolling(20).mean().iloc[i]
                volume_ratio = current_bar['volume'] / avg_volume if avg_volume > 0 else 1.0
                
                # Check for bullish order block
                if (current_bar['close'] < current_bar['open'] and
                    next_bar['close'] > next_bar['open'] and
                    next_bar['close'] > current_bar['high'] and
                    volume_ratio > self.params.volume_ratio_threshold):
                    
                    obs.append({
                        'id': f"OB_bull_{i}",
                        'type': 'bullish',
                        'start_idx': i, 'end_idx': i,
                        'open': float(current_bar['open']), 'high': float(current_bar['high']),
                        'low': float(current_bar['low']), 'close': float(current_bar['close']),
                        'volume_ratio': volume_ratio, 'timestamp': current_bar.name
                    })
                
                # Check for bearish order block
                elif (current_bar['close'] > current_bar['open'] and
                      next_bar['close'] < next_bar['open'] and
                      next_bar['close'] < current_bar['low'] and
                      volume_ratio > self.params.volume_ratio_threshold):
                    
                    obs.append({
                        'id': f"OB_bear_{i}",
                        'type': 'bearish',
                        'start_idx': i, 'end_idx': i,
                        'open': float(current_bar['open']), 'high': float(current_bar['high']),
                        'low': float(current_bar['low']), 'close': float(current_bar['close']),
                        'volume_ratio': volume_ratio, 'timestamp': current_bar.name
                    })
                    
            except Exception:
                continue
        
        return obs
    
    @handle_errors
    def detect_fair_value_gaps_htf(self) -> List[Dict]:
        """Detect fair value gaps on HTF."""
        df = self._convert_to_dataframe(self.get_htf_data(), 100)
        if df.empty or len(df) < 3:
            return []
        
        fvgs = []
        min_gap_pct = self.params.fvg_min_pct / 100
        
        for i in range(2, len(df)):
            try:
                current_bar = df.iloc[i]
                prev_prev_bar = df.iloc[i-2]
                
                # Bullish FVG: gap up
                if current_bar['low'] > prev_prev_bar['high']:
                    gap_size = (current_bar['low'] - prev_prev_bar['high']) / prev_prev_bar['high']
                    if gap_size >= min_gap_pct:
                        fvgs.append({
                            'id': f"FVG_bull_{i}", 'type': 'bullish',
                            'start_idx': i-2, 'end_idx': i,
                            'top': float(current_bar['low']), 'bottom': float(prev_prev_bar['high']),
                            'gap_size_pct': gap_size * 100, 'timestamp': current_bar.name
                        })
                
                # Bearish FVG: gap down
                elif current_bar['high'] < prev_prev_bar['low']:
                    gap_size = (prev_prev_bar['low'] - current_bar['high']) / current_bar['high']
                    if gap_size >= min_gap_pct:
                        fvgs.append({
                            'id': f"FVG_bear_{i}", 'type': 'bearish',
                            'start_idx': i-2, 'end_idx': i,
                            'top': float(prev_prev_bar['low']), 'bottom': float(current_bar['high']),
                            'gap_size_pct': gap_size * 100, 'timestamp': current_bar.name
                        })
                        
            except Exception:
                continue
        
        return fvgs
    
    @handle_errors
    def detect_liquidity_pools_htf(self) -> List[Dict]:
        """Detect liquidity pools (swing highs/lows) on HTF."""
        df = self._convert_to_dataframe(self.get_htf_data(), 100)
        if df.empty or len(df) < 5:
            return []
        
        pools = []
        swing_threshold = self.params.swing_threshold
        
        for i in range(2, len(df) - 2):
            try:
                current_bar = df.iloc[i]
                start_idx, end_idx = max(0, i-2), min(len(df), i+3)
                slice_data = df.iloc[start_idx:end_idx]
                
                # Swing high
                if (current_bar['high'] == slice_data['high'].max() and
                    current_bar['high'] > slice_data['low'].min() * (1 + swing_threshold)):
                    pools.append({
                        'id': f"LP_high_{i}", 'type': 'high', 'idx': i,
                        'price': float(current_bar['high']), 'timestamp': current_bar.name
                    })
                
                # Swing low
                if (current_bar['low'] == slice_data['low'].min() and
                    current_bar['low'] < slice_data['high'].max() * (1 - swing_threshold)):
                    pools.append({
                        'id': f"LP_low_{i}", 'type': 'low', 'idx': i,
                        'price': float(current_bar['low']), 'timestamp': current_bar.name
                    })
                    
            except Exception:
                continue
        
        return pools
    
    @handle_errors
    def detect_liquidity_sweep_ltf(self) -> bool:
        """Detect liquidity sweep on LTF."""
        df = self._convert_to_dataframe(self.get_ltf_data(), 100)
        if df.empty or len(df) < 3 or len(self.ltf_swings) == 0:
            return False
        
        current_bar = df.iloc[-1]
        last_swing = self.ltf_swings[-1]
        
        if last_swing['type'] == 'low':
            return (current_bar['low'] < last_swing['price'] and 
                   current_bar['close'] > last_swing['price'])
        elif last_swing['type'] == 'high':
            return (current_bar['high'] > last_swing['price'] and 
                   current_bar['close'] < last_swing['price'])
        
        return False
    
    @handle_errors
    def detect_bos_ltf(self, direction: str) -> bool:
        """Detect Break of Structure on LTF."""
        df = self._convert_to_dataframe(self.get_ltf_data(), 100)
        if df.empty or len(df) < 3 or len(self.ltf_swings) < 2:
            return False
        
        current_bar = df.iloc[-1]
        
        if direction == 'bullish':
            recent_highs = [s for s in self.ltf_swings if s['type'] == 'high']
            return recent_highs and current_bar['close'] > recent_highs[-1]['price']
        elif direction == 'bearish':
            recent_lows = [s for s in self.ltf_swings if s['type'] == 'low']
            return recent_lows and current_bar['close'] < recent_lows[-1]['price']
        
        return False
    
    def _check_filters(self, direction: str) -> Tuple[bool, List[str]]:
        """Check all filters and return (passed, passed_filters_list)."""
        passed_filters = []
        
        # RSI filter
        if self.params.use_rsi and len(self.ltf_rsi) > 0:
            current_rsi = self.ltf_rsi[0]
            if direction == 'long' and current_rsi <= self.params.rsi_overbought:
                passed_filters.append('rsi')
            elif direction == 'short' and current_rsi >= self.params.rsi_oversold:
                passed_filters.append('rsi')
        else:
            passed_filters.append('rsi')
        
        # Volume filter
        if len(self.ltf_volume_sma) > 0:
            current_volume = self.get_ltf_data().volume[0]
            avg_volume = self.ltf_volume_sma[0]
            if avg_volume > 0 and current_volume / avg_volume >= 1.0:
                passed_filters.append('volume')
        else:
            passed_filters.append('volume')
        
        # OBV filter (temporarily disabled)
        if self.params.use_obv:
            passed_filters.append('obv')
        
        # Bollinger Bands filter
        if self.params.use_bbands and len(self.ltf_bbands) > 0:
            current_price = self.get_ltf_data().close[0]
            upper_band = self.ltf_bbands.lines.top[0]
            lower_band = self.ltf_bbands.lines.bot[0]
            if lower_band <= current_price <= upper_band:
                passed_filters.append('bbands')
        else:
            passed_filters.append('bbands')
        
        passed = len(passed_filters) >= 3  # At least 3 filters must pass
        return passed, passed_filters
    
    def _calculate_signal_confidence(self, direction: str, passed_filters: List[str]) -> float:
        """Calculate signal confidence based on multiple factors."""
        confidence = 0.5  # Base confidence
        
        # Filter contributions
        confidence += len(passed_filters) * 0.1
        
        # HTF trend alignment
        if direction == 'long' and self.htf_trend == 'bullish':
            confidence += 0.1
        elif direction == 'short' and self.htf_trend == 'bearish':
            confidence += 0.1
        
        # SMC confirmations
        if self.detect_liquidity_sweep_ltf():
            confidence += 0.1
        if self.detect_bos_ltf(direction):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _compute_sl_tp(self, entry: float, direction: str, ob: Dict) -> Tuple[float, float]:
        """Compute stop loss and take profit levels."""
        try:
            atr = self.ltf_atr[0] if len(self.ltf_atr) > 0 else 0.01
            buffer = atr * self.params.sl_buffer_atr
            
            if direction == 'long':
                stop_loss = ob['low'] - buffer
                risk = entry - stop_loss
                take_profit = entry + (risk * self.params.min_risk_reward)
            else:
                stop_loss = ob['high'] + buffer
                risk = stop_loss - entry
                take_profit = entry - (risk * self.params.min_risk_reward)
            
            return stop_loss, take_profit
        except Exception:
            # Fallback values
            return (entry * 0.99, entry * 1.03) if direction == 'long' else (entry * 1.01, entry * 0.97)
    
    def _generate_signal(self, direction: str) -> Optional[Signal]:
        """Generate a trading signal for the given direction."""
        # Find matching order blocks
        obs = [ob for ob in self.htf_order_blocks if ob['type'] == direction]
        if not obs:
            return None
        
        ob = obs[-1]  # Use most recent
        current_price = self.get_ltf_data().close[0]
        
        # Check if price is near the order block
        ob_mid = (ob['high'] + ob['low']) / 2
        if abs(current_price - ob_mid) / ob_mid > 0.02:
            return None
        
        # Check filters
        filters_passed, passed_filters = self._check_filters(direction)
        if not filters_passed:
            return None
        
        # Calculate entry, stop loss, and take profit
        entry = current_price
        stop_loss, take_profit = self._compute_sl_tp(entry, direction, ob)
        
        # Calculate confidence
        confidence = self._calculate_signal_confidence(direction, passed_filters)
        if confidence < 0.5:
            return None
        
        # Generate metadata
        metadata = {
            'strategy': 'SMCSignalStrategy',
            'htf_trend': self.htf_trend,
            'matched_ob_id': ob['id'],
            'liquidity_sweep': self.detect_liquidity_sweep_ltf(),
            'bos_confirmation': self.detect_bos_ltf(direction),
            'filters_passed': passed_filters,
            'htf_zone_type': 'OrderBlock'
        }
        
        return Signal(
            side='long' if direction == 'bullish' else 'short',
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            metadata=metadata
        )
    
    def generate_signals(self) -> List[Signal]:
        """Generate trading signals based on SMC analysis."""
        signals = []
        
        # Validate data feeds
        htf_data = self.get_htf_data()
        ltf_data = self.get_ltf_data()
        
        if (htf_data is None or ltf_data is None or 
            len(htf_data) < 50 or len(ltf_data) < 20 or
            len(self.htf_ema_50) == 0 or len(self.ltf_rsi) == 0):
            return signals
        
        # Update HTF state
        try:
            self.htf_trend = self.detect_market_bias_htf()
            self.htf_order_blocks = self.detect_order_blocks_htf()
            self.htf_fair_value_gaps = self.detect_fair_value_gaps_htf()
            self.htf_liquidity_pools = self.detect_liquidity_pools_htf()
        except Exception as e:
            print(f"SMC Strategy Error updating HTF state: {e}")
            return signals
        
        # Generate signals based on current conditions
        if self.htf_trend == 'bullish' and self.htf_order_blocks:
            signal = self._generate_signal('bullish')
            if signal:
                signals.append(signal)
                print(f"SMC Strategy: Generated BULLISH signal - Entry: {signal.entry:.2f}, SL: {signal.stop_loss:.2f}, TP: {signal.take_profit:.2f}, Confidence: {signal.confidence:.2f}")
        
        elif self.htf_trend == 'bearish' and self.htf_order_blocks:
            signal = self._generate_signal('bearish')
            if signal:
                signals.append(signal)
                print(f"SMC Strategy: Generated BEARISH signal - Entry: {signal.entry:.2f}, SL: {signal.stop_loss:.2f}, TP: {signal.take_profit:.2f}, Confidence: {signal.confidence:.2f}")
        
        self.total_signals += len(signals)
        return signals
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get SMC-specific strategy statistics."""
        try:
            base_stats = super().get_strategy_stats()
            smc_stats = {
                'htf_trend': self.htf_trend,
                'htf_order_blocks_count': len(self.htf_order_blocks),
                'htf_fair_value_gaps_count': len(self.htf_fair_value_gaps),
                'htf_liquidity_pools_count': len(self.htf_liquidity_pools),
                'ltf_swings_count': len(self.ltf_swings),
                'ltf_bos_events_count': len(self.ltf_bos_events),
                'ltf_liquidity_sweeps_count': len(self.ltf_liquidity_sweeps),
                'current_rsi': float(self.ltf_rsi[0]) if len(self.ltf_rsi) > 0 else None,
                'current_volume_ratio': float(self.get_ltf_data().volume[0] / self.ltf_volume_sma[0]) if len(self.ltf_volume_sma) > 0 else None,
            }
            base_stats.update(smc_stats)
            return base_stats
        except Exception:
            return {}
    
    def stop(self):
        """Called when the strategy stops."""
        try:
            super().stop()
            print(f"SMC Strategy Statistics:")
            print(f"  HTF Market Trend: {self.htf_trend}")
            print(f"  HTF Order Blocks: {len(self.htf_order_blocks)}")
            print(f"  HTF Fair Value Gaps: {len(self.htf_fair_value_gaps)}")
            print(f"  HTF Liquidity Pools: {len(self.htf_liquidity_pools)}")
            print(f"  Total Signals Generated: {self.total_signals}")
        except Exception:
            pass
