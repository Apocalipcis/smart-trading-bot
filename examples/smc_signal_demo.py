#!/usr/bin/env python3
"""
Demo script for SMCSignalStrategy

This script demonstrates how to use the Signal-Only SMC Strategy
with multi-timeframe data feeds.
"""

import sys
import os
import pandas as pd
import backtrader as bt
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategies.smc_signal import SMCSignalStrategy


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


def run_demo():
    """Run the SMC Signal Strategy demo."""
    print("=== SMC Signal Strategy Demo ===\n")
    
    # Create sample data for different timeframes
    print("Creating sample data...")
    
    # HTF data (4H)
    htf_data = create_sample_data('BTCUSDT', '4H', 500)
    htf_data_bt = bt.feeds.PandasData(
        dataname=htf_data,
        datetime=None,
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        name='HTF_4H'
    )
    
    # LTF data (15m)
    ltf_data = create_sample_data('BTCUSDT', '15m', 2000)
    ltf_data_bt = bt.feeds.PandasData(
        dataname=ltf_data,
        datetime=None,
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        name='LTF_15m'
    )
    
    print(f"HTF data: {len(htf_data)} bars (4H)")
    print(f"LTF data: {len(ltf_data)} bars (15m)")
    
    # Create Cerebro engine
    cerebro = bt.Cerebro()
    
    # Add data feeds
    cerebro.adddata(htf_data_bt, name='HTF')
    cerebro.adddata(ltf_data_bt, name='LTF')
    
    # Strategy parameters
    strategy_params = {
        'htf_timeframe': '4H',
        'ltf_timeframe': '15m',
        'risk_per_trade': 0.01,  # 1% risk per trade
        'min_risk_reward': 3.0,   # Minimum 3:1 R:R
        'volume_ratio_threshold': 1.5,
        'use_rsi': True,
        'use_obv': True,
        'use_bbands': False,
    }
    
    print(f"\nStrategy parameters: {strategy_params}")
    
    # Add strategy
    cerebro.addstrategy(SMCSignalStrategy, **strategy_params)
    
    # Set initial cash
    initial_cash = 10000.0
    cerebro.broker.setcash(initial_cash)
    
    print(f"\nInitial cash: ${initial_cash:,.2f}")
    
    # Run backtest
    print("\nRunning backtest...")
    try:
        results = cerebro.run()
        strategy = results[0]
        
        print("\n=== Backtest Results ===")
        print(f"Final cash: ${cerebro.broker.getcash():,.2f}")
        print(f"Total return: {((cerebro.broker.getcash() / initial_cash - 1) * 100):.2f}%")
        
        # Get strategy statistics
        stats = strategy.get_strategy_stats()
        print(f"\nStrategy Statistics:")
        print(f"  Total signals: {stats.get('total_signals', 0)}")
        print(f"  Current positions: {stats.get('current_positions', 0)}")
        print(f"  HTF Trend: {stats.get('htf_trend', 'unknown')}")
        print(f"  HTF Order Blocks: {stats.get('htf_order_blocks_count', 0)}")
        print(f"  HTF Fair Value Gaps: {stats.get('htf_fair_value_gaps_count', 0)}")
        print(f"  HTF Liquidity Pools: {stats.get('htf_liquidity_pools_count', 0)}")
        
        # Show generated signals
        if strategy.signals:
            print(f"\nGenerated Signals ({len(strategy.signals)}):")
            for i, signal in enumerate(strategy.signals[-5:], 1):  # Show last 5 signals
                print(f"  Signal {i}:")
                print(f"    Side: {signal.side}")
                print(f"    Entry: ${signal.entry:.2f}")
                print(f"    Stop Loss: ${signal.stop_loss:.2f}")
                print(f"    Take Profit: ${signal.take_profit:.2f}")
                print(f"    Confidence: {signal.confidence:.2f}")
                print(f"    HTF Zone: {signal.metadata.get('htf_zone_type', 'unknown')}")
                print(f"    Liquidity Sweep: {signal.metadata.get('liquidity_sweep', False)}")
                print(f"    BoS Confirmation: {signal.metadata.get('bos_confirmation', False)}")
                print(f"    Filters Passed: {signal.metadata.get('filters_passed', [])}")
        
        print("\n=== Demo Completed Successfully ===")
        
    except Exception as e:
        print(f"\nError running backtest: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_demo()
