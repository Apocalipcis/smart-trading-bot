#!/usr/bin/env python3
"""
Demo script for SMC Strategy Configuration System

This script demonstrates how to use the new configurable SMC Strategy
with different configurations loaded from JSON files.
"""

import sys
import os
import json
import pandas as pd
import backtrader as bt
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategies.smc_signal import SMCSignalStrategy
from strategies.smc_config import SMCStrategyConfig, load_config_from_json


def create_sample_data(symbol: str, timeframe: str, bars: int = 1000) -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    import numpy as np
    
    # Generate sample data
    dates = pd.date_range(start='2024-01-01', periods=bars, freq='1H')
    
    # Create realistic price movement
    np.random.seed(42)
    base_price = 50000.0  # BTC-like price
    
    # Generate price series with some trend and volatility
    returns = np.random.normal(0.0001, 0.02, bars)  # Small positive drift, 2% volatility
    prices = [base_price]
    
    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)
    
    # Create OHLCV data
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        # Generate realistic OHLC from close price
        volatility = price * 0.01  # 1% volatility per bar
        
        open_price = price + np.random.normal(0, volatility * 0.3)
        high_price = max(open_price, price) + np.random.uniform(0, volatility * 0.5)
        low_price = min(open_price, price) - np.random.uniform(0, volatility * 0.5)
        close_price = price
        
        # Generate volume (higher volume on larger moves)
        price_change = abs(close_price - open_price)
        base_volume = 1000
        volume = base_volume + (price_change / price) * 10000
        
        data.append({
            'datetime': date,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    
    return df


def load_configuration_presets():
    """Load all available configuration presets."""
    configs_dir = os.path.join(os.path.dirname(__file__), '..', 'configs', 'smc_presets')
    
    configs = {}
    for filename in os.listdir(configs_dir):
        if filename.endswith('.json'):
            config_name = filename.replace('.json', '')
            config_path = os.path.join(configs_dir, filename)
            try:
                config = load_config_from_json(config_path)
                configs[config_name] = config
                print(f"✓ Loaded {config_name} configuration")
            except Exception as e:
                print(f"✗ Failed to load {config_name} configuration: {e}")
    
    return configs


def run_backtest_with_config(config: SMCStrategyConfig, config_name: str):
    """Run backtest with a specific configuration."""
    print(f"\n=== Testing {config_name.upper()} Configuration ===")
    print(f"Description: {config.description}")
    print(f"Timeframes: {config.htf_timeframe} / {config.ltf_timeframe}")
    print(f"Scalping Mode: {config.scalping_mode}")
    
    # Create sample data for different timeframes
    htf_bars = 500 if config.htf_timeframe == '4H' else 1000
    ltf_bars = 2000 if config.ltf_timeframe == '15m' else 3000
    
    # HTF data
    htf_data = create_sample_data('BTCUSDT', config.htf_timeframe, htf_bars)
    htf_data_bt = bt.feeds.PandasData(
        dataname=htf_data,
        datetime=None,
        open='open', high='high', low='low', close='close', volume='volume',
        name='HTF'
    )
    
    # LTF data
    ltf_data = create_sample_data('BTCUSDT', config.ltf_timeframe, ltf_bars)
    ltf_data_bt = bt.feeds.PandasData(
        dataname=ltf_data,
        datetime=None,
        open='open', high='high', low='low', close='close', volume='volume',
        name='LTF'
    )
    
    # Create Cerebro engine
    cerebro = bt.Cerebro()
    
    # Add data feeds
    cerebro.adddata(htf_data_bt, name='HTF')
    cerebro.adddata(ltf_data_bt, name='LTF')
    
    # Convert configuration to strategy parameters
    strategy_params = {
        'indicators_config': config.indicators.model_dump(),
        'filters_config': config.filters.model_dump(),
        'smc_config': config.smc_elements.model_dump(),
        'risk_config': config.risk_management.model_dump(),
        'htf_timeframe': config.htf_timeframe,
        'ltf_timeframe': config.ltf_timeframe,
        'scalping_mode': config.scalping_mode,
        'quiet_mode': True  # Reduce log spam during demo
    }
    
    # Add strategy
    cerebro.addstrategy(SMCSignalStrategy, **strategy_params)
    
    # Set initial cash
    initial_cash = 10000.0
    cerebro.broker.setcash(initial_cash)
    
    # Run backtest
    try:
        results = cerebro.run()
        strategy = results[0]
        
        print(f"\nBacktest Results:")
        print(f"  Final cash: ${cerebro.broker.getcash():,.2f}")
        print(f"  Total return: {((cerebro.broker.getcash() / initial_cash - 1) * 100):.2f}%")
        
        # Get strategy statistics
        stats = strategy.get_strategy_stats()
        print(f"\nStrategy Statistics:")
        print(f"  Configuration: {stats.get('configuration', {}).get('name', 'Unknown')}")
        print(f"  Total signals: {stats.get('total_signals', 0)}")
        print(f"  Current positions: {stats.get('current_positions', 0)}")
        print(f"  HTF Trend: {stats.get('htf_trend', 'unknown')}")
        print(f"  HTF Order Blocks: {stats.get('htf_order_blocks_count', 0)}")
        print(f"  HTF Fair Value Gaps: {stats.get('htf_fair_value_gaps_count', 0)}")
        print(f"  HTF Liquidity Pools: {stats.get('htf_liquidity_pools_count', 0)}")
        print(f"  Indicators Enabled: {stats.get('configuration', {}).get('indicators_enabled', 0)}")
        print(f"  Filters Enabled: {stats.get('configuration', {}).get('filters_enabled', 0)}")
        print(f"  SMC Elements Enabled: {stats.get('configuration', {}).get('smc_elements_enabled', 0)}")
        
        # Show generated signals
        if strategy.signals:
            print(f"\nGenerated Signals ({len(strategy.signals)}):")
            for i, signal in enumerate(strategy.signals[-3:], 1):  # Show last 3 signals
                print(f"  Signal {i}:")
                print(f"    Side: {signal.side}")
                print(f"    Entry: ${signal.entry:.2f}")
                print(f"    Stop Loss: ${signal.stop_loss:.2f}")
                print(f"    Take Profit: ${signal.take_profit:.2f}")
                print(f"    Confidence: {signal.confidence:.2f}")
                print(f"    HTF Zone: {signal.metadata.get('htf_zone_type', 'unknown')}")
                print(f"    Filters Passed: {signal.metadata.get('filters_passed', [])}")
        
        return True
        
    except Exception as e:
        print(f"\nError running backtest: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_configuration_system():
    """Demonstrate the configuration system."""
    print("=== SMC Strategy Configuration System Demo ===\n")
    
    # Load configuration presets
    print("Loading configuration presets...")
    configs = load_configuration_presets()
    
    if not configs:
        print("No configurations found. Creating default configurations...")
        configs = {
            'default': SMCStrategyConfig.get_default_config(),
            'conservative': SMCStrategyConfig.get_conservative_config(),
            'aggressive': SMCStrategyConfig.get_aggressive_config(),
            'scalping': SMCStrategyConfig.get_scalping_config()
        }
    
    print(f"\nLoaded {len(configs)} configurations: {list(configs.keys())}")
    
    # Test each configuration
    successful_tests = 0
    total_tests = len(configs)
    
    for config_name, config in configs.items():
        if run_backtest_with_config(config, config_name):
            successful_tests += 1
    
    print(f"\n=== Demo Summary ===")
    print(f"Total configurations tested: {total_tests}")
    print(f"Successful tests: {successful_tests}")
    print(f"Failed tests: {total_tests - successful_tests}")
    
    if successful_tests == total_tests:
        print("\n🎉 All configurations tested successfully!")
    else:
        print(f"\n⚠️  {total_tests - successful_tests} configurations failed")


def demo_custom_configuration():
    """Demonstrate creating custom configurations programmatically."""
    print("\n=== Custom Configuration Demo ===")
    
    # Create a custom configuration
    custom_config = SMCStrategyConfig(
        name="Custom SMC",
        description="My custom configuration",
        htf_timeframe="1h",
        ltf_timeframe="5m",
        indicators={
            'rsi': {'enabled': True, 'period': 21, 'overbought': 75, 'oversold': 25},
            'macd': {'enabled': True, 'fast_period': 8, 'slow_period': 21, 'signal_period': 5},
            'bbands': {'enabled': False},
            'stochastic': {'enabled': False},
            'volume': {'enabled': True, 'period': 15},
            'atr': {'enabled': True, 'period': 10}
        },
        filters={
            'rsi': {'enabled': True, 'min_confidence': 0.5},
            'volume': {'enabled': True, 'min_volume_ratio': 1.1},
            'bbands': {'enabled': False},
            'macd': {'enabled': True, 'signal_cross': True},
            'stochastic': {'enabled': False},
            'min_filters_required': 2
        },
        smc_elements={
            'order_blocks': {'enabled': True, 'lookback_bars': 18, 'volume_threshold': 1.8},
            'fair_value_gaps': {'enabled': True, 'min_gap_pct': 0.8},
            'liquidity_pools': {'enabled': True, 'swing_threshold': 0.025},
            'break_of_structure': {'enabled': True, 'confirmation_bars': 2}
        },
        risk_management={
            'risk_per_trade': 0.015,
            'min_risk_reward': 3.5,
            'max_positions': 4,
            'sl_buffer_atr': 0.18
        }
    )
    
    print("Created custom configuration:")
    print(f"  Name: {custom_config.name}")
    print(f"  Description: {custom_config.description}")
    print(f"  Timeframes: {custom_config.htf_timeframe} / {custom_config.ltf_timeframe}")
    print(f"  RSI Period: {custom_config.indicators.rsi.period}")
    print(f"  MACD Fast Period: {custom_config.indicators.macd.fast_period}")
    print(f"  Risk per Trade: {custom_config.risk_management.risk_per_trade:.1%}")
    
    # Test the custom configuration
    print("\nTesting custom configuration...")
    run_backtest_with_config(custom_config, "Custom")


if __name__ == "__main__":
    try:
        # Run the main demo
        demo_configuration_system()
        
        # Run custom configuration demo
        demo_custom_configuration()
        
        print("\n=== Demo Completed Successfully! ===")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()
