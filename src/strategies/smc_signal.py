
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
    from src.strategies.smc_config import SMCStrategyConfig, load_config_from_dict
except ImportError:
    from .base import BaseStrategy, Signal
    from .smc_config import SMCStrategyConfig, load_config_from_dict


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
        
        # Configuration System
        ('indicators_config', {}),         # Indicators configuration
        ('filters_config', {}),            # Filters configuration
        ('smc_config', {}),                # SMC elements configuration
        ('risk_config', {}),               # Risk management configuration
        
        # Legacy Parameters (for backward compatibility)
        ('volume_ratio_threshold', 1.5),   # Volume expansion threshold
        ('fvg_min_pct', 0.5),             # Minimum FVG gap (0.5%)
        ('ob_lookback_bars', 20),         # Bars to look back for OBs
        ('swing_threshold', 0.02),         # Minimum swing size (2%)
        ('risk_per_trade', 0.01),          # 1% risk per trade
        ('min_risk_reward', 3.0),          # Minimum 3:1 R:R
        ('max_positions', 3),              # Max concurrent positions
        ('sl_buffer_atr', 0.15),           # SL buffer in ATR multiples
        ('use_rsi', True),                 # Enable RSI filter
        ('use_obv', True),                 # Enable OBV filter
        ('use_bbands', False),             # Enable Bollinger Bands filter
        ('rsi_overbought', 70),            # RSI overbought threshold
        ('rsi_oversold', 30),              # RSI oversold threshold
        ('quiet_mode', False),             # Suppress processing logs
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
        
        # Load configuration
        self._load_configuration()
        
        # Initialize indicators based on configuration
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
        self.last_signal_bar = 0  # Track last signal generation
        self.min_bars_between_signals = 25  # Minimum bars between signals (increased)
        
        if not self.validate_multi_timeframe_setup():
            raise ValueError("Invalid multi-timeframe setup. Need HTF and LTF data feeds.")
    
    def _load_configuration(self):
        """Load and validate configuration."""
        # Try to load from configuration parameters first
        if self.params.indicators_config and self.params.filters_config:
            self.config = load_config_from_dict({
                'indicators': self.params.indicators_config,
                'filters': self.params.filters_config,
                'smc_elements': self.params.smc_config,
                'risk_management': self.params.risk_config
            })
        else:
            # Use default configuration
            self.config = SMCStrategyConfig.get_default_config()
        
        # Override with legacy parameters if provided
        self._apply_legacy_parameters()
    
    def _apply_legacy_parameters(self):
        """Apply legacy parameters to configuration for backward compatibility."""
        # Override indicators if legacy params are set
        if hasattr(self.params, 'use_rsi') and self.params.use_rsi:
            self.config.indicators.rsi.enabled = True
            if hasattr(self.params, 'rsi_overbought'):
                self.config.indicators.rsi.overbought = self.params.rsi_overbought
            if hasattr(self.params, 'rsi_oversold'):
                self.config.indicators.rsi.oversold = self.params.rsi_oversold
        
        if hasattr(self.params, 'use_bbands') and self.params.use_bbands:
            self.config.indicators.bbands.enabled = True
        
        # Override risk management if legacy params are set
        if hasattr(self.params, 'risk_per_trade'):
            self.config.risk_management.risk_per_trade = self.params.risk_per_trade
        if hasattr(self.params, 'min_risk_reward'):
            self.config.risk_management.min_risk_reward = self.params.min_risk_reward
        if hasattr(self.params, 'max_positions'):
            self.config.risk_management.max_positions = self.params.max_positions
        if hasattr(self.params, 'sl_buffer_atr'):
            self.config.risk_management.sl_buffer_atr = self.params.sl_buffer_atr
    
    def _init_indicators(self):
        """Initialize technical indicators based on configuration."""
        htf_data = self.get_htf_data()
        ltf_data = self.get_ltf_data()
        
        if htf_data is None or ltf_data is None:
            raise ValueError("HTF and LTF data feeds not available")
        
        # HTF Indicators (always enabled)
        self.htf_ema_50 = bt.indicators.ExponentialMovingAverage(htf_data.close, period=50)
        self.htf_volume_sma = bt.indicators.SimpleMovingAverage(htf_data.volume, period=20)
        self.htf_atr = bt.indicators.ATR(htf_data, period=14)
        
        # LTF Indicators - based on configuration
        indicators_config = self.config.indicators
        
        # RSI
        if indicators_config.rsi.enabled:
            self.ltf_rsi = bt.indicators.RSI(ltf_data.close, period=indicators_config.rsi.period)
        else:
            self.ltf_rsi = None
        
        # MACD
        if indicators_config.macd.enabled:
            self.ltf_macd = bt.indicators.MACD(
                ltf_data.close,
                period_me1=indicators_config.macd.fast_period,
                period_me2=indicators_config.macd.slow_period,
                period_signal=indicators_config.macd.signal_period
            )
        else:
            self.ltf_macd = None
        
        # Bollinger Bands
        if indicators_config.bbands.enabled:
            self.ltf_bbands = bt.indicators.BollingerBands(
                ltf_data.close, 
                period=indicators_config.bbands.period, 
                devfactor=indicators_config.bbands.deviation
            )
        else:
            self.ltf_bbands = None
        
        # Stochastic
        if indicators_config.stochastic.enabled:
            self.ltf_stochastic = bt.indicators.Stochastic(
                ltf_data,
                period=indicators_config.stochastic.k_period,
                period_d=indicators_config.stochastic.d_period
            )
        else:
            self.ltf_stochastic = None
        
        # Volume SMA
        if indicators_config.volume.enabled:
            self.ltf_volume_sma = bt.indicators.SimpleMovingAverage(
                ltf_data.volume, 
                period=indicators_config.volume.period
            )
        else:
            self.ltf_volume_sma = None
        
        # ATR
        if indicators_config.atr.enabled:
            self.ltf_atr = bt.indicators.ATR(ltf_data, period=indicators_config.atr.period)
        else:
            self.ltf_atr = None
    
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
        # Check if order blocks are enabled in configuration
        if not self.config.smc_elements.order_blocks.enabled:
            return []
        
        df = self._convert_to_dataframe(self.get_htf_data(), 100)
        if df.empty or len(df) < 5:
            return []
        
        obs = []
        config = self.config.smc_elements.order_blocks
        lookback = min(config.lookback_bars, len(df) - 1)
        volume_threshold = config.volume_threshold
        
        for i in range(lookback, len(df) - 1):
            try:
                current_bar = df.iloc[i]
                next_bar = df.iloc[i + 1]
                
                # Calculate volume ratio
                avg_volume = df['volume'].rolling(20).mean().iloc[i]
                volume_ratio = current_bar['volume'] / avg_volume if avg_volume > 0 else 1.0
                
                # Check for bullish order block (bearish candle followed by bullish move)
                if (current_bar['close'] < current_bar['open'] and  # Bearish candle
                    next_bar['close'] > next_bar['open'] and      # Next candle bullish
                    next_bar['close'] > current_bar['high'] and   # Break above high
                    volume_ratio > volume_threshold):
                    
                    obs.append({
                        'id': f"OB_bull_{i}",
                        'type': 'bullish',
                        'start_idx': i, 'end_idx': i,
                        'open': float(current_bar['open']), 'high': float(current_bar['high']),
                        'low': float(current_bar['low']), 'close': float(current_bar['close']),
                        'volume_ratio': volume_ratio, 'timestamp': current_bar.name
                    })
                
                # Check for bearish order block (bullish candle followed by bearish move)
                elif (current_bar['close'] > current_bar['open'] and  # Bullish candle
                      next_bar['close'] < next_bar['open'] and      # Next candle bearish
                      next_bar['close'] < current_bar['low'] and    # Break below low
                      volume_ratio > volume_threshold):
                    
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
        # Check if fair value gaps are enabled in configuration
        if not self.config.smc_elements.fair_value_gaps.enabled:
            return []
        
        df = self._convert_to_dataframe(self.get_htf_data(), 100)
        if df.empty or len(df) < 3:
            return []
        
        fvgs = []
        config = self.config.smc_elements.fair_value_gaps
        min_gap_pct = config.min_gap_pct / 100
        
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
        # Check if liquidity pools are enabled in configuration
        if not self.config.smc_elements.liquidity_pools.enabled:
            return []
        
        df = self._convert_to_dataframe(self.get_htf_data(), 100)
        if df.empty or len(df) < 5:
            return []
        
        pools = []
        config = self.config.smc_elements.liquidity_pools
        swing_threshold = config.swing_threshold
        
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
        """Check all filters based on configuration and return (passed, passed_filters_list)."""
        passed_filters = []
        filters_config = self.config.filters
        
        # RSI filter
        if filters_config.rsi.enabled and self.ltf_rsi is not None and len(self.ltf_rsi) > 0:
            if self._check_rsi_filter(direction, filters_config.rsi):
                passed_filters.append('rsi')
        
        # Volume filter
        if filters_config.volume.enabled and self.ltf_volume_sma is not None and len(self.ltf_volume_sma) > 0:
            if self._check_volume_filter(filters_config.volume):
                passed_filters.append('volume')
        
        # Bollinger Bands filter
        if filters_config.bbands.enabled and self.ltf_bbands is not None and len(self.ltf_bbands) > 0:
            if self._check_bbands_filter(filters_config.bbands):
                passed_filters.append('bbands')
        
        # MACD filter
        if filters_config.macd.enabled and self.ltf_macd is not None and len(self.ltf_macd) > 0:
            if self._check_macd_filter(direction, filters_config.macd):
                passed_filters.append('macd')
        
        # Stochastic filter
        if filters_config.stochastic.enabled and self.ltf_stochastic is not None and len(self.ltf_stochastic) > 0:
            if self._check_stochastic_filter(direction, filters_config.stochastic):
                passed_filters.append('stochastic')
        
        # Check if we have enough filters passing
        min_filters = filters_config.min_filters_required
        passed = len(passed_filters) >= min_filters
        return passed, passed_filters
    
    def _check_rsi_filter(self, direction: str, config) -> bool:
        """Check RSI filter based on configuration."""
        if self.ltf_rsi is None or len(self.ltf_rsi) == 0:
            return False
        
        current_rsi = self.ltf_rsi[0]
        
        if direction == 'bullish':
            return current_rsi <= config.overbought
        elif direction == 'bearish':
            return current_rsi >= config.oversold
        
        return False
    
    def _check_volume_filter(self, config) -> bool:
        """Check volume filter based on configuration."""
        if self.ltf_volume_sma is None or len(self.ltf_volume_sma) == 0:
            return False
        
        try:
            current_volume = self.get_ltf_data().volume[0]
            avg_volume = self.ltf_volume_sma[0]
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                return volume_ratio >= config.min_volume_ratio
        except:
            pass
        
        return False
    
    def _check_bbands_filter(self, config) -> bool:
        """Check Bollinger Bands filter based on configuration."""
        if self.ltf_bbands is None or len(self.ltf_bbands) == 0:
            return False
        
        try:
            current_price = self.get_ltf_data().close[0]
            bb_upper = self.ltf_bbands.lines.top[0]
            bb_lower = self.ltf_bbands.lines.bot[0]
            
            # Check if price is within the bands
            if bb_upper > bb_lower:
                position = (current_price - bb_lower) / (bb_upper - bb_lower)
                return position >= config.position_threshold
        except:
            pass
        
        return False
    
    def _check_macd_filter(self, direction: str, config) -> bool:
        """Check MACD filter based on configuration."""
        if self.ltf_macd is None or len(self.ltf_macd) == 0:
            return False
        
        try:
            macd_line = self.ltf_macd.lines.macd[0]
            signal_line = self.ltf_macd.lines.signal[0]
            
            if config.signal_cross:
                # Check for MACD crossing above/below signal line
                if direction == 'bullish':
                    return macd_line > signal_line
                elif direction == 'bearish':
                    return macd_line < signal_line
            
            return True
        except:
            pass
        
        return False
    
    def _check_stochastic_filter(self, direction: str, config) -> bool:
        """Check Stochastic filter based on configuration."""
        if self.ltf_stochastic is None or len(self.ltf_stochastic) == 0:
            return False
        
        try:
            k_line = self.ltf_stochastic.lines.percK[0]
            
            if direction == 'bullish':
                return k_line <= config.oversold
            elif direction == 'bearish':
                return k_line >= config.overbought
            
            return True
        except:
            pass
        
        return False
    
    def _calculate_signal_confidence(self, direction: str, passed_filters: List[str]) -> float:
        """Calculate signal confidence based on multiple factors."""
        confidence = 0.3  # Lower base confidence
        
        # Filter contributions (more weight)
        confidence += len(passed_filters) * 0.15
        
        # HTF trend alignment (more weight)
        if direction == 'bullish' and self.htf_trend == 'bullish':
            confidence += 0.2
        elif direction == 'bearish' and self.htf_trend == 'bearish':
            confidence += 0.2
        
        # SMC confirmations (more weight)
        if self.detect_liquidity_sweep_ltf():
            confidence += 0.15
        if self.detect_bos_ltf(direction):
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _compute_sl_tp(self, entry: float, direction: str, ob: Dict) -> Tuple[float, float]:
        """Compute stop loss and take profit levels."""
        try:
            risk_config = self.config.risk_management
            
            if self.ltf_atr is not None and len(self.ltf_atr) > 0:
                atr = self.ltf_atr[0]
                buffer = atr * risk_config.sl_buffer_atr
            else:
                # Fallback to percentage-based buffer
                buffer = entry * 0.02  # 2% buffer
            
            if direction == 'bullish':
                stop_loss = ob['low'] - buffer
                risk = entry - stop_loss
                take_profit = entry + (risk * risk_config.min_risk_reward)
            else:  # bearish
                stop_loss = ob['high'] + buffer
                risk = stop_loss - entry
                take_profit = entry - (risk * risk_config.min_risk_reward)
            
            return stop_loss, take_profit
        except Exception:
            # Fallback values
            return (entry * 0.99, entry * 1.03) if direction == 'bullish' else (entry * 1.01, entry * 0.97)
    
    def _generate_signal(self, direction: str) -> Optional[Signal]:
        """Generate a trading signal for the given direction."""
        current_price = self.get_ltf_data().close[0]
        
        # Try to find matching order blocks first
        obs = [ob for ob in self.htf_order_blocks if ob['type'] == direction]
        
        if obs:
            # Use order block if available
            ob = obs[-1]  # Use most recent
            
            # Check if price is near the order block
            ob_mid = (ob['high'] + ob['low']) / 2
            if abs(current_price - ob_mid) / ob_mid > 0.03:  # Increased tolerance
                return None
            
            # Calculate entry, stop loss, and take profit
            entry = current_price
            stop_loss, take_profit = self._compute_sl_tp(entry, direction, ob)
            zone_type = 'OrderBlock'
            ob_id = ob['id']
        else:
            # Fallback: create signal without order block
            entry = current_price
            risk_config = self.config.risk_management
            
            if self.ltf_atr is not None and len(self.ltf_atr) > 0:
                atr = self.ltf_atr[0]
                buffer = atr * risk_config.sl_buffer_atr
            else:
                buffer = current_price * 0.02  # 2% buffer
            
            if direction == 'bullish':
                stop_loss = entry - buffer
                risk = buffer
                take_profit = entry + (risk * risk_config.min_risk_reward)
            else:  # bearish
                stop_loss = entry + buffer
                risk = buffer
                take_profit = entry - (risk * risk_config.min_risk_reward)
            
            zone_type = 'PriceAction'
            ob_id = 'PA_fallback'
        
        # Check filters
        filters_passed, passed_filters = self._check_filters(direction)
        if not filters_passed:
            return None
        
        # Calculate confidence
        confidence = self._calculate_signal_confidence(direction, passed_filters)
        min_confidence = self.config.filters.min_filters_required * 0.1  # Dynamic minimum confidence
        if confidence < min_confidence:
            return None
        
        # Generate metadata
        metadata = {
            'strategy': 'SMCSignalStrategy',
            'htf_trend': self.htf_trend,
            'matched_ob_id': ob_id,
            'liquidity_sweep': self.detect_liquidity_sweep_ltf(),
            'bos_confirmation': self.detect_bos_ltf(direction),
            'filters_passed': passed_filters,
            'htf_zone_type': zone_type
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
            len(self.htf_ema_50) == 0):
            return signals
        
        # Check signal frequency - don't generate signals too often
        current_bar = len(ltf_data)
        if current_bar - self.last_signal_bar < self.min_bars_between_signals:
            return signals
        
        # Check if we have at least one enabled indicator
        if (self.ltf_rsi is None and self.ltf_macd is None and 
            self.ltf_bbands is None and self.ltf_stochastic is None):
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
        
        # Generate signals based on current conditions - more selective
        if self.htf_trend == 'bullish':
            signal = self._generate_signal('bullish')
            if signal and signal.confidence >= 0.8:  # Only very high confidence signals
                signals.append(signal)
        
        elif self.htf_trend == 'bearish':
            signal = self._generate_signal('bearish')
            if signal and signal.confidence >= 0.8:  # Only very high confidence signals
                signals.append(signal)
        
        # Fallback: generate signals only for extremely high quality setups
        if not signals and len(self.htf_order_blocks) > 0:
            # Try to generate signals based on order blocks, but only extremely high confidence ones
            for ob in self.htf_order_blocks[-1:]:  # Only last order block
                direction = ob['type']
                signal = self._generate_signal(direction)
                if signal and signal.confidence >= 0.9:  # Extremely high confidence required for fallback
                    signals.append(signal)
        
        # Log summary instead of individual signals
        if signals:
            print(f"SMC Strategy: Generated {len(signals)} signal(s) - Confidence range: {min(s.confidence for s in signals):.2f}-{max(s.confidence for s in signals):.2f}")
            for signal in signals:
                print(f"  {signal.side.upper()}: Entry {signal.entry:.2f}, SL {signal.stop_loss:.2f}, TP {signal.take_profit:.2f}, Conf {signal.confidence:.2f}")
        elif not self.params.quiet_mode and len(ltf_data) % 100 == 0:  # Progress indicator every 100 bars (less frequent)
            print(f"SMC Strategy: Processing bar {len(ltf_data)} - No signals generated (confidence too low)")
        
        if signals:
            self.last_signal_bar = len(ltf_data)
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
                'current_rsi': float(self.ltf_rsi[0]) if self.ltf_rsi is not None and len(self.ltf_rsi) > 0 else None,
                'current_volume_ratio': float(self.get_ltf_data().volume[0] / self.ltf_volume_sma[0]) if self.ltf_volume_sma is not None and len(self.ltf_volume_sma) > 0 else None,
                'configuration': {
                    'name': self.config.name,
                    'indicators_enabled': sum([
                        self.config.indicators.rsi.enabled,
                        self.config.indicators.macd.enabled,
                        self.config.indicators.bbands.enabled,
                        self.config.indicators.stochastic.enabled,
                        self.config.indicators.volume.enabled,
                        self.config.indicators.atr.enabled
                    ]),
                    'filters_enabled': sum([
                        self.config.filters.rsi.enabled,
                        self.config.filters.volume.enabled,
                        self.config.filters.bbands.enabled,
                        self.config.filters.macd.enabled,
                        self.config.filters.stochastic.enabled
                    ]),
                    'smc_elements_enabled': sum([
                        self.config.smc_elements.order_blocks.enabled,
                        self.config.smc_elements.fair_value_gaps.enabled,
                        self.config.smc_elements.liquidity_pools.enabled,
                        self.config.smc_elements.break_of_structure.enabled
                    ])
                }
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
            print(f"  Configuration: {self.config.name}")
            print(f"  HTF Market Trend: {self.htf_trend}")
            print(f"  HTF Order Blocks: {len(self.htf_order_blocks)}")
            print(f"  HTF Fair Value Gaps: {len(self.htf_fair_value_gaps)}")
            print(f"  HTF Liquidity Pools: {len(self.htf_liquidity_pools)}")
            print(f"  Total Signals Generated: {self.total_signals}")
            print(f"  Indicators Enabled: {sum([self.config.indicators.rsi.enabled, self.config.indicators.macd.enabled, self.config.indicators.bbands.enabled, self.config.indicators.stochastic.enabled, self.config.indicators.volume.enabled, self.config.indicators.atr.enabled])}")
            print(f"  Filters Enabled: {sum([self.config.filters.rsi.enabled, self.config.filters.volume.enabled, self.config.filters.bbands.enabled, self.config.filters.macd.enabled, self.config.filters.stochastic.enabled])}")
        except Exception:
            pass
