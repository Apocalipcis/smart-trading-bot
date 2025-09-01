#!/usr/bin/env python3
"""
Basic SMC Demo - Testing Core SMC Elements

This script tests the basic SMC functionality using real data
without any complex indicators or filters.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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


def detect_order_blocks(df: pd.DataFrame, lookback: int = 10, volume_threshold: float = 1.5) -> list:
    """Detect order blocks in the data."""
    order_blocks = []
    
    if len(df) < lookback + 1:
        return order_blocks
    
    for i in range(lookback, len(df) - 1):
        current_bar = df.iloc[i]
        prev_bar = df.iloc[i-1]
        
        # Bullish Order Block: strong move up after consolidation
        if (current_bar['close'] > current_bar['open'] and  # Current bar is bullish
            current_bar['volume'] > df['volume'].rolling(20).mean().iloc[i] * volume_threshold and
            prev_bar['low'] < prev_bar['open'] and  # Previous bar has lower low
            current_bar['close'] > prev_bar['high']):  # Break above previous high
            
            order_blocks.append({
                'type': 'bullish',
                'index': i,
                'timestamp': df.index[i],
                'high': float(current_bar['high']),
                'low': float(prev_bar['low']),
                'volume': float(current_bar['volume']),
                'strength': float(current_bar['close'] - prev_bar['low'])
            })
        
        # Bearish Order Block: strong move down after consolidation
        elif (current_bar['close'] < current_bar['open'] and  # Current bar is bearish
              current_bar['volume'] > df['volume'].rolling(20).mean().iloc[i] * volume_threshold and
              prev_bar['high'] > prev_bar['open'] and  # Previous bar has higher high
              current_bar['close'] < prev_bar['low']):  # Break below previous low
            
            order_blocks.append({
                'type': 'bearish',
                'index': i,
                'timestamp': df.index[i],
                'high': float(prev_bar['high']),
                'low': float(current_bar['low']),
                'volume': float(current_bar['volume']),
                'strength': float(prev_bar['high'] - current_bar['close'])
            })
    
    return order_blocks


def detect_fair_value_gaps(df: pd.DataFrame, min_gap_pct: float = 0.5) -> list:
    """Detect Fair Value Gaps in the data."""
    fvgs = []
    
    if len(df) < 3:
        return fvgs
    
    for i in range(2, len(df)):
        current_bar = df.iloc[i]
        prev_bar = df.iloc[i-1]
        prev_prev_bar = df.iloc[i-2]
        
        # Bullish FVG: gap up
        if (prev_bar['low'] > prev_prev_bar['high'] and
            (prev_bar['low'] - prev_prev_bar['high']) / prev_prev_bar['high'] * 100 >= min_gap_pct):
            
            fvgs.append({
                'type': 'bullish',
                'index': i,
                'timestamp': df.index[i],
                'top': float(current_bar['low']),
                'bottom': float(prev_prev_bar['high']),
                'gap_size_pct': float((prev_bar['low'] - prev_prev_bar['high']) / prev_prev_bar['high'] * 100)
            })
        
        # Bearish FVG: gap down
        elif (prev_bar['high'] < prev_prev_bar['low'] and
              (prev_prev_bar['low'] - prev_bar['high']) / prev_prev_bar['low'] * 100 >= min_gap_pct):
            
            fvgs.append({
                'type': 'bearish',
                'index': i,
                'timestamp': df.index[i],
                'top': float(prev_prev_bar['low']),
                'bottom': float(current_bar['high']),
                'gap_size_pct': float((prev_prev_bar['low'] - prev_bar['high']) / prev_prev_bar['low'] * 100)
            })
    
    return fvgs


def detect_liquidity_pools(df: pd.DataFrame, swing_threshold: float = 0.02) -> list:
    """Detect liquidity pools (swing highs/lows) in the data."""
    liquidity_pools = []
    
    if len(df) < 3:
        return liquidity_pools
    
    for i in range(1, len(df) - 1):
        current_bar = df.iloc[i]
        prev_bar = df.iloc[i-1]
        next_bar = df.iloc[i+1]
        
        # Swing High (Resistance)
        if (current_bar['high'] > prev_bar['high'] and 
            current_bar['high'] > next_bar['high'] and
            (current_bar['high'] - min(prev_bar['low'], next_bar['low'])) / current_bar['high'] >= swing_threshold):
            
            liquidity_pools.append({
                'type': 'resistance',
                'index': i,
                'timestamp': df.index[i],
                'price': float(current_bar['high']),
                'strength': float(current_bar['high'] - min(prev_bar['low'], next_bar['low']))
            })
        
        # Swing Low (Support)
        elif (current_bar['low'] < prev_bar['low'] and 
              current_bar['low'] < next_bar['low'] and
              (max(prev_bar['high'], next_bar['high']) - current_bar['low']) / current_bar['low'] >= swing_threshold):
            
            liquidity_pools.append({
                'type': 'support',
                'index': i,
                'timestamp': df.index[i],
                'price': float(current_bar['low']),
                'strength': float(max(prev_bar['high'], next_bar['high']) - current_bar['low'])
            })
    
    return liquidity_pools


def analyze_market_structure(df: pd.DataFrame) -> dict:
    """Analyze market structure using SMC principles."""
    print("\n=== Market Structure Analysis ===")
    
    # Detect SMC elements
    order_blocks = detect_order_blocks(df, lookback=10, volume_threshold=1.5)
    fvgs = detect_fair_value_gaps(df, min_gap_pct=0.5)
    liquidity_pools = detect_liquidity_pools(df, swing_threshold=0.015)
    
    # Market trend analysis
    if len(df) >= 20:
        recent_highs = df['high'].tail(20).max()
        recent_lows = df['low'].tail(20).min()
        current_price = df['close'].iloc[-1]
        
        # Simple trend detection
        if current_price > (recent_highs + recent_lows) / 2:
            trend = "bullish"
        elif current_price < (recent_highs + recent_lows) / 2:
            trend = "bearish"
        else:
            trend = "neutral"
    else:
        trend = "insufficient_data"
    
    # Results
    results = {
        'trend': trend,
        'order_blocks': order_blocks,
        'fair_value_gaps': fvgs,
        'liquidity_pools': liquidity_pools,
        'total_patterns': len(order_blocks) + len(fvgs) + len(liquidity_pools)
    }
    
    print(f"Market Trend: {trend.upper()}")
    print(f"Order Blocks Found: {len(order_blocks)}")
    print(f"Fair Value Gaps Found: {len(fvgs)}")
    print(f"Liquidity Pools Found: {len(liquidity_pools)}")
    print(f"Total SMC Patterns: {results['total_patterns']}")
    
    return results


def show_detailed_patterns(analysis: dict):
    """Show detailed information about detected patterns."""
    print("\n=== Detailed Pattern Analysis ===")
    
    # Order Blocks
    if analysis['order_blocks']:
        print(f"\n📊 Order Blocks ({len(analysis['order_blocks'])}):")
        for i, ob in enumerate(analysis['order_blocks'][-3:], 1):  # Show last 3
            print(f"  {i}. {ob['type'].upper()} Order Block")
            print(f"     Time: {ob['timestamp']}")
            print(f"     Price Range: ${ob['low']:.2f} - ${ob['high']:.2f}")
            print(f"     Volume: {ob['volume']:,.0f}")
            print(f"     Strength: ${ob['strength']:.2f}")
    
    # Fair Value Gaps
    if analysis['fair_value_gaps']:
        print(f"\n🕳️  Fair Value Gaps ({len(analysis['fair_value_gaps'])}):")
        for i, fvg in enumerate(analysis['fair_value_gaps'][-3:], 1):  # Show last 3
            print(f"  {i}. {fvg['type'].upper()} FVG")
            print(f"     Time: {fvg['timestamp']}")
            print(f"     Gap Range: ${fvg['bottom']:.2f} - ${fvg['top']:.2f}")
            print(f"     Gap Size: {fvg['gap_size_pct']:.2f}%")
    
    # Liquidity Pools
    if analysis['liquidity_pools']:
        print(f"\n💧 Liquidity Pools ({len(analysis['liquidity_pools'])}):")
        for i, lp in enumerate(analysis['liquidity_pools'][-3:], 1):  # Show last 3
            print(f"  {i}. {lp['type'].upper()}")
            print(f"     Time: {lp['timestamp']}")
            print(f"     Price: ${lp['price']:.2f}")
            print(f"     Strength: ${lp['strength']:.2f}")


def run_basic_smc_analysis():
    """Run basic SMC analysis on real data."""
    print("=== Basic SMC Analysis with Real Data ===")
    print("Testing core SMC elements without complex indicators")
    
    try:
        # Load real data
        print("\nLoading real Binance data...")
        
        # Load HTF data (4h)
        htf_data = load_real_binance_data('BTCUSDT', '4h')
        
        # Load LTF data (15m)
        ltf_data = load_real_binance_data('BTCUSDT', '15m')
        
        print(f"\nData Summary:")
        print(f"  HTF (4h): {len(htf_data)} bars")
        print(f"  LTF (15m): {len(ltf_data)} bars")
        
        # Analyze HTF market structure
        print(f"\n{'='*50}")
        print("HIGHER TIMEFRAME (4h) ANALYSIS")
        print(f"{'='*50}")
        htf_analysis = analyze_market_structure(htf_data)
        show_detailed_patterns(htf_analysis)
        
        # Analyze LTF market structure
        print(f"\n{'='*50}")
        print("LOWER TIMEFRAME (15m) ANALYSIS")
        print(f"{'='*50}")
        ltf_analysis = analyze_market_structure(ltf_data)
        show_detailed_patterns(ltf_analysis)
        
        # Summary
        print(f"\n{'='*50}")
        print("ANALYSIS SUMMARY")
        print(f"{'='*50}")
        print(f"HTF Trend: {htf_analysis['trend'].upper()}")
        print(f"HTF Patterns: {htf_analysis['total_patterns']}")
        print(f"LTF Patterns: {ltf_analysis['total_patterns']}")
        print(f"Total Analysis: SUCCESS")
        
        return True
        
    except Exception as e:
        print(f"\nError during basic SMC analysis: {e}")
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
        
        # Run the basic SMC analysis
        success = run_basic_smc_analysis()
        
        if success:
            print("\n🎉 Basic SMC Analysis Completed Successfully!")
            print("\n💡 What we tested:")
            print("  - Real Binance BTCUSDT data loading")
            print("  - Core SMC elements detection")
            print("  - Order Blocks identification")
            print("  - Fair Value Gaps detection")
            print("  - Liquidity Pools identification")
            print("  - Market structure analysis")
            print("  - Multi-timeframe analysis (4h + 15m)")
        else:
            print("\n❌ Analysis failed. Check the error messages above.")
        
    except Exception as e:
        print(f"\nError during basic SMC demonstration: {e}")
        import traceback
        traceback.print_exc()
