# Strategy Configuration - Only parameters accepted by SMCSignalStrategy
STRATEGY_CONFIG = {
    # Timeframe Configuration
    'htf_timeframe': '4H',           # Higher timeframe
    'ltf_timeframe': '15m',          # Lower timeframe
    'scalping_mode': False,          # Disable scalping for now
    
    # SMC Detection - VERY AGGRESSIVE Parameters for Debugging
    'volume_ratio_threshold': 1.0,   # Reduced to 1.0 (any volume increase)
    'fvg_min_pct': 0.1,             # Reduced to 0.1% (very small gaps)
    'ob_lookback_bars': 10,          # Reduced to 10 (shorter lookback)
    'swing_threshold': 0.005,        # Reduced to 0.5% (very small swings)
    
    # Risk Management - More Aggressive
    'risk_per_trade': 0.02,          # Increased from 0.01 (2% risk)
    'min_risk_reward': 2.0,          # Reduced from 3.0 (easier to meet)
    'max_positions': 5,              # Increased from 3 (more opportunities)
    'sl_buffer_atr': 0.1,            # Reduced from 0.15 (tighter stops)
    
    # Indicator Filters - More Permissive
    'use_rsi': True,                 # Keep RSI filter
    'use_obv': True,                 # Keep OBV filter
    'use_bbands': False,             # Disable BB filter (too restrictive)
    'rsi_overbought': 80,            # Increased from 75 (less restrictive)
    'rsi_oversold': 20,              # Decreased from 25 (less restrictive)
}

# Debug Configuration - These are NOT passed to the strategy
DEBUG_CONFIG = {
    'enable_verbose_logging': True,   # Enable detailed logging
    'log_smc_detection': True,       # Log SMC detection steps
    'log_signal_generation': True,   # Log signal generation process
    'log_data_flow': True,           # Log data flow through strategy
    'save_debug_data': True,         # Save debug data to files
}

# Data Configuration - These are NOT passed to the strategy
DATA_CONFIG = {
    'symbol': 'ETHUSDT',
    'htf_timeframe': '4H',
    'ltf_timeframe': '15m',
    'min_htf_bars': 50,              # Minimum bars needed
    'min_ltf_bars': 20,              # Minimum bars needed
    'data_quality_checks': True,     # Enable data validation
}

# Backtest Configuration - These are NOT passed to the strategy
BACKTEST_CONFIG = {
    'initial_cash': 10000.0,         # Starting capital
    'commission': 0.001,             # 0.1% commission
    'slippage': 0.0005,              # 0.05% slippage
    'enable_short_selling': True,    # Allow short positions
    'max_positions': 5,              # Maximum concurrent positions
}

# SMC Detection Thresholds (Debug Mode) - These are NOT passed to the strategy
SMC_DEBUG_THRESHOLDS = {
    # Order Block Detection
    'ob_min_volume_ratio': 1.0,      # Very lenient volume requirement
    'ob_min_price_move': 0.005,      # 0.5% minimum price move
    'ob_max_lookback': 10,           # Shorter lookback for debugging
    
    # Fair Value Gap Detection
    'fvg_min_gap_pct': 0.1,         # Very small gaps (0.1%)
    'fvg_max_age_bars': 50,         # Allow older FVGs
    
    # Liquidity Pool Detection
    'lp_min_swing_pct': 0.005,      # 0.5% minimum swing
    'lp_lookback_bars': 10,          # Shorter lookback
    
    # Break of Structure
    'bos_min_move_pct': 0.002,       # 0.2% minimum move
    'bos_confirmation_bars': 2,      # Fewer confirmation bars
}

# Signal Generation Thresholds (Debug Mode) - These are NOT passed to the strategy
SIGNAL_DEBUG_THRESHOLDS = {
    'min_confidence': 0.3,           # Lower confidence requirement
    'min_trend_strength': 0.2,       # Lower trend strength requirement
    'max_signal_age_bars': 10,       # Allow older signals
    'enable_weak_signals': True,     # Generate even weak signals
}

# Performance Monitoring - These are NOT passed to the strategy
PERFORMANCE_CONFIG = {
    'track_metrics': True,            # Enable performance tracking
    'save_trades': True,             # Save all trade details
    'save_signals': True,            # Save all signal details
    'generate_reports': True,        # Generate performance reports
}

def get_strategy_config():
    """Get only the configuration parameters that the strategy accepts."""
    return STRATEGY_CONFIG.copy()

def get_debug_config():
    """Get the complete debug configuration (includes non-strategy params for logging)."""
    config = {}
    config.update(STRATEGY_CONFIG)
    config.update(DEBUG_CONFIG)
    config.update(DATA_CONFIG)
    config.update(BACKTEST_CONFIG)
    config.update(SMC_DEBUG_THRESHOLDS)
    config.update(SIGNAL_DEBUG_THRESHOLDS)
    config.update(PERFORMANCE_CONFIG)
    return config

def get_production_config():
    """Get production-ready configuration (more conservative)."""
    production_config = STRATEGY_CONFIG.copy()
    
    # Make production config more conservative
    production_config.update({
        'volume_ratio_threshold': 1.5,   # Back to original
        'fvg_min_pct': 0.5,             # Back to original
        'ob_lookback_bars': 20,          # Back to original
        'swing_threshold': 0.02,         # Back to original
        'risk_per_trade': 0.01,          # Back to original
        'min_risk_reward': 3.0,          # Back to original
        'max_positions': 3,              # Back to original
        'sl_buffer_atr': 0.15,           # Back to original
        'rsi_overbought': 70,            # Back to original
        'rsi_oversold': 30,              # Back to original
    })
    
    return production_config

def print_config_summary(config_name: str = "debug"):
    """Print a summary of the configuration."""
    if config_name == "debug":
        config = get_debug_config()
        print("=== DEBUG Configuration (More Lenient) ===")
    else:
        config = get_production_config()
        print("=== PRODUCTION Configuration (Conservative) ===")
    
    print(f"Strategy: {config['htf_timeframe']} + {config['ltf_timeframe']}")
    print(f"Risk per trade: {config['risk_per_trade']*100:.1f}%")
    print(f"Min R:R ratio: {config['min_risk_reward']:.1f}")
    print(f"Volume threshold: {config['volume_ratio_threshold']:.1f}")
    print(f"FVG min gap: {config['fvg_min_pct']:.1f}%")
    print(f"OB lookback: {config['ob_lookback_bars']} bars")
    print(f"Max positions: {config['max_positions']}")
    print(f"Verbose logging: {config.get('enable_verbose_logging', False)}")

if __name__ == "__main__":
    print("=== ETHUSDT SMC Strategy Configuration ===\n")
    
    print_config_summary("debug")
    print()
    print_config_summary("production")
    
    print("\nConfiguration files loaded successfully!")
    print(f"\nStrategy accepts {len(STRATEGY_CONFIG)} parameters:")
    for key, value in STRATEGY_CONFIG.items():
        print(f"  {key}: {value}")
