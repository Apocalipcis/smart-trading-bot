#!/usr/bin/env python3
"""
Historical Data Download Demo

This script demonstrates how to download historical candle data
from Binance for backtesting purposes.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add src to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.data.downloader import DataDownloader


async def demo_single_download():
    """Demonstrate downloading data for a single symbol/timeframe."""
    print("=== Single Symbol Download Demo ===")
    
    # Create downloader
    downloader = DataDownloader(data_dir="./data")
    
    # Download BTCUSDT 1h data for the last 7 days
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    try:
        result = await downloader.download_symbol_data(
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date,
            force_update=False
        )
        
        print(f"✅ Download successful!")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Timeframe: {result['timeframe']}")
        print(f"   Candles: {result['total_candles']}")
        print(f"   File size: {result['file_size_mb']:.2f} MB")
        print(f"   Date range: {result['start_date']} to {result['end_date']}")
        
    except Exception as e:
        print(f"❌ Download failed: {e}")


async def demo_multiple_downloads():
    """Demonstrate downloading data for multiple symbols and timeframes."""
    print("\n=== Multiple Downloads Demo ===")
    
    # Create downloader
    downloader = DataDownloader(data_dir="./data")
    
    # Define symbols and timeframes
    symbols = ["BTCUSDT", "ETHUSDT"]
    timeframes = ["1h", "4h"]
    
    # Download last 30 days of data
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    try:
        results = await downloader.download_multiple_symbols(
            symbols=symbols,
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date,
            force_update=False
        )
        
        print(f"✅ Downloaded {len(results)} datasets:")
        for result in results:
            if "error" in result:
                print(f"   ❌ {result['symbol']} {result['timeframe']}: {result['error']}")
            else:
                print(f"   ✅ {result['symbol']} {result['timeframe']}: {result['total_candles']} candles")
        
    except Exception as e:
        print(f"❌ Downloads failed: {e}")


async def demo_data_inventory():
    """Demonstrate checking available data."""
    print("\n=== Data Inventory Demo ===")
    
    # Create downloader
    downloader = DataDownloader(data_dir="./data")
    
    try:
        inventory = await downloader.get_available_data()
        
        print(f"📊 Data Inventory:")
        print(f"   Exchange: {inventory['exchange']}")
        print(f"   Directory: {inventory['data_directory']}")
        print(f"   Total symbols: {inventory['total_symbols']}")
        
        if inventory['data']:
            print(f"\n   Available data:")
            for symbol, timeframes in inventory['data'].items():
                print(f"     {symbol}:")
                for tf, info in timeframes.items():
                    if "error" in info:
                        print(f"       ❌ {tf}: {info['error']}")
                    else:
                        print(f"       ✅ {tf}: {info['total_candles']} candles ({info['file_size_mb']:.2f} MB)")
        else:
            print(f"   No data found")
        
    except Exception as e:
        print(f"❌ Failed to get inventory: {e}")


async def demo_cli_usage():
    """Demonstrate CLI usage."""
    print("\n=== CLI Usage Demo ===")
    
    print("Command-line usage examples:")
    print()
    print("1. Download BTCUSDT 1h data for last 7 days:")
    print("   python -m src.data.downloader --symbols BTCUSDT --timeframes 1h --start-date 2024-01-01 --end-date 2024-01-07")
    print()
    print("2. Download multiple symbols and timeframes:")
    print("   python -m src.data.downloader --symbols BTCUSDT ETHUSDT --timeframes 1h 4h --start-date 2024-01-01 --end-date 2024-01-31")
    print()
    print("3. Force re-download existing data:")
    print("   python -m src.data.downloader --symbols BTCUSDT --timeframes 1h --start-date 2024-01-01 --end-date 2024-01-07 --force")
    print()
    print("4. Use custom data directory:")
    print("   python -m src.data.downloader --symbols BTCUSDT --timeframes 1h --start-date 2024-01-01 --end-date 2024-01-07 --data-dir /custom/data/path")


async def main():
    """Main demonstration function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Historical Data Download Demonstration")
    print("=" * 50)
    
    # Run demonstrations
    await demo_single_download()
    await demo_multiple_downloads()
    await demo_data_inventory()
    await demo_cli_usage()
    
    print("\n" + "=" * 50)
    print("Demonstration complete!")
    print("\nNext steps:")
    print("1. Download data for your desired symbols and timeframes")
    print("2. Run backtests using the downloaded data")
    print("3. Use the web interface to view and manage your data")


if __name__ == "__main__":
    asyncio.run(main())
