#!/usr/bin/env python3
"""
Minimal Real Data Demo for SMC Strategy

This script demonstrates the SMC Strategy using REAL Binance data
with minimal configuration - only basic SMC elements, no indicators.
"""

import sys
import os
import pandas as pd
import backtrader as bt
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategies.smc_signal import SMCSignalStrategy
from strategies.smc_config import SMCStrategyConfig


def load_real_binance_data(symbol: str, timeframe: str) -> pd.DataFrame:
    """Load real Binance data from parquet files."""
    data_path = f"../data/candles/binance_futures/{symbol}/{timeframe}.parquet"
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    # Load data
    df = pd.read_parquet(data_path)
    
    # Convert timestamp columns
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    elif 'open_time' in df.columns:
        df['datetime'] = pd.to_datetime(df['open_time'], unit='ms')
    
    # Ensure we have the required columns
    required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Set datetime as index
    df.set_index('datetime', inplace=True)
    
    # Sort by datetime
    df.sort_index(inplace=True)
    
    # Convert to float
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove any rows with NaN values
    df.dropna(inplace=True)
    
    print(f"✅ Loaded {len(df)} bars of {timeframe} data for {symbol}")
    print(f"   Date range: {df.index[0]} to {df.index[-1]}")
    print(f"   Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    
    return df


def create_backtrader_datafeed(df: pd.DataFrame, name: str) -> bt.feeds.PandasData:
    """Convert pandas DataFrame to Backtrader data feed."""
    # Ensure datetime is the index
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have DatetimeIndex")
    
    # Create Backtrader data feed
    data_feed = bt.feeds.PandasData(
        dataname=df,
        datetime=None,  # Use index
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        name=name
    )
    
    return data_feed


def create_minimal_config() -> SMCStrategyConfig:
    """Create a minimal configuration with NO indicators."""
    return SMCStrategyConfig(
        name="Minimal Real Data Test",
        description="No indicators, only SMC elements for real data testing",
        htf_timeframe="4h",
        ltf_timeframe="15m",
        scalping_mode=False,
        indicators={
            'rsi': {'enabled': False},
            'macd': {'enabled': False},
            'bbands': {'enabled': False},
            'stochastic': {'enabled': False},
            'volume': {'enabled': False},
            'atr': {'enabled': False}
        },
        filters={
            'rsi': {'enabled': False},
            'volume': {'enabled': False},
            'bbands': {'enabled': False},
            'macd': {'enabled': False},
            'stochastic': {'enabled': False},
            'min_filters_required': 1  # At least 1 filter required (even if disabled)
        },
        smc_elements={
            'order_blocks': {'enabled': True, 'lookback_bars': 5, 'volume_threshold': 1.2},
            'fair_value_gaps': {'enabled': True, 'min_gap_pct': 0.3},
            'liquidity_pools': {'enabled': True, 'swing_threshold': 0.015},
            'break_of_structure': {'enabled': True, 'confirmation_bars': 1}
        },
        risk_management={
            'risk_per_trade': 0.01,
            'min_risk_reward': 2.0,
            'max_positions': 2,
            'sl_buffer_atr': 0.1
        }
    )


def run_minimal_real_data_backtest():
    """Run backtest with real data using minimal configuration."""
    print("=== Minimal Real Data Backtest ===")
    print("Using NO indicators, only SMC elements")
    
    try:
        # Load real data
        print("\nLoading real Binance data...")
        
        # Load HTF data (4h)
        htf_data = load_real_binance_data('BTCUSDT', '4h')
        htf_data_bt = create_backtrader_datafeed(htf_data, 'HTF')
        
        # Load LTF data (15m)
        ltf_data = load_real_binance_data('BTCUSDT', '15m')
        ltf_data_bt = create_backtrader_datafeed(ltf_data, 'LTF')
        
        print(f"\nData Summary:")
        print(f"  HTF (4h): {len(htf_data)} bars")
        print(f"  LTF (15m): {len(ltf_data)} bars")
        
        # Check if we have enough data
        if len(htf_data) < 20:
            print(f"⚠️  Warning: HTF data has only {len(htf_data)} bars, need at least 20")
        if len(ltf_data) < 50:
            print(f"⚠️  Warning: LTF data has only {len(ltf_data)} bars, need at least 50")
        
        # Create minimal configuration
        config = create_minimal_config()
        print(f"\nConfiguration: {config.name}")
        print(f"  Indicators enabled: 0")
        print(f"  Filters enabled: 0")
        print(f"  SMC elements enabled: 4")
        print(f"  Order Blocks: {config.smc_elements.order_blocks.enabled}")
        print(f"  Fair Value Gaps: {config.smc_elements.fair_value_gaps.enabled}")
        print(f"  Liquidity Pools: {config.smc_elements.liquidity_pools.enabled}")
        print(f"  Break of Structure: {config.smc_elements.break_of_structure.enabled}")
        
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
            'quiet_mode': False
        }
        
        # Add strategy
        cerebro.addstrategy(SMCSignalStrategy, **strategy_params)
        
        # Set initial cash
        initial_cash = 10000.0
        cerebro.broker.setcash(initial_cash)
        
        print(f"\nInitial cash: ${initial_cash:,.2f}")
        
        # Run backtest
        print("\nRunning backtest with real data...")
        results = cerebro.run()
        strategy = results[0]
        
        print("\n=== Real Data Backtest Results ===")
        print(f"Final cash: ${cerebro.broker.getcash():,.2f}")
        print(f"Total return: {((cerebro.broker.getcash() / initial_cash - 1) * 100):.2f}%")
        
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
        else:
            print("\nNo signals generated during this period.")
        
        print(f"\n=== Minimal Real Data Test Completed Successfully ===")
        return True
        
    except Exception as e:
        print(f"\nError running minimal real data backtest: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        # Check if real data exists
        btc_data_path = "../data/candles/binance_futures/BTCUSDT/4h.parquet"
        if not os.path.exists(btc_data_path):
            print("❌ Real data not found!")
            print("Please ensure you have downloaded Binance data to data/candles/binance_futures/")
            sys.exit(1)
        
        # Run the minimal demo
        success = run_minimal_real_data_backtest()
        
        if success:
            print("\n🎉 Minimal Real Data Demo Completed Successfully!")
            print("\n💡 What we tested:")
            print("  - Real Binance BTCUSDT data loading")
            print("  - SMC strategy with NO indicators")
            print("  - Pure SMC elements (Order Blocks, FVG, Liquidity Pools)")
            print("  - Signal generation based only on market structure")
            print("  - Real market data analysis")
        else:
            print("\n❌ Demo failed. Check the error messages above.")
        
    except Exception as e:
        print(f"\nError during minimal real data demonstration: {e}")
        import traceback
        traceback.print_exc()
