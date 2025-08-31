#!/usr/bin/env python3
"""
Main Debugging Script for ETHUSDT SMC Signal Strategy

This script systematically tests and debugs the SMC strategy to identify
why no signals are being generated.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import our modules
from data_preprocessor import load_eth_data, validate_data_quality, create_backtrader_feeds
from eth_smc_config import get_debug_config

# Import strategy
try:
    from strategies.smc_signal import SMCSignalStrategy
    print("✅ SMCSignalStrategy imported successfully")
except ImportError as e:
    print(f"❌ Failed to import SMCSignalStrategy: {e}")
    sys.exit(1)

def test_data_preprocessing():
    """Test data preprocessing and validation."""
    print("\n=== Phase 1: Data Preprocessing Test ===")
    
    try:
        # Load and preprocess data
        htf_data, ltf_data = load_eth_data()
        
        # Validate data quality
        if not validate_data_quality(htf_data, ltf_data):
            print("❌ Data quality validation failed!")
            return False, None, None
        
        print("✅ Data preprocessing successful!")
        return True, htf_data, ltf_data
        
    except Exception as e:
        print(f"❌ Data preprocessing failed: {e}")
        traceback.print_exc()
        return False, None, None

def test_backtrader_integration(htf_data, ltf_data):
    """Test Backtrader integration."""
    print("\n=== Phase 2: Backtrader Integration Test ===")
    
    try:
        # Create Backtrader feeds
        htf_feed, ltf_feed = create_backtrader_feeds(htf_data, ltf_data)
        
        if htf_feed is None or ltf_feed is None:
            print("❌ Failed to create Backtrader feeds")
            return False, None, None
        
        print("✅ Backtrader feeds created successfully!")
        return True, htf_feed, ltf_feed
        
    except Exception as e:
        print(f"❌ Backtrader integration failed: {e}")
        traceback.print_exc()
        return False, None, None

def test_strategy_initialization(htf_feed, ltf_feed):
    """Test strategy initialization and basic functionality."""
    print("\n=== Phase 3: Strategy Initialization Test ===")
    
    try:
        import backtrader as bt
        
        # Create Cerebro engine
        cerebro = bt.Cerebro()
        
        # Add data feeds
        cerebro.adddata(htf_feed, name='HTF')
        cerebro.adddata(ltf_feed, name='LTF')
        
        # Get strategy configuration (only valid parameters)
        from eth_smc_config import get_strategy_config
        strategy_config = get_strategy_config()
        
        # Add strategy with valid parameters only
        cerebro.addstrategy(SMCSignalStrategy, **strategy_config)
        
        # Store full config for later use
        config = get_debug_config()
        
        # Set initial cash
        initial_cash = config['initial_cash']
        cerebro.broker.setcash(initial_cash)
        
        print(f"✅ Strategy initialized with ${initial_cash:,.2f} initial cash")
        print(f"✅ Configuration applied: {len(config)} parameters")
        
        return True, cerebro, config
        
    except Exception as e:
        print(f"❌ Strategy initialization failed: {e}")
        traceback.print_exc()
        return False, None, None

def test_strategy_logic():
    """Test individual SMC detection components."""
    print("\n=== Phase 4: Strategy Logic Test ===")
    
    try:
        # Create a minimal strategy instance for testing
        config = get_debug_config()
        
        # Test basic strategy properties
        print(f"Strategy version: {SMCSignalStrategy.version}")
        print(f"Required roles: {SMCSignalStrategy.required_roles}")
        
        # Try to get parameters count safely
        try:
            if hasattr(SMCSignalStrategy.params, '_asdict'):
                params_count = len(SMCSignalStrategy.params._asdict())
            else:
                params_count = len(dict(SMCSignalStrategy.params))
            print(f"Parameters count: {params_count}")
        except Exception as e:
            print(f"Parameters count: Unable to determine ({e})")
        
        # Test parameter access
        try:
            params_dict = dict(SMCSignalStrategy.params)
            print(f"Key parameters:")
            for key, value in list(params_dict.items())[:10]:  # Show first 10
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"  Parameter access failed: {e}")
            # Try alternative approach
            try:
                params = SMCSignalStrategy.params
                print(f"  Parameters object type: {type(params)}")
                if hasattr(params, '_asdict'):
                    params_dict = params._asdict()
                    for key, value in list(params_dict.items())[:10]:
                        print(f"  {key}: {value}")
                else:
                    print(f"  Parameters: {params}")
            except Exception as e2:
                print(f"  Alternative parameter access failed: {e2}")
        
        print("✅ Strategy logic test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Strategy logic test failed: {e}")
        traceback.print_exc()
        return False

def run_mini_backtest(cerebro, config):
    """Run a mini backtest to test signal generation."""
    print("\n=== Phase 5: Mini Backtest Test ===")
    
    try:
        print("Running mini backtest...")
        
        # Run backtest
        results = cerebro.run()
        
        if not results:
            print("❌ No results returned from backtest")
            return False
        
        strategy = results[0]
        
        # Get strategy statistics
        stats = strategy.get_strategy_stats()
        
        print(f"\n=== Mini Backtest Results ===")
        print(f"Final cash: ${cerebro.broker.getcash():,.2f}")
        print(f"Total return: {((cerebro.broker.getcash() / config['initial_cash'] - 1) * 100):.2f}%")
        
        print(f"\nStrategy Statistics:")
        print(f"  Total signals: {stats.get('total_signals', 0)}")
        print(f"  Current positions: {stats.get('current_positions', 0)}")
        print(f"  HTF Trend: {stats.get('htf_trend', 'unknown')}")
        print(f"  HTF Order Blocks: {stats.get('htf_order_blocks_count', 0)}")
        print(f"  HTF Fair Value Gaps: {stats.get('htf_fair_value_gaps_count', 0)}")
        print(f"  HTF Liquidity Pools: {stats.get('htf_liquidity_pools_count', 0)}")
        
        # Check for signals
        if hasattr(strategy, 'signals') and strategy.signals:
            print(f"\nGenerated Signals ({len(strategy.signals)}):")
            for i, signal in enumerate(strategy.signals[-3:], 1):  # Show last 3
                print(f"  Signal {i}:")
                print(f"    Side: {signal.side}")
                print(f"    Entry: ${signal.entry:.2f}")
                print(f"    Stop Loss: ${signal.stop_loss:.2f}")
                print(f"    Take Profit: ${signal.take_profit:.2f}")
                print(f"    Confidence: {signal.confidence:.2f}")
        else:
            print("\n❌ No signals generated during backtest")
            
            # Try to understand why
            if hasattr(strategy, 'htf_trend'):
                print(f"HTF Trend detected: {strategy.htf_trend}")
            if hasattr(strategy, 'htf_order_blocks'):
                print(f"HTF Order Blocks: {len(strategy.htf_order_blocks) if strategy.htf_order_blocks else 0}")
            if hasattr(strategy, 'htf_fair_value_gaps'):
                print(f"HTF Fair Value Gaps: {len(strategy.htf_fair_value_gaps) if strategy.htf_fair_value_gaps else 0}")
        
        return len(strategy.signals) > 0 if hasattr(strategy, 'signals') else False
        
    except Exception as e:
        print(f"❌ Mini backtest failed: {e}")
        traceback.print_exc()
        return False

def run_full_backtest(cerebro, config):
    """Run a full backtest with the working configuration."""
    print("\n=== Phase 6: Full Backtest ===")
    
    try:
        print("Running full backtest...")
        
        # Run backtest
        results = cerebro.run()
        strategy = results[0]
        
        print(f"\n=== Full Backtest Results ===")
        print(f"Final cash: ${cerebro.broker.getcash():,.2f}")
        print(f"Total return: {((cerebro.broker.getcash() / config['initial_cash'] - 1) * 100):.2f}%")
        
        # Get detailed statistics
        stats = strategy.get_strategy_stats()
        
        print(f"\nDetailed Statistics:")
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value}")
            elif isinstance(value, list) and len(value) <= 5:
                print(f"  {key}: {value}")
            elif isinstance(value, dict):
                print(f"  {key}: {len(value)} items")
        
        # Show all signals
        if hasattr(strategy, 'signals') and strategy.signals:
            print(f"\nAll Generated Signals ({len(strategy.signals)}):")
            for i, signal in enumerate(strategy.signals, 1):
                print(f"  Signal {i}:")
                print(f"    Side: {signal.side}")
                print(f"    Entry: ${signal.entry:.2f}")
                print(f"    Stop Loss: ${signal.stop_loss:.2f}")
                print(f"    Take Profit: ${signal.take_profit:.2f}")
                print(f"    Confidence: {signal.confidence:.2f}")
                if hasattr(signal, 'metadata') and signal.metadata:
                    print(f"    Metadata: {signal.metadata}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full backtest failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main debugging function."""
    print("=== ETHUSDT SMC Signal Strategy Debug Session ===")
    print(f"Started at: {datetime.now()}")
    
    # Phase 1: Data preprocessing
    success, htf_data, ltf_data = test_data_preprocessing()
    if not success:
        print("❌ Debug session failed at data preprocessing phase")
        return
    
    # Phase 2: Backtrader integration
    success, htf_feed, ltf_feed = test_backtrader_integration(htf_data, ltf_data)
    if not success:
        print("❌ Debug session failed at Backtrader integration phase")
        return
    
    # Phase 3: Strategy initialization
    success, cerebro, config = test_strategy_initialization(htf_feed, ltf_feed)
    if not success:
        print("❌ Debug session failed at strategy initialization phase")
        return
    
    # Phase 4: Strategy logic test
    success = test_strategy_logic()
    if not success:
        print("❌ Debug session failed at strategy logic test phase")
        return
    
    # Phase 5: Mini backtest
    signals_generated = run_mini_backtest(cerebro, config)
    
    if signals_generated:
        print("\n✅ SUCCESS: Signals were generated!")
        
        # Phase 6: Full backtest
        run_full_backtest(cerebro, config)
        
        print("\n🎉 Debug session completed successfully!")
        print("The SMC strategy is now working and generating signals.")
        
    else:
        print("\n❌ ISSUE IDENTIFIED: No signals generated")
        print("This indicates a problem with:")
        print("1. SMC detection algorithms")
        print("2. Signal generation logic")
        print("3. Parameter thresholds")
        print("4. Data synchronization")
        
        print("\nNext steps:")
        print("1. Check SMC detection logs")
        print("2. Adjust detection thresholds")
        print("3. Verify data alignment")
        print("4. Test with different parameters")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Debug session interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        traceback.print_exc()
