#!/usr/bin/env python3
"""
Test Fixed SMC Strategy

This script tests the fixed SMCSignalStrategy to verify it generates signals.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import traceback

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_preprocessor import load_eth_data, create_backtrader_feeds
from eth_smc_config import get_strategy_config

def test_fixed_strategy():
    """Test the fixed SMC strategy."""
    print("=== Testing Fixed SMC Strategy ===\n")
    
    try:
        import backtrader as bt
        from fixed_smc_strategy import FixedSMCSignalStrategy
        
        # Load data
        htf_data, ltf_data = load_eth_data()
        htf_feed, ltf_feed = create_backtrader_feeds(htf_data, ltf_data)
        
        # Get strategy config
        strategy_config = get_strategy_config()
        
        print("Strategy Configuration:")
        for key, value in strategy_config.items():
            print(f"  {key}: {value}")
        
        # Create Cerebro
        cerebro = bt.Cerebro()
        
        # Add data feeds
        cerebro.adddata(htf_feed, name='HTF')
        cerebro.adddata(ltf_feed, name='LTF')
        
        # Add fixed strategy
        cerebro.addstrategy(FixedSMCSignalStrategy, **strategy_config)
        
        # Set initial cash
        initial_cash = 10000.0
        cerebro.broker.setcash(initial_cash)
        
        print(f"\nInitial cash: ${initial_cash:,.2f}")
        print(f"Data feeds: HTF ({len(htf_data)} bars), LTF ({len(ltf_data)} bars)")
        
        # Run backtest
        print("\nRunning fixed strategy...")
        results = cerebro.run()
        
        if not results:
            print("❌ No results returned!")
            return
        
        strategy = results[0]
        
        print(f"\nStrategy completed!")
        print(f"Final cash: ${cerebro.broker.getcash():,.2f}")
        
        # Get strategy statistics
        try:
            stats = strategy.get_strategy_stats()
            print(f"\nStrategy Statistics:")
            for key, value in stats.items():
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value}")
                elif isinstance(value, list) and len(value) <= 5:
                    print(f"  {key}: {value}")
                elif isinstance(value, dict):
                    print(f"  {key}: {len(value)} items")
        except Exception as e:
            print(f"Error getting stats: {e}")
        
        # Check for signals
        if hasattr(strategy, 'signals'):
            print(f"\nSignals generated: {len(strategy.signals)}")
            if strategy.signals:
                print(f"✅ SUCCESS: Strategy generated {len(strategy.signals)} signals!")
                for i, signal in enumerate(strategy.signals):
                    print(f"  Signal {i+1}:")
                    print(f"    Side: {signal.side}")
                    print(f"    Entry: ${signal.entry:.2f}")
                    print(f"    Stop Loss: ${signal.stop_loss:.2f}")
                    print(f"    Take Profit: ${signal.take_profit:.2f}")
                    print(f"    Confidence: {signal.confidence:.2f}")
                    if hasattr(signal, 'metadata') and signal.metadata:
                        print(f"    Metadata: {signal.metadata}")
            else:
                print(f"❌ No signals generated")
        else:
            print(f"\n❌ Strategy has no 'signals' attribute!")
        
        # Check strategy state
        print(f"\nStrategy State:")
        if hasattr(strategy, 'htf_trend'):
            print(f"  HTF Trend: {strategy.htf_trend}")
        if hasattr(strategy, 'htf_order_blocks'):
            print(f"  HTF Order Blocks: {len(strategy.htf_order_blocks) if strategy.htf_order_blocks else 0}")
        if hasattr(strategy, 'htf_fair_value_gaps'):
            print(f"  HTF Fair Value Gaps: {len(strategy.htf_fair_value_gaps) if strategy.htf_fair_value_gaps else 0}")
        if hasattr(strategy, 'htf_liquidity_pools'):
            print(f"  HTF Liquidity Pools: {len(strategy.htf_liquidity_pools) if strategy.htf_liquidity_pools else 0}")
        
        # Check if generate_signals was called
        if hasattr(strategy, 'total_signals'):
            print(f"  Total Signals: {strategy.total_signals}")
        
        # Try to call generate_signals manually
        print(f"\n=== Manual Signal Generation Test ===")
        try:
            if hasattr(strategy, 'generate_signals'):
                print("Calling generate_signals() manually...")
                signals = strategy.generate_signals()
                print(f"Manual generate_signals() returned: {len(signals)} signals")
                
                if signals:
                    print(f"✅ Manual signal generation successful!")
                    for i, signal in enumerate(signals):
                        print(f"  Manual Signal {i+1}:")
                        print(f"    Side: {signal.side}")
                        print(f"    Entry: ${signal.entry:.2f}")
                        print(f"    Stop Loss: ${signal.stop_loss:.2f}")
                        print(f"    Take Profit: ${signal.take_profit:.2f}")
                        print(f"    Confidence: {signal.confidence:.2f}")
                else:
                    print("❌ Manual generate_signals() returned no signals!")
            else:
                print("❌ Strategy has no generate_signals method!")
        except Exception as e:
            print(f"Error calling generate_signals manually: {e}")
            traceback.print_exc()
        
        # Final result
        if hasattr(strategy, 'signals') and strategy.signals:
            print(f"\n🎉 SUCCESS: The fixed strategy is working and generating signals!")
            print(f"Total signals generated: {len(strategy.signals)}")
        else:
            print(f"\n❌ The fixed strategy still has issues")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error running fixed strategy: {e}")
        traceback.print_exc()

def main():
    """Main function."""
    print("=== Fixed SMC Strategy Test ===\n")
    
    try:
        test_fixed_strategy()
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
