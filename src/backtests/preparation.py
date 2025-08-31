"""
Data preparation module for backtests.

This module handles automatic preparation of candle data before backtest execution,
ensuring all required data is available in the correct format and date ranges.
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import pyarrow.parquet as pq

try:
    from src.data.downloader import DataDownloader
    from src.data.validators import BinanceValidator
    from src.data.binance_client import BinanceClient, BinanceConfig
except ImportError:
    from ..data.downloader import DataDownloader
    from ..data.validators import BinanceValidator
    from ..data.binance_client import BinanceClient, BinanceConfig

logger = logging.getLogger(__name__)


class DataPreparationError(Exception):
    """Exception raised when data preparation fails."""
    pass


class BacktestDataPreparer:
    """Handles automatic preparation of backtest data."""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            import os
            data_dir = os.getenv("DATA_DIR", "data")
        self.data_dir = Path(data_dir)
        self.downloader = DataDownloader(data_dir)
        self.validator = BinanceValidator()
        
        # Supported timeframes for validation
        self.supported_timeframes = [
            '1m', '3m', '5m', '15m', '30m',
            '1h', '2h', '4h', '6h', '8h', '12h',
            '1d', '3d', '1w', '1M'
        ]
    
    def _validate_timeframes(self, timeframes: List[str]) -> None:
        """Validate that all requested timeframes are supported."""
        invalid_timeframes = [tf for tf in timeframes if tf not in self.supported_timeframes]
        if invalid_timeframes:
            raise DataPreparationError(
                f"Unsupported timeframes: {invalid_timeframes}. "
                f"Supported: {', '.join(self.supported_timeframes)}"
            )
    
    def _validate_date_range(self, start_date: datetime, end_date: datetime) -> None:
        """Validate the requested date range."""
        # Ensure both dates are timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        if start_date >= end_date:
            raise DataPreparationError("Start date must be before end date")
        
        # Check if dates are in the future
        now = datetime.now(timezone.utc)
        if start_date > now or end_date > now:
            raise DataPreparationError("Cannot request data from the future")
    
    def _get_parquet_file_path(self, symbol: str, timeframe: str) -> Path:
        """Get the expected Parquet file path for a symbol/timeframe combination."""
        return self.data_dir / 'candles' / 'binance_futures' / symbol / f"{timeframe}.parquet"
    
    def _check_data_coverage(
        self, 
        file_path: Path, 
        start_date: datetime, 
        end_date: datetime
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if existing Parquet file covers the requested date range.
        
        Returns:
            Tuple of (is_covered, coverage_info)
        """
        if not file_path.exists():
            return False, None
        
        try:
            # Read Parquet file metadata to check date range
            table = pq.read_table(file_path)
            df = table.to_pandas()
            
            if len(df) == 0:
                return False, None
            
            # Determine datetime column or index
            datetime_col = None
            if 'datetime' in df.columns:
                datetime_col = 'datetime'
            elif 'open_time' in df.columns:
                # Convert timestamp to datetime
                df['datetime'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
                datetime_col = 'datetime'
            elif df.index.name == 'datetime' or isinstance(df.index, pd.DatetimeIndex):
                # Datetime is the index
                datetime_col = 'index'
            
            if datetime_col is None:
                logger.warning(f"No datetime column or index found in {file_path}")
                return False, None
            
            # Get datetime values
            if datetime_col == 'index':
                datetime_values = df.index
            else:
                # Convert to datetime if needed
                if not pd.api.types.is_datetime64_any_dtype(df[datetime_col]):
                    df[datetime_col] = pd.to_datetime(df[datetime_col])
                datetime_values = df[datetime_col]
            
            # Sort by datetime
            df_sorted = df.sort_index() if datetime_col == 'index' else df.sort_values(datetime_col)
            
            # Check coverage
            file_start = datetime_values.min()
            file_end = datetime_values.max()
            
            # Ensure all dates are timezone-aware for comparison
            # Convert naive dates to UTC if needed
            if start_date.tzinfo is None:
                start_date_utc = start_date.replace(tzinfo=timezone.utc)
            else:
                start_date_utc = start_date
                
            if end_date.tzinfo is None:
                end_date_utc = end_date.replace(tzinfo=timezone.utc)
            else:
                end_date_utc = end_date
            
            # Ensure file dates are also timezone-aware
            if file_start.tzinfo is None:
                file_start = file_start.replace(tzinfo=timezone.utc)
            if file_end.tzinfo is None:
                file_end = file_end.replace(tzinfo=timezone.utc)
            
            # Add some buffer for data completeness
            buffer = pd.Timedelta(hours=1)
            is_covered = (file_start <= start_date_utc + buffer) and (file_end >= end_date_utc - buffer)
            
            coverage_info = {
                "file_start": file_start,
                "file_end": file_end,
                "requested_start": start_date_utc,
                "requested_end": end_date_utc,
                "total_candles": len(df),
                "file_size_mb": file_path.stat().st_size / (1024 * 1024)
            }
            
            return is_covered, coverage_info
            
        except Exception as e:
            logger.warning(f"Error checking data coverage for {file_path}: {e}")
            return False, None
    
    async def prepare_backtest_data(
        self,
        symbol: str,
        timeframes: List[str],
        start_date: datetime,
        end_date: datetime,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Prepare all required data for a backtest.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            timeframes: List of timeframes to prepare
            start_date: Start date for data
            end_date: End date for data
            force_update: Force re-download even if data exists
            
        Returns:
            Dict with preparation summary
        """
        logger.info(f"Preparing backtest data for {symbol} timeframes: {timeframes}")
        
        # Validate inputs
        self._validate_timeframes(timeframes)
        self._validate_date_range(start_date, end_date)
        
        # Ensure symbol is uppercase
        symbol = symbol.upper()
        
        preparation_summary = {
            "symbol": symbol,
            "timeframes": timeframes,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "force_update": force_update,
            "preparation_time": datetime.now(timezone.utc).isoformat(),
            "results": {},
            "errors": [],
            "total_files_checked": 0,
            "total_files_downloaded": 0,
            "total_files_reused": 0
        }
        
        # Process each timeframe
        for timeframe in timeframes:
            try:
                result = await self._prepare_timeframe_data(
                    symbol, timeframe, start_date, end_date, force_update
                )
                preparation_summary["results"][timeframe] = result
                preparation_summary["total_files_checked"] += 1
                
                if result["action"] == "downloaded":
                    preparation_summary["total_files_downloaded"] += 1
                elif result["action"] == "reused":
                    preparation_summary["total_files_reused"] += 1
                    
            except Exception as e:
                error_msg = f"Failed to prepare {timeframe} data: {str(e)}"
                logger.error(error_msg)
                preparation_summary["errors"].append(error_msg)
                preparation_summary["results"][timeframe] = {
                    "action": "failed",
                    "error": str(e)
                }
                preparation_summary["total_files_checked"] += 1
        
        # Log summary
        logger.info(
            f"Data preparation completed for {symbol}: "
            f"{preparation_summary['total_files_downloaded']} downloaded, "
            f"{preparation_summary['total_files_reused']} reused, "
            f"{len(preparation_summary['errors'])} errors"
        )
        
        return preparation_summary
    
    async def _prepare_timeframe_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        force_update: bool
    ) -> Dict[str, Any]:
        """Prepare data for a specific timeframe with improved error handling."""
        file_path = self._get_parquet_file_path(symbol, timeframe)
        
        try:
            # Check if we need to download data
            if not force_update:
                is_covered, coverage_info = self._check_data_coverage(file_path, start_date, end_date)
                if is_covered:
                    logger.info(f"Reusing existing data for {symbol} {timeframe}: {coverage_info}")
                    return {
                        "action": "reused",
                        "file_path": str(file_path),
                        "coverage_info": coverage_info
                    }
            
            # Download data
            logger.info(f"Downloading data for {symbol} {timeframe} from {start_date} to {end_date}")
            download_result = await self.downloader.download_symbol_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                force_update=force_update
            )
            
            # Validate download result
            if not download_result or "error" in download_result:
                error_msg = f"Download failed for {symbol} {timeframe}: {download_result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise DataPreparationError(error_msg)
            
            logger.info(f"Successfully downloaded data for {symbol} {timeframe}: {download_result.get('total_candles', 0)} candles")
            
            return {
                "action": "downloaded",
                "download_result": download_result,
                "file_path": download_result["file_path"]
            }
            
        except Exception as e:
            error_msg = f"Failed to prepare {timeframe} data for {symbol}: {str(e)}"
            logger.error(error_msg)
            raise DataPreparationError(error_msg)
    
    async def prepare_multiple_symbols_data(
        self,
        symbols: List[str],
        timeframes: List[str],
        start_date: datetime,
        end_date: datetime,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Prepare data for multiple symbols and timeframes.
        
        Args:
            symbols: List of trading pair symbols
            timeframes: List of timeframes to prepare
            start_date: Start date for data
            end_date: End date for data
            force_update: Force re-download even if data exists
            
        Returns:
            Dict with preparation summary for all symbols
        """
        logger.info(f"Preparing data for {len(symbols)} symbols with {len(timeframes)} timeframes")
        
        overall_summary = {
            "symbols": symbols,
            "timeframes": timeframes,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "force_update": force_update,
            "preparation_time": datetime.now(timezone.utc).isoformat(),
            "symbol_results": {},
            "total_symbols": len(symbols),
            "successful_symbols": 0,
            "failed_symbols": 0
        }
        
        # Process each symbol
        for symbol in symbols:
            try:
                symbol_result = await self.prepare_backtest_data(
                    symbol, timeframes, start_date, end_date, force_update
                )
                overall_summary["symbol_results"][symbol] = symbol_result
                overall_summary["successful_symbols"] += 1
                
            except Exception as e:
                error_msg = f"Failed to prepare data for {symbol}: {str(e)}"
                logger.error(error_msg)
                overall_summary["symbol_results"][symbol] = {
                    "error": str(e),
                    "status": "failed"
                }
                overall_summary["failed_symbols"] += 1
        
        logger.info(
            f"Multi-symbol preparation completed: "
            f"{overall_summary['successful_symbols']} successful, "
            f"{overall_summary['failed_symbols']} failed"
        )
        
        return overall_summary


# Convenience function for direct use
async def prepare_backtest_data(
    symbol: str,
    timeframes: List[str],
    start_date: datetime,
    end_date: datetime,
    force_update: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to prepare backtest data.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        timeframes: List of timeframes to prepare
        start_date: Start date for data
        end_date: End date for data
        force_update: Force re-download even if data exists
        
    Returns:
        Dict with preparation summary
    """
    preparer = BacktestDataPreparer()
    return await preparer.prepare_backtest_data(
        symbol, timeframes, start_date, end_date, force_update
    )
