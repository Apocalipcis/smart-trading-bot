"""
Historical Data Downloader

This module provides functionality to download historical candle data
from Binance USDT-M Futures for backtesting purposes. It supports
multiple timeframes and stores data in Parquet format as specified.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .binance_client import BinanceClient, BinanceConfig
from .validators import BinanceValidator
try:
    from src.storage.files import FileManager
except ImportError:
    from ..storage.files import FileManager


class DataDownloader:
    """
    Historical data downloader for Binance USDT-M Futures.
    
    Downloads candle data and stores it in the specified format:
    data/candles/{exchange}/{symbol}/{timeframe}.parquet
    """
    
    def __init__(self, data_dir: str = None, exchange: str = "binance_futures"):
        # Use environment variable or default based on context
        if data_dir is None:
            import os
            data_dir = os.getenv("DATA_DIR", "data")
        self.data_dir = Path(data_dir)
        self.exchange = exchange
        self.file_manager = FileManager(data_dir)
        self.logger = logging.getLogger(__name__)
        
        # Binance API limits
        self.max_klines_per_request = 1000
        self.rate_limit_delay = 0.1  # 100ms between requests
        
        # Timeframe mappings
        self.timeframe_limits = {
            "1m": {"max_days": 1, "max_klines": 1440},      # 1 day max
            "5m": {"max_days": 5, "max_klines": 1440},      # 5 days max
            "15m": {"max_days": 15, "max_klines": 1440},    # 15 days max
            "30m": {"max_days": 30, "max_klines": 1440},    # 30 days max
            "1h": {"max_days": 30, "max_klines": 720},      # 30 days max
            "4h": {"max_days": 120, "max_klines": 720},     # 120 days max
            "1d": {"max_days": 365, "max_klines": 365},     # 1 year max
        }
    
    async def download_symbol_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Download historical data for a specific symbol and timeframe.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            timeframe: Time interval ('1m', '5m', '15m', '30m', '1h', '4h', '1d')
            start_date: Start date for data download
            end_date: End date for data download
            force_update: Force re-download even if file exists
            
        Returns:
            Dict with download statistics
        """
        self.logger.info(f"Starting download for {symbol} {timeframe} from {start_date} to {end_date}")
        
        # Validate inputs
        if timeframe not in self.timeframe_limits:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Check if data already exists
        file_path = self.file_manager.get_candle_path(self.exchange, symbol, timeframe)
        if file_path.exists() and not force_update:
            self.logger.info(f"Data file already exists: {file_path}")
            return await self._get_existing_data_stats(file_path)
        
        # Create directory structure
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download data
        config = BinanceConfig()
        async with BinanceClient(config) as client:
            candles = await self._download_candles(
                client, symbol, timeframe, start_date, end_date
            )
        
        if not candles:
            raise ValueError(f"No data downloaded for {symbol} {timeframe}")
        
        # Convert to DataFrame and save
        df = self._process_candles(candles, symbol, timeframe)
        await self._save_data(df, file_path)
        
        # Return statistics
        stats = {
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_candles": len(df),
            "file_path": str(file_path),
            "file_size_mb": file_path.stat().st_size / (1024 * 1024),
            "download_time": datetime.now(timezone.utc).isoformat()
        }
        
        self.logger.info(f"Download completed: {stats}")
        return stats
    
    async def download_multiple_symbols(
        self,
        symbols: List[str],
        timeframes: List[str],
        start_date: datetime,
        end_date: datetime,
        force_update: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Download data for multiple symbols and timeframes.
        
        Args:
            symbols: List of trading pair symbols
            timeframes: List of time intervals
            start_date: Start date for data download
            end_date: End date for data download
            force_update: Force re-download even if files exist
            
        Returns:
            List of download statistics for each symbol/timeframe
        """
        results = []
        
        for symbol in symbols:
            for timeframe in timeframes:
                try:
                    stats = await self.download_symbol_data(
                        symbol, timeframe, start_date, end_date, force_update
                    )
                    results.append(stats)
                    
                    # Rate limiting between downloads
                    await asyncio.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    self.logger.error(f"Failed to download {symbol} {timeframe}: {e}")
                    results.append({
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "error": str(e),
                        "status": "failed"
                    })
        
        return results
    
    async def _download_candles(
        self,
        client: BinanceClient,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Download candles in chunks to respect API limits."""
        all_candles = []
        current_start = start_date
        
        while current_start < end_date:
            # Calculate end time for this chunk
            chunk_end = min(
                current_start + timedelta(days=self.timeframe_limits[timeframe]["max_days"]),
                end_date
            )
            
            self.logger.debug(f"Downloading chunk: {current_start} to {chunk_end}")
            
            try:
                # Download chunk
                chunk_candles = await client.get_klines(
                    symbol=symbol,
                    interval=timeframe,
                    start_time=int(current_start.timestamp() * 1000),
                    end_time=int(chunk_end.timestamp() * 1000),
                    limit=self.max_klines_per_request
                )
                
                all_candles.extend(chunk_candles)
                
                # Move to next chunk
                current_start = chunk_end
                
                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                self.logger.error(f"Failed to download chunk {current_start} to {chunk_end}: {e}")
                raise
        
        return all_candles
    
    def _process_candles(
        self, 
        candles: List[Any], 
        symbol: str, 
        timeframe: str
    ) -> pd.DataFrame:
        """Process raw candle data into a DataFrame."""
        if not candles:
            raise ValueError("No candles to process")
        
        # Check if candles are KlineData objects or raw lists
        if hasattr(candles[0], 'open_time'):
            # Handle KlineData objects (from BinanceClient)
            df = pd.DataFrame([{
                'open_time': candle.open_time,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume,
                'close_time': candle.close_time,
                'quote_volume': candle.quote_volume,
                'trades': candle.trades,
                'taker_buy_base': candle.taker_buy_base,
                'taker_buy_quote': candle.taker_buy_quote
            } for candle in candles])
        else:
            # Handle raw list format (legacy support)
            df = pd.DataFrame(candles)
            
            # Rename columns to match specification
            column_mapping = {
                0: 'open_time',
                1: 'open',
                2: 'high',
                3: 'low',
                4: 'close',
                5: 'volume',
                6: 'close_time',
                7: 'quote_volume',
                8: 'trades',
                9: 'taker_buy_base',
                10: 'taker_buy_quote'
            }
            
            df = df.rename(columns=column_mapping)
        
        # Convert data types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_volume', 'taker_buy_base', 'taker_buy_quote']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        integer_columns = ['open_time', 'close_time', 'trades']
        for col in integer_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
        
        # Add datetime column
        df['datetime'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
        
        # Sort by datetime
        df = df.sort_values('datetime').reset_index(drop=True)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['datetime']).reset_index(drop=True)
        
        # Validate data integrity
        self._validate_candle_data(df, symbol, timeframe)
        
        return df
    
    def _validate_candle_data(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """Validate downloaded candle data with improved error handling."""
        if df.empty:
            raise ValueError(f"No data after processing for {symbol} {timeframe}")
        
        # Check for required columns
        required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Check for invalid prices
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            if (df[col] <= 0).any():
                raise ValueError(f"Invalid prices (<=0) found in column: {col}")
        
        # Check for high >= low
        invalid_ohlc = df[df['high'] < df['low']]
        if not invalid_ohlc.empty:
            raise ValueError(f"Invalid OHLC data found: high < low in {len(invalid_ohlc)} rows")
        
        # Check for time gaps with improved handling
        if len(df) > 1:
            time_diffs = df['datetime'].diff()
            expected_interval = self._get_expected_interval(timeframe)
            tolerance = pd.Timedelta(seconds=30)
            
            gaps = time_diffs[time_diffs > expected_interval + tolerance]
            if not gaps.empty:
                self.logger.warning(f"Time gaps detected in {symbol} {timeframe}: {len(gaps)} gaps")
                # Log details about the gaps
                gap_details = []
                for idx, gap in gaps.items():
                    if pd.notna(gap):
                        gap_details.append(f"Gap at {df.loc[idx, 'datetime']}: {gap}")
                if gap_details:
                    self.logger.warning(f"Gap details: {'; '.join(gap_details[:5])}")  # Limit to first 5 gaps
                
                # Check if gaps are too large to be acceptable
                max_acceptable_gap = expected_interval * 10  # Allow gaps up to 10x the expected interval
                large_gaps = gaps[gaps > max_acceptable_gap]
                if not large_gaps.empty:
                    self.logger.error(f"Large time gaps detected in {symbol} {timeframe}: {len(large_gaps)} gaps exceed acceptable threshold")
                    # For large gaps, we might want to raise an error or handle differently
                    if len(large_gaps) > len(df) * 0.1:  # If more than 10% of data has large gaps
                        self.logger.error(f"Too many large gaps in {symbol} {timeframe}, data quality may be poor")
        
        # Check for duplicate timestamps
        duplicates = df[df.duplicated(subset=['datetime'], keep=False)]
        if not duplicates.empty:
            self.logger.warning(f"Duplicate timestamps found in {symbol} {timeframe}: {len(duplicates)} rows")
            # Remove duplicates keeping the first occurrence
            df.drop_duplicates(subset=['datetime'], keep='first', inplace=True)
            self.logger.info(f"Removed {len(duplicates)} duplicate timestamps from {symbol} {timeframe}")
        
        # Check for missing values in critical columns
        critical_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_values = df[critical_columns].isnull().sum()
        if missing_values.any():
            self.logger.warning(f"Missing values found in {symbol} {timeframe}: {missing_values.to_dict()}")
            # Remove rows with missing values in critical columns
            initial_count = len(df)
            df.dropna(subset=critical_columns, inplace=True)
            final_count = len(df)
            if final_count < initial_count:
                self.logger.info(f"Removed {initial_count - final_count} rows with missing values from {symbol} {timeframe}")
        
        # Final validation
        if df.empty:
            raise ValueError(f"After validation and cleaning, no data remains for {symbol} {timeframe}")
        
        self.logger.info(f"Data validation completed for {symbol} {timeframe}: {len(df)} valid candles")
    
    def _get_expected_interval(self, timeframe: str) -> pd.Timedelta:
        """Get expected time interval for a timeframe."""
        interval_map = {
            '1m': pd.Timedelta(minutes=1),
            '5m': pd.Timedelta(minutes=5),
            '15m': pd.Timedelta(minutes=15),
            '30m': pd.Timedelta(minutes=30),
            '1h': pd.Timedelta(hours=1),
            '4h': pd.Timedelta(hours=4),
            '1d': pd.Timedelta(days=1),
        }
        return interval_map.get(timeframe, pd.Timedelta(minutes=1))
    
    async def _save_data(self, df: pd.DataFrame, file_path: Path):
        """Save DataFrame to Parquet file."""
        try:
            # Convert to Arrow table
            table = pa.Table.from_pandas(df)
            
            # Write to Parquet with compression
            pq.write_table(
                table, 
                file_path,
                compression='snappy',
                row_group_size=10000
            )
            
            self.logger.info(f"Data saved to {file_path} ({len(df)} candles)")
            
        except Exception as e:
            self.logger.error(f"Failed to save data to {file_path}: {e}")
            raise
    
    async def _get_existing_data_stats(self, file_path: Path) -> Dict[str, Any]:
        """Get statistics for existing data file."""
        try:
            table = pq.read_table(file_path)
            df = table.to_pandas()
            
            # Handle datetime as index or column
            if df.index.name == 'datetime' or isinstance(df.index, pd.DatetimeIndex):
                start_date = df.index.min()
                end_date = df.index.max()
            elif 'datetime' in df.columns:
                start_date = df['datetime'].min()
                end_date = df['datetime'].max()
            else:
                raise ValueError("No datetime column or index found")
            
            return {
                "symbol": file_path.parent.name,
                "timeframe": file_path.stem,
                "total_candles": len(df),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "file_path": str(file_path),
                "file_size_mb": file_path.stat().st_size / (1024 * 1024),
                "status": "existing"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to read existing data: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_available_data(self) -> Dict[str, Any]:
        """Get information about available historical data."""
        data_info = {}
        
        candles_dir = self.data_dir / "candles" / self.exchange
        
        if not candles_dir.exists():
            return {"message": "No data directory found", "data": {}}
        
        for symbol_dir in candles_dir.iterdir():
            if symbol_dir.is_dir():
                symbol_data = {}
                for file_path in symbol_dir.glob("*.parquet"):
                    timeframe = file_path.stem
                    try:
                        stats = await self._get_existing_data_stats(file_path)
                        symbol_data[timeframe] = stats
                    except Exception as e:
                        symbol_data[timeframe] = {"error": str(e)}
                
                data_info[symbol_dir.name] = symbol_data
        
        return {
            "exchange": self.exchange,
            "data_directory": str(candles_dir),
            "total_symbols": len(data_info),
            "data": data_info
        }


# CLI interface for data downloading
async def download_data_cli():
    """Command-line interface for downloading historical data."""
    import argparse
    import os
    from datetime import datetime, timedelta
    
    parser = argparse.ArgumentParser(description="Download historical data for backtesting")
    parser.add_argument("--symbols", nargs="+", required=True, help="Trading symbols to download")
    parser.add_argument("--timeframes", nargs="+", default=["1h"], 
                       choices=["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
                       help="Timeframes to download")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", default=None, help="Data directory (defaults to DATA_DIR env var or 'data')")
    parser.add_argument("--force", action="store_true", help="Force re-download existing data")
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    
    # Create downloader
    data_dir = args.data_dir or os.getenv("DATA_DIR", "data")
    downloader = DataDownloader(data_dir=data_dir)
    
    # Download data
    results = await downloader.download_multiple_symbols(
        symbols=args.symbols,
        timeframes=args.timeframes,
        start_date=start_date,
        end_date=end_date,
        force_update=args.force
    )
    
    # Print results
    print(f"\nDownload Results:")
    print("=" * 80)
    
    for result in results:
        if "error" in result:
            print(f"❌ {result['symbol']} {result['timeframe']}: {result['error']}")
        else:
            print(f"✅ {result['symbol']} {result['timeframe']}: {result['total_candles']} candles")
    
    # Summary
    successful = len([r for r in results if "error" not in r])
    failed = len([r for r in results if "error" in r])
    
    print(f"\nSummary: {successful} successful, {failed} failed")


if __name__ == "__main__":
    asyncio.run(download_data_cli())
