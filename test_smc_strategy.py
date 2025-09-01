#!/usr/bin/env python3
"""
Simple test for the main SMC strategy
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import backtrader as bt
from datetime import datetime, timedelta

def create_sample_data():
    """Create sample data for testing."""
    # Create sample HTF data (4H)
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='4H')
    np.random.seed(42)
    
    # Generate realistic price data
    base_price = 4000.0
    prices = [base_price]
    
    for i in range(1, len(dates)):
        change = np.random.normal(0, 0.02)  # 2% volatility
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 100))  # Ensure positive prices
    
    htf_data = pd.DataFrame({
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000, 10000, len(prices))
    }, index=dates)
    
    # Create sample LTF data (15m)
    ltf_dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='15min')
    ltf_prices = [base_price]
    
    for i in range(1, len(ltf_dates)):
        change = np.random.normal(0, 0.005)  # 0.5% volatility
        new_price = ltf_prices[-1] * (1 + change)
        ltf_prices.append(max(new_price, 100))
    
    ltf_data = pd.DataFrame({
        'open': ltf_prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in ltf_prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in ltf_prices],
        'close': ltf_prices,
        'volume': np.random.randint(100, 1000, len(ltf_prices))
    }, index=ltf_dates)
    
    return htf_data, ltf_data

def test_smc_strategy():
    """Test the main SMC strategy."""
    print("=== Testing Main SMC Strategy ===\n")
    
    try:
        # Import the main strategy
        from src.strategies.smc_signal import SMCSignalStrategy
        
        # Create sample data
        htf_data, ltf_data = create_sample_data()
        
        print(f"Created sample data:")
        print(f"  HTF (4H): {len(htf_data)} bars")
        print(f"  LTF (15m): {len(ltf_data)} bars")
        
        # Create Backtrader data feeds
        htf_feed = bt.feeds.PandasData(
            dataname=htf_data,
            name='HTF',
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=None
        )
        
        ltf_feed = bt.feeds.PandasData(
            dataname=ltf_data,
            name='LTF',
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=None
        )
        
        # Create Cerebro
        cerebro = bt.Cerebro()
        
        # Add data feeds
        cerebro.adddata(htf_feed, name='HTF')
        cerebro.adddata(ltf_feed, name='LTF')
        
        # Add strategy with configuration
        strategy_config = {
            'htf_timeframe': '4H',
            'ltf_timeframe': '15m',
            'risk_per_trade': 0.01,
            'min_risk_reward': 3.0,
            'use_rsi': True,
            'use_obv': True,
            'use_bbands': False
        }
        
        cerebro.addstrategy(SMCSignalStrategy, **strategy_config)
        
        # Set initial cash
        initial_cash = 10000.0
        cerebro.broker.setcash(initial_cash)
        
        print(f"\nInitial cash: ${initial_cash:,.2f}")
        print("Strategy configuration:")
        for key, value in strategy_config.items():
            print(f"  {key}: {value}")
        
        # Run backtest
        print("\nRunning SMC strategy...")
        results = cerebro.run()
        
        if not results:
            print("❌ No results returned!")
            return
        
        strategy = results[0]
        
        # Get strategy statistics
        stats = strategy.get_strategy_stats()
        
        print(f"\n📊 Strategy Results:")
        print(f"  Final Cash: ${strategy.broker.getcash():,.2f}")
        print(f"  Total Return: {((strategy.broker.getcash() / initial_cash - 1) * 100):.2f}%")
        print(f"  Total Signals: {stats.get('total_signals', 0)}")
        print(f"  HTF Trend: {stats.get('htf_trend', 'unknown')}")
        print(f"  Order Blocks: {stats.get('htf_order_blocks_count', 0)}")
        print(f"  Fair Value Gaps: {stats.get('htf_fair_value_gaps_count', 0)}")
        print(f"  Liquidity Pools: {stats.get('htf_liquidity_pools_count', 0)}")
        
        # Check if signals were generated
        if hasattr(strategy, 'signals') and strategy.signals:
            print(f"\n📋 Generated Signals:")
            for i, signal in enumerate(strategy.signals[:5]):  # Show first 5
                print(f"  Signal {i+1}:")
                print(f"    Side: {signal.side}")
                print(f"    Entry: ${signal.entry:.2f}")
                print(f"    Stop Loss: ${signal.stop_loss:.2f}")
                print(f"    Take Profit: ${signal.take_profit:.2f}")
                print(f"    Confidence: {signal.confidence:.2f}")
                if signal.metadata:
                    print(f"    Metadata: {signal.metadata}")
        else:
            print("\n📋 No signals generated (this might be normal for sample data)")
        
        print("\n✅ SMC Strategy test completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error testing SMC strategy: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_smc_strategy()
