#!/usr/bin/env python3
"""
Diagnostic test for SMC strategy to understand why no signals are generated
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import backtrader as bt
from datetime import datetime, timedelta

def create_realistic_smc_data():
    """Create realistic data that should generate SMC patterns."""
    # Create sample HTF data (4H) with SMC patterns
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='4H')
    np.random.seed(42)
    
    # Generate realistic price data with SMC patterns
    base_price = 4000.0
    prices = [base_price]
    
    # Create bullish trend with pullbacks (order blocks)
    for i in range(1, len(dates)):
        if i < 10:  # Initial uptrend
            change = np.random.normal(0.01, 0.015)  # 1% average growth
        elif i < 20:  # Pullback (bearish order block)
            change = np.random.normal(-0.005, 0.02)  # Slight decline
        elif i < 30:  # Recovery (bullish order block)
            change = np.random.normal(0.008, 0.02)  # Recovery
        else:  # Continue trend
            change = np.random.normal(0.005, 0.015)
        
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 100))
    
    # Create realistic OHLC data
    htf_data = pd.DataFrame({
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.008))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.008))) for p in prices],
        'close': prices,
        'volume': [int(1000 + np.random.normal(0, 2000)) for _ in prices]
    }, index=dates)
    
    # Ensure high volume on key reversal points (order blocks)
    htf_data.loc[htf_data.index[9], 'volume'] = 8000  # High volume on pullback
    htf_data.loc[htf_data.index[19], 'volume'] = 9000  # High volume on recovery
    
    # Create sample LTF data (15m) with more volatility
    ltf_dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='15min')
    ltf_prices = [base_price]
    
    for i in range(1, len(ltf_dates)):
        # Higher volatility on LTF
        change = np.random.normal(0, 0.008)  # 0.8% volatility
        new_price = ltf_prices[-1] * (1 + change)
        ltf_prices.append(max(new_price, 100))
    
    ltf_data = pd.DataFrame({
        'open': ltf_prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.004))) for p in ltf_prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.004))) for p in ltf_prices],
        'close': ltf_prices,
        'volume': [int(100 + np.random.normal(0, 200)) for _ in ltf_prices]
    }, index=ltf_dates)
    
    return htf_data, ltf_data

def test_smc_diagnostic():
    """Test SMC strategy with diagnostic information."""
    print("=== SMC Strategy Diagnostic Test ===\n")
    
    try:
        # Import the main strategy
        from src.strategies.smc_signal import SMCSignalStrategy
        
        # Create realistic data
        htf_data, ltf_data = create_realistic_smc_data()
        
        print(f"Created realistic SMC data:")
        print(f"  HTF (4H): {len(htf_data)} bars")
        print(f"  LTF (15m): {len(ltf_data)} bars")
        print(f"  HTF Price range: ${htf_data['low'].min():.2f} - ${htf_data['high'].max():.2f}")
        print(f"  LTF Price range: ${ltf_data['low'].min():.2f} - ${ltf_data['high'].max():.2f}")
        
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
        
        # Add strategy with more lenient configuration
        strategy_config = {
            'htf_timeframe': '4H',
            'ltf_timeframe': '15m',
            'risk_per_trade': 0.01,
            'min_risk_reward': 2.0,  # Reduced from 3.0
            'use_rsi': True,
            'use_obv': True,
            'use_bbands': False,
            'volume_ratio_threshold': 1.2,  # Reduced from 1.5
            'fvg_min_pct': 0.3,  # Reduced from 0.5
            'ob_lookback_bars': 15,  # Reduced from 20
            'swing_threshold': 0.015  # Reduced from 0.02
        }
        
        cerebro.addstrategy(SMCSignalStrategy, **strategy_config)
        
        # Set initial cash
        initial_cash = 10000.0
        cerebro.broker.setcash(initial_cash)
        
        print(f"\nInitial cash: ${initial_cash:,.2f}")
        print("Strategy configuration (more lenient):")
        for key, value in strategy_config.items():
            print(f"  {key}: {value}")
        
        # Run backtest
        print("\nRunning SMC strategy with diagnostics...")
        results = cerebro.run()
        
        if not results:
            print("❌ No results returned!")
            return
        
        strategy = results[0]
        
        # Get detailed strategy statistics
        stats = strategy.get_strategy_stats()
        
        print(f"\n📊 Detailed Strategy Results:")
        print(f"  Final Cash: ${strategy.broker.getcash():,.2f}")
        print(f"  Total Return: {((strategy.broker.getcash() / initial_cash - 1) * 100):.2f}%")
        print(f"  Total Signals: {stats.get('total_signals', 0)}")
        print(f"  HTF Trend: {stats.get('htf_trend', 'unknown')}")
        print(f"  Order Blocks: {stats.get('htf_order_blocks_count', 0)}")
        print(f"  Fair Value Gaps: {stats.get('htf_fair_value_gaps_count', 0)}")
        print(f"  Liquidity Pools: {stats.get('htf_liquidity_pools_count', 0)}")
        print(f"  Current RSI: {stats.get('current_rsi', 'N/A')}")
        print(f"  Volume Ratio: {stats.get('current_volume_ratio', 'N/A')}")
        
        # Check if signals were generated
        if hasattr(strategy, 'signals') and strategy.signals:
            print(f"\n📋 Generated Signals:")
            for i, signal in enumerate(strategy.signals[:5]):
                print(f"  Signal {i+1}:")
                print(f"    Side: {signal.side}")
                print(f"    Entry: ${signal.entry:.2f}")
                print(f"    Stop Loss: ${signal.stop_loss:.2f}")
                print(f"    Take Profit: ${signal.take_profit:.2f}")
                print(f"    Confidence: {signal.confidence:.2f}")
                if signal.metadata:
                    print(f"    Metadata: {signal.metadata}")
        else:
            print("\n📋 No signals generated - Let's diagnose why:")
            
            # Check data availability
            print(f"\n🔍 Data Diagnostics:")
            print(f"  HTF data length: {len(strategy.get_htf_data()) if strategy.get_htf_data() else 'None'}")
            print(f"  LTF data length: {len(strategy.get_ltf_data()) if strategy.get_ltf_data() else 'None'}")
            print(f"  HTF EMA length: {len(strategy.htf_ema_50) if hasattr(strategy, 'htf_ema_50') else 'N/A'}")
            print(f"  LTF RSI length: {len(strategy.ltf_rsi) if hasattr(strategy, 'ltf_rsi') else 'N/A'}")
            
            # Check SMC detection
            print(f"\n🔍 SMC Detection Diagnostics:")
            try:
                htf_trend = strategy.detect_market_bias_htf()
                print(f"  HTF Trend Detection: {htf_trend}")
            except Exception as e:
                print(f"  HTF Trend Detection Error: {e}")
            
            try:
                order_blocks = strategy.detect_order_blocks_htf()
                print(f"  Order Blocks Detection: {len(order_blocks)} found")
                if order_blocks:
                    print(f"    First OB: {order_blocks[0]}")
            except Exception as e:
                print(f"  Order Blocks Detection Error: {e}")
            
            try:
                fvgs = strategy.detect_fair_value_gaps_htf()
                print(f"  Fair Value Gaps: {len(fvgs)} found")
            except Exception as e:
                print(f"  Fair Value Gaps Detection Error: {e}")
        
        print("\n✅ SMC Strategy diagnostic test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error testing SMC strategy: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_smc_diagnostic()
