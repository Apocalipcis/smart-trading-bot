#!/usr/bin/env python3
"""
Data Preprocessor for ETHUSDT SMC Strategy Debugging

This module handles data formatting and preparation for Backtrader compatibility.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Tuple, Optional
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def load_eth_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and preprocess ETHUSDT data for both timeframes.
    
    Returns:
        Tuple of (htf_data, ltf_data) properly formatted for Backtrader
    """
    print("Loading ETHUSDT data...")
    
    # Load raw data
    htf_path = 'data/candles/binance_futures/ETHUSDT/4h.parquet'
    ltf_path = 'data/candles/binance_futures/ETHUSDT/15m.parquet'
    
    htf_raw = pd.read_parquet(htf_path)
    ltf_raw = pd.read_parquet(ltf_path)
    
    print(f"4H data: {len(htf_raw)} bars")
    print(f"15m data: {len(ltf_raw)} bars")
    
    # Preprocess HTF data (4H)
    htf_data = preprocess_dataframe(htf_raw, '4H')
    
    # Preprocess LTF data (15m)
    ltf_data = preprocess_dataframe(ltf_raw, '15m')
    
    # Ensure data alignment
    htf_data, ltf_data = align_timeframes(htf_data, ltf_data)
    
    print(f"Processed 4H data: {len(htf_data)} bars")
    print(f"Processed 15m data: {len(ltf_data)} bars")
    
    return htf_data, ltf_data

def preprocess_dataframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    Preprocess dataframe for Backtrader compatibility.
    
    Args:
        df: Raw dataframe from parquet
        timeframe: Timeframe string for logging
        
    Returns:
        Processed dataframe ready for Backtrader
    """
    print(f"Preprocessing {timeframe} data...")
    
    # Create a copy to avoid modifying original
    processed = df.copy()
    
    # Convert datetime column to proper datetime index
    if 'datetime' in processed.columns:
        processed['datetime'] = pd.to_datetime(processed['datetime'])
        processed.set_index('datetime', inplace=True)
    elif 'open_time' in processed.columns:
        # Convert timestamp to datetime
        processed['datetime'] = pd.to_datetime(processed['open_time'], unit='ms')
        processed.set_index('datetime', inplace=True)
    
    # Ensure required columns exist and are properly named
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    
    # Check if we need to rename columns
    column_mapping = {}
    for col in required_columns:
        if col not in processed.columns:
            # Try to find similar columns
            if col == 'volume' and 'quote_volume' in processed.columns:
                column_mapping['quote_volume'] = 'volume'
            elif col == 'volume' and 'taker_buy_base' in processed.columns:
                column_mapping['taker_buy_base'] = 'volume'
    
    if column_mapping:
        processed.rename(columns=column_mapping, inplace=True)
    
    # Select only required columns
    processed = processed[required_columns].copy()
    
    # Ensure data types are correct
    for col in ['open', 'high', 'low', 'close']:
        processed[col] = pd.to_numeric(processed[col], errors='coerce')
    
    processed['volume'] = pd.to_numeric(processed['volume'], errors='coerce')
    
    # Remove any rows with NaN values
    initial_len = len(processed)
    processed.dropna(inplace=True)
    final_len = len(processed)
    
    if initial_len != final_len:
        print(f"  Removed {initial_len - final_len} rows with NaN values")
    
    # Sort by datetime index
    processed.sort_index(inplace=True)
    
    # Verify data quality
    print(f"  {timeframe} data quality check:")
    print(f"    Price range: ${processed['low'].min():.2f} - ${processed['high'].max():.2f}")
    print(f"    Volume range: {processed['volume'].min():.2e} - {processed['volume'].max():.2e}")
    print(f"    Date range: {processed.index.min()} to {processed.index.max()}")
    
    return processed

def align_timeframes(htf_data: pd.DataFrame, ltf_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ensure HTF and LTF data are properly aligned for strategy execution.
    
    Args:
        htf_data: Higher timeframe data (4H)
        ltf_data: Lower timeframe data (15m)
        
    Returns:
        Tuple of aligned (htf_data, ltf_data)
    """
    print("Aligning timeframes...")
    
    # Find common date range
    htf_start = htf_data.index.min()
    htf_end = htf_data.index.max()
    ltf_start = ltf_data.index.min()
    ltf_end = ltf_data.index.max()
    
    print(f"  4H range: {htf_start} to {htf_end}")
    print(f"  15m range: {ltf_start} to {ltf_end}")
    
    # Use the more restrictive range
    start_date = max(htf_start, ltf_start)
    end_date = min(htf_end, ltf_end)
    
    print(f"  Common range: {start_date} to {end_date}")
    
    # Filter data to common range
    htf_aligned = htf_data[(htf_data.index >= start_date) & (htf_data.index <= end_date)].copy()
    ltf_aligned = ltf_data[(ltf_data.index >= start_date) & (ltf_data.index <= end_date)].copy()
    
    print(f"  Aligned 4H: {len(htf_aligned)} bars")
    print(f"  Aligned 15m: {len(ltf_aligned)} bars")
    
    return htf_aligned, ltf_aligned

