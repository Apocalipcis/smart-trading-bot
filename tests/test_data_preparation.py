"""
Unit tests for the data preparation module.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.backtests.preparation import (
    BacktestDataPreparer, 
    DataPreparationError, 
    prepare_backtest_data
)
from src.data.downloader import DataDownloader


class TestBacktestDataPreparer:
    """Test the BacktestDataPreparer class."""
    
    @pytest.fixture
    def preparer(self, tmp_path):
        """Create a BacktestDataPreparer instance for testing."""
        return BacktestDataPreparer(str(tmp_path))
    
    @pytest.fixture
    def sample_dates(self):
        """Sample date range for testing."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
        return start_date, end_date
    
    def test_init(self, tmp_path):
        """Test BacktestDataPreparer initialization."""
        preparer = BacktestDataPreparer(str(tmp_path))
        assert preparer.data_dir == Path(tmp_path)
        assert isinstance(preparer.downloader, DataDownloader)
        assert isinstance(preparer.validator, type(preparer.validator))
        assert len(preparer.supported_timeframes) > 0
    
    def test_validate_timeframes_valid(self, preparer):
        """Test timeframe validation with valid timeframes."""
        valid_timeframes = ['1m', '5m', '1h', '4h', '1d']
        preparer._validate_timeframes(valid_timeframes)  # Should not raise
    
    def test_validate_timeframes_invalid(self, preparer):
        """Test timeframe validation with invalid timeframes."""
        invalid_timeframes = ['1m', 'invalid', '5m']
        with pytest.raises(DataPreparationError, match="Unsupported timeframes"):
            preparer._validate_timeframes(invalid_timeframes)
    
    def test_validate_date_range_valid(self, preparer, sample_dates):
        """Test date range validation with valid dates."""
        start_date, end_date = sample_dates
        preparer._validate_date_range(start_date, end_date)  # Should not raise
    
    def test_validate_date_range_invalid_order(self, preparer, sample_dates):
        """Test date range validation with invalid date order."""
        start_date, end_date = sample_dates
        with pytest.raises(DataPreparationError, match="Start date must be before end date"):
            preparer._validate_date_range(end_date, start_date)
    
    def test_validate_date_range_future_dates(self, preparer):
        """Test date range validation with future dates."""
        future_start = datetime.now(timezone.utc) + timedelta(days=1)
        future_end = datetime.now(timezone.utc) + timedelta(days=2)
        with pytest.raises(DataPreparationError, match="Cannot request data from the future"):
            preparer._validate_date_range(future_start, future_end)
    
    def test_get_parquet_file_path(self, preparer):
        """Test parquet file path construction."""
        symbol = "BTCUSDT"
        timeframe = "1h"
        expected_path = preparer.data_dir / 'candles' / 'binance_futures' / symbol / f"{timeframe}.parquet"
        actual_path = preparer._get_parquet_file_path(symbol, timeframe)
        assert actual_path == expected_path
    
    def test_check_data_coverage_file_not_exists(self, preparer, sample_dates):
        """Test data coverage check when file doesn't exist."""
        start_date, end_date = sample_dates
        file_path = Path("/nonexistent/file.parquet")
        
        is_covered, coverage_info = preparer._check_data_coverage(file_path, start_date, end_date)
        assert not is_covered
        assert coverage_info is None
    
    @patch('pyarrow.parquet.read_table')
    def test_check_data_coverage_file_exists_covered(self, mock_read_table, preparer, sample_dates, tmp_path):
        """Test data coverage check when file exists and covers the requested range."""
        start_date, end_date = sample_dates
        
        # Create a mock DataFrame with datetime column
        dates = pd.date_range(start_date - timedelta(days=1), end_date + timedelta(days=1), freq='D')
        mock_df = pd.DataFrame({
            'datetime': dates,
            'open': [100 + i for i in range(len(dates))],
            'high': [101 + i for i in range(len(dates))],
            'low': [99 + i for i in range(len(dates))],
            'close': [101 + i for i in range(len(dates))],
            'volume': [1000 + i*100 for i in range(len(dates))]
        })
        
        # Mock the parquet reading
        mock_table = Mock()
        mock_table.to_pandas.return_value = mock_df
        mock_read_table.return_value = mock_table
        
        file_path = tmp_path / "test.parquet"
        file_path.touch()
        
        is_covered, coverage_info = preparer._check_data_coverage(file_path, start_date, end_date)
        
        assert is_covered
        assert coverage_info is not None
        assert coverage_info['total_candles'] == 33  # 33 days from start_date-1 to end_date+1
    
    @patch('pyarrow.parquet.read_table')
    def test_check_data_coverage_file_exists_not_covered(self, mock_read_table, preparer, sample_dates, tmp_path):
        """Test data coverage check when file exists but doesn't cover the requested range."""
        start_date, end_date = sample_dates
        
        # Create a mock DataFrame with limited date range
        dates = pd.date_range(start_date + timedelta(days=15), start_date + timedelta(days=16), freq='D')
        mock_df = pd.DataFrame({
            'datetime': dates,
            'open': [100 + i for i in range(len(dates))],
            'high': [101 + i for i in range(len(dates))],
            'low': [99 + i for i in range(len(dates))],
            'close': [101 + i for i in range(len(dates))],
            'volume': [1000 + i*100 for i in range(len(dates))]
        })
        
        # Mock the parquet reading
        mock_table = Mock()
        mock_table.to_pandas.return_value = mock_df
        mock_read_table.return_value = mock_table
        
        file_path = tmp_path / "test.parquet"
        file_path.touch()
        
        is_covered, coverage_info = preparer._check_data_coverage(file_path, start_date, end_date)
        
        assert not is_covered
        assert coverage_info is not None
    
    @patch('pyarrow.parquet.read_table')
    def test_check_data_coverage_with_open_time_column(self, mock_read_table, preparer, sample_dates, tmp_path):
        """Test data coverage check with open_time column (timestamp format)."""
        start_date, end_date = sample_dates
        
        # Create a mock DataFrame with open_time column
        mock_df = pd.DataFrame({
            'open_time': [
                int((start_date - timedelta(days=1)).timestamp() * 1000),
                int(start_date.timestamp() * 1000),
                int(end_date.timestamp() * 1000),
                int((end_date + timedelta(days=1)).timestamp() * 1000)
            ],
            'open': [100, 101, 102, 103],
            'high': [101, 102, 103, 104],
            'low': [99, 100, 101, 102],
            'close': [101, 102, 103, 104],
            'volume': [1000, 1100, 1200, 1300]
        })
        
        # Mock the parquet reading
        mock_table = Mock()
        mock_table.to_pandas.return_value = mock_df
        mock_read_table.return_value = mock_table
        
        file_path = tmp_path / "test.parquet"
        file_path.touch()
        
        is_covered, coverage_info = preparer._check_data_coverage(file_path, start_date, end_date)
        
        assert is_covered
        assert coverage_info is not None
        assert coverage_info['total_candles'] == 4
    
    @patch('pyarrow.parquet.read_table')
    def test_check_data_coverage_error_handling(self, mock_read_table, preparer, sample_dates, tmp_path):
        """Test data coverage check error handling."""
        start_date, end_date = sample_dates
        
        # Mock the parquet reading to raise an exception
        mock_read_table.side_effect = Exception("Test error")
        
        file_path = tmp_path / "test.parquet"
        file_path.touch()
        
        is_covered, coverage_info = preparer._check_data_coverage(file_path, start_date, end_date)
        
        assert not is_covered
        assert coverage_info is None
    
    @pytest.mark.asyncio
    async def test_prepare_timeframe_data_reuse_existing(self, preparer, sample_dates, tmp_path):
        """Test preparing timeframe data when file already exists and covers the range."""
        start_date, end_date = sample_dates
        symbol = "BTCUSDT"
        timeframe = "1h"
        
        # Create a mock file that covers the requested range
        file_path = preparer._get_parquet_file_path(symbol, timeframe)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create sample data
        dates = pd.date_range(start_date - timedelta(days=1), end_date + timedelta(days=1), freq='D')
        sample_data = pd.DataFrame({
            'datetime': dates,
            'open': [100 + i for i in range(len(dates))],
            'high': [101 + i for i in range(len(dates))],
            'low': [99 + i for i in range(len(dates))],
            'close': [101 + i for i in range(len(dates))],
            'volume': [1000 + i*100 for i in range(len(dates))]
        })
        
        # Save as parquet
        table = pa.Table.from_pandas(sample_data)
        pq.write_table(table, file_path)
        
        # Test preparation
        result = await preparer._prepare_timeframe_data(symbol, timeframe, start_date, end_date, False)
        
        assert result["action"] == "reused"
        assert "file_path" in result
        assert "coverage_info" in result
    
    @pytest.mark.asyncio
    async def test_prepare_timeframe_data_download_new(self, preparer, sample_dates):
        """Test preparing timeframe data when file doesn't exist."""
        start_date, end_date = sample_dates
        symbol = "BTCUSDT"
        timeframe = "1h"
        
        # Mock the downloader to return success
        mock_download_result = {
            "file_path": f"/data/candles/binance_futures/{symbol}/{timeframe}.parquet",
            "total_candles": 100
        }
        
        with patch.object(preparer.downloader, 'download_symbol_data', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = mock_download_result
            
            result = await preparer._prepare_timeframe_data(symbol, timeframe, start_date, end_date, False)
            
            assert result["action"] == "downloaded"
            assert result["download_result"] == mock_download_result
            mock_download.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prepare_timeframe_data_download_error(self, preparer, sample_dates):
        """Test preparing timeframe data when download fails."""
        start_date, end_date = sample_dates
        symbol = "BTCUSDT"
        timeframe = "1h"
        
        # Mock the downloader to raise an exception
        with patch.object(preparer.downloader, 'download_symbol_data', new_callable=AsyncMock) as mock_download:
            mock_download.side_effect = Exception("Download failed")
            
            with pytest.raises(DataPreparationError, match="Failed to prepare 1h data for BTCUSDT: Download failed"):
                await preparer._prepare_timeframe_data(symbol, timeframe, start_date, end_date, False)
    
    @pytest.mark.asyncio
    async def test_prepare_backtest_data_success(self, preparer, sample_dates):
        """Test successful backtest data preparation."""
        start_date, end_date = sample_dates
        symbol = "BTCUSDT"
        timeframes = ["1h", "4h"]
        
        # Mock the timeframe preparation
        with patch.object(preparer, '_prepare_timeframe_data', new_callable=AsyncMock) as mock_prepare:
            mock_prepare.side_effect = [
                {"action": "reused", "file_path": "/path/to/1h.parquet"},
                {"action": "downloaded", "file_path": "/path/to/4h.parquet"}
            ]
            
            result = await preparer.prepare_backtest_data(symbol, timeframes, start_date, end_date)
            
            assert result["symbol"] == symbol.upper()
            assert result["timeframes"] == timeframes
            assert result["total_files_checked"] == 2
            assert result["total_files_downloaded"] == 1
            assert result["total_files_reused"] == 1
            assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_prepare_backtest_data_with_errors(self, preparer, sample_dates):
        """Test backtest data preparation with some errors."""
        start_date, end_date = sample_dates
        symbol = "BTCUSDT"
        timeframes = ["1h", "4h"]
        
        # Mock the timeframe preparation with one success and one failure
        with patch.object(preparer, '_prepare_timeframe_data', new_callable=AsyncMock) as mock_prepare:
            mock_prepare.side_effect = [
                {"action": "reused", "file_path": "/path/to/1h.parquet"},
                Exception("Failed to prepare 4h data")
            ]
            
            result = await preparer.prepare_backtest_data(symbol, timeframes, start_date, end_date)
            
            # The second timeframe will fail, so we'll have 1 success and 1 error
            assert result["total_files_checked"] == 2
            assert result["total_files_downloaded"] == 0
            assert result["total_files_reused"] == 1
            assert len(result["errors"]) == 1
            assert "Failed to prepare 4h data" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_prepare_multiple_symbols_data(self, preparer, sample_dates):
        """Test preparing data for multiple symbols."""
        start_date, end_date = sample_dates
        symbols = ["BTCUSDT", "ETHUSDT"]
        timeframes = ["1h"]
        
        # Mock the symbol preparation
        with patch.object(preparer, 'prepare_backtest_data', new_callable=AsyncMock) as mock_prepare:
            mock_prepare.side_effect = [
                {
                    "symbol": "BTCUSDT",
                    "total_files_downloaded": 1,
                    "total_files_reused": 0
                },
                {
                    "symbol": "ETHUSDT",
                    "total_files_downloaded": 0,
                    "total_files_reused": 1
                }
            ]
            
            result = await preparer.prepare_multiple_symbols_data(symbols, timeframes, start_date, end_date)
            
            assert result["total_symbols"] == 2
            assert result["successful_symbols"] == 2
            assert result["failed_symbols"] == 0
            assert len(result["symbol_results"]) == 2


class TestPrepareBacktestDataFunction:
    """Test the convenience function prepare_backtest_data."""
    
    @pytest.mark.asyncio
    async def test_prepare_backtest_data_function(self, sample_dates):
        """Test the convenience function."""
        start_date, end_date = sample_dates
        symbol = "BTCUSDT"
        timeframes = ["1h"]
        
        with patch('src.backtests.preparation.BacktestDataPreparer') as mock_preparer_class:
            mock_preparer = Mock()
            mock_preparer_class.return_value = mock_preparer
            
            mock_preparer.prepare_backtest_data = AsyncMock(return_value={"status": "success"})
            
            result = await prepare_backtest_data(symbol, timeframes, start_date, end_date)
            
            assert result["status"] == "success"
            mock_preparer.prepare_backtest_data.assert_called_once_with(
                symbol, timeframes, start_date, end_date, False
            )


class TestDataPreparationError:
    """Test the DataPreparationError exception."""
    
    def test_data_preparation_error(self):
        """Test DataPreparationError creation and message."""
        error = DataPreparationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


# Fixture for sample dates
@pytest.fixture
def sample_dates():
    """Sample date range for testing."""
    start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
    return start_date, end_date
