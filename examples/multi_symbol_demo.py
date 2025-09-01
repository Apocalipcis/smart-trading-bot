#!/usr/bin/env python3
"""
Multi-Symbol SMC Demo

This script tests SMC analysis on multiple trading pairs
to demonstrate the system's versatility.
"""

import sys
import os
import pandas as pd
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
    
    return df


def quick_smc_analysis(df: pd.DataFrame, symbol: str, timeframe: str) -> dict:
    """Quick SMC analysis for a given dataset."""
    print(f"\n📊 {symbol} {timeframe} Analysis:")
    print(f"   Bars: {len(df)}")
    print(f"   Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"   Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    
    # Simple trend detection
    if len(df) >= 20:
        recent_highs = df['high'].tail(20).max()
        recent_lows = df['low'].tail(20).min()
        current_price = df['close'].iloc[-1]
        
        if current_price > (recent_highs + recent_lows) / 2:
            trend = "BULLISH"
        elif current_price < (recent_highs + recent_lows) / 2:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"
    else:
        trend = "INSUFFICIENT_DATA"
    
    print(f"   Trend: {trend}")
    
    # Count potential order blocks (simplified)
    order_blocks = 0
    for i in range(1, len(df)):
        if (df.iloc[i]['close'] > df.iloc[i]['open'] and  # Bullish bar
            df.iloc[i]['volume'] > df['volume'].rolling(20).mean().iloc[i] * 1.5):
            order_blocks += 1
        elif (df.iloc[i]['close'] < df.iloc[i]['open'] and  # Bearish bar
              df.iloc[i]['volume'] > df['volume'].rolling(20).mean().iloc[i] * 1.5):
            order_blocks += 1
    
    print(f"   Potential Order Blocks: {order_blocks}")
    
    return {
        'symbol': symbol,
        'timeframe': timeframe,
        'bars': len(df),
        'trend': trend,
        'order_blocks': order_blocks,
        'price_range': f"${df['low'].min():.2f} - ${df['high'].max():.2f}"
    }


def run_multi_symbol_analysis():
    """Run SMC analysis on multiple symbols."""
    print("=== Multi-Symbol SMC Analysis ===")
    print("Testing SMC system on different trading pairs")
    
    # Define symbols and timeframes to test
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'LINKUSDT']
    timeframes = ['4h', '15m']
    
    results = []
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"ANALYZING {symbol}")
        print(f"{'='*60}")
        
        symbol_results = []
        
        for timeframe in timeframes:
            try:
                # Check if data exists
                data_path = f"../data/candles/binance_futures/{symbol}/{timeframe}.parquet"
                if not os.path.exists(data_path):
                    print(f"❌ No {timeframe} data for {symbol}")
                    continue
                
                # Load and analyze data
                df = load_real_binance_data(symbol, timeframe)
                analysis = quick_smc_analysis(df, symbol, timeframe)
                symbol_results.append(analysis)
                
            except Exception as e:
                print(f"❌ Error analyzing {symbol} {timeframe}: {e}")
        
        if symbol_results:
            results.extend(symbol_results)
            print(f"\n✅ {symbol} analysis completed successfully")
        else:
            print(f"\n❌ {symbol} analysis failed")
    
    # Summary
    print(f"\n{'='*60}")
    print("MULTI-SYMBOL ANALYSIS SUMMARY")
    print(f"{'='*60}")
    
    successful_analyses = len(results)
    total_possible = len(symbols) * len(timeframes)
    
    print(f"Total analyses attempted: {total_possible}")
    print(f"Successful analyses: {successful_analyses}")
    print(f"Success rate: {(successful_analyses/total_possible)*100:.1f}%")
    
    if results:
        print(f"\nDetailed Results:")
        for result in results:
            print(f"  {result['symbol']} {result['timeframe']}: {result['trend']} trend, {result['order_blocks']} order blocks")
    
    return successful_analyses > 0


if __name__ == "__main__":
    try:
        # Check if we have any data
        data_dir = "../data/candles/binance_futures"
        if not os.path.exists(data_dir):
            print("❌ No Binance data found!")
            print("Please ensure you have downloaded data to data/candles/binance_futures/")
            sys.exit(1)
        
        # Run multi-symbol analysis
        success = run_multi_symbol_analysis()
        
        if success:
            print("\n🎉 Multi-Symbol SMC Analysis Completed Successfully!")
            print("\n💡 What we demonstrated:")
            print("  - SMC analysis on multiple trading pairs")
            print("  - Multi-timeframe analysis (4h + 15m)")
            print("  - System versatility across different assets")
            print("  - Real market data processing")
            print("  - Trend detection and pattern counting")
        else:
            print("\n❌ Multi-symbol analysis failed.")
        
    except Exception as e:
        print(f"\nError during multi-symbol demonstration: {e}")
        import traceback
        traceback.print_exc()