def validate_data_quality(htf_data: pd.DataFrame, ltf_data: pd.DataFrame) -> bool:
    """
    Validate that data meets minimum requirements for strategy execution.
    
    Args:
        htf_data: Higher timeframe data
        ltf_data: Lower timeframe data
        
    Returns:
        True if data is valid, False otherwise
    """
    print("Validating data quality...")
    
    # Check minimum data requirements
    min_htf_bars = 50  # Strategy needs at least 50 HTF bars
    min_ltf_bars = 20  # Strategy needs at least 20 LTF bars
    
    if len(htf_data) < min_htf_bars:
        print(f"  ERROR: Insufficient HTF data. Need {min_htf_bars}, have {len(htf_data)}")
        return False
    
    if len(ltf_data) < min_ltf_bars:
        print(f"  ERROR: Insufficient LTF data. Need {min_ltf_bars}, have {len(ltf_data)}")
        return False
    
    # Check for price anomalies
    for name, data in [('4H', htf_data), ('15m', ltf_data)]:
        # Check for zero or negative prices
        if (data[['open', 'high', 'low', 'close']] <= 0).any().any():
            print(f"  ERROR: {name} data contains zero or negative prices")
            return False
        
        # Check for extreme price movements (>50% in one bar)
        price_changes = abs(data['close'] - data['open']) / data['open']
        if (price_changes > 0.5).any():
            print(f"  WARNING: {name} data contains extreme price movements (>50%)")
        
        # Check for zero volume
        zero_volume_bars = (data['volume'] == 0).sum()
        if zero_volume_bars > 0:
            print(f"  WARNING: {name} data has {zero_volume_bars} bars with zero volume")
    
    print("  Data quality validation passed")
    return True

def create_backtrader_feeds(htf_data: pd.DataFrame, ltf_data: pd.DataFrame):
    """
    Create Backtrader data feeds from processed dataframes.
    
    Args:
        htf_data: Processed HTF dataframe
        ltf_data: Processed LTF dataframe
        
    Returns:
        Tuple of (htf_feed, ltf_feed) Backtrader data feeds
    """
    try:
        import backtrader as bt
        
        print("Creating Backtrader data feeds...")
        
        # Create HTF feed
        htf_feed = bt.feeds.PandasData(
            dataname=htf_data,
            datetime=None,  # Use index as datetime
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            name='HTF'
        )
        
        # Create LTF feed
        ltf_feed = bt.feeds.PandasData(
            dataname=ltf_data,
            datetime=None,  # Use index as datetime
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            name='LTF'
        )
        
        print("  Backtrader feeds created successfully")
        return htf_feed, ltf_feed
        
    except ImportError:
        print("  ERROR: Backtrader not available")
        return None, None

if __name__ == "__main__":
    # Test data loading and preprocessing
    print("=== ETHUSDT Data Preprocessing Test ===\n")
    
    try:
        htf_data, ltf_data = load_eth_data()
        
        if validate_data_quality(htf_data, ltf_data):
            print("\n✅ Data preprocessing successful!")
            
            # Try to create Backtrader feeds
            htf_feed, ltf_feed = create_backtrader_feeds(htf_data, ltf_data)
            
            if htf_feed and ltf_feed:
                print("✅ Backtrader feeds created successfully!")
            else:
                print("❌ Failed to create Backtrader feeds")
        else:
            print("\n❌ Data quality validation failed!")
            
    except Exception as e:
        print(f"\n❌ Error during data preprocessing: {e}")
        import traceback
        traceback.print_exc()
