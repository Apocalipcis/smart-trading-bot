"""
Integration tests for BacktestRunner with data preparation.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.backtests.runner import BacktestRunner
from src.backtests.models import BacktestConfig
from src.backtests.preparation import DataPreparationError


class TestBacktestRunnerIntegration:
    """Integration tests for BacktestRunner with data preparation."""
    
    @pytest.fixture
    def runner(self, tmp_path):
        """Create a BacktestRunner instance for testing."""
        return BacktestRunner(str(tmp_path))
    
    @pytest.fixture
    def sample_config(self):
        """Create a sample BacktestConfig for testing."""
        return BacktestConfig(
            symbol="BTCUSDT",
            strategy_name="SimpleTest",
            strategy_params={},
            timeframes=["1h", "4h"],
            tf_roles={"1h": "LTF", "4h": "HTF"},
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_cash=10000.0,
            commission=0.001,
            slippage=0.0001
        )
    
    @pytest.fixture
    def legacy_config(self):
        """Create a legacy BacktestConfig for backwards compatibility testing."""
        return BacktestConfig(
            symbol="BTCUSDT",
            strategy_name="SimpleTest",
            strategy_params={},
            timeframe="1h",  # Legacy single timeframe
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_cash=10000.0,
            commission=0.001,
            slippage=0.0001
        )
    
    def test_runner_initialization(self, runner, tmp_path):
        """Test BacktestRunner initialization with data preparer."""
        assert runner.data_dir == Path(tmp_path)
        assert runner.data_preparer is not None
        assert hasattr(runner.data_preparer, 'prepare_backtest_data')
    
    def test_get_primary_timeframes(self, sample_config):
        """Test getting primary timeframes from config."""
        timeframes = sample_config.get_primary_timeframes()
        assert timeframes == ["1h", "4h"]
    
    def test_get_primary_timeframe(self, sample_config):
        """Test getting primary timeframe for backwards compatibility."""
        primary_tf = sample_config.get_primary_timeframe()
        assert primary_tf == "1h"
    
    def test_legacy_config_compatibility(self, legacy_config):
        """Test legacy config backwards compatibility."""
        timeframes = legacy_config.get_primary_timeframes()
        assert timeframes == ["1h"]
        
        primary_tf = legacy_config.get_primary_timeframe()
        assert primary_tf == "1h"
    
    @pytest.mark.asyncio
    async def test_prepare_data_success(self, runner, sample_config):
        """Test successful data preparation."""
        # Mock the data preparer
        mock_preparation_result = {
            "symbol": "BTCUSDT",
            "timeframes": ["1h", "4h"],
            "total_files_downloaded": 1,
            "total_files_reused": 1,
            "errors": []
        }
        
        with patch.object(runner.data_preparer, 'prepare_backtest_data', new_callable=AsyncMock) as mock_prepare:
            mock_prepare.return_value = mock_preparation_result
            
            result = await runner._prepare_data(sample_config)
            
            assert result == mock_preparation_result
            mock_prepare.assert_called_once_with(
                symbol="BTCUSDT", 
                timeframes=["1h", "4h"], 
                start_date=sample_config.start_date, 
                end_date=sample_config.end_date, 
                force_update=False
            )
    
    @pytest.mark.asyncio
    async def test_prepare_data_with_errors(self, runner, sample_config):
        """Test data preparation with errors."""
        # Mock the data preparer to return errors
        mock_preparation_result = {
            "symbol": "BTCUSDT",
            "timeframes": ["1h", "4h"],
            "total_files_downloaded": 0,
            "total_files_reused": 0,
            "errors": ["Failed to download 1h data", "Failed to download 4h data"]
        }
        
        with patch.object(runner.data_preparer, 'prepare_backtest_data', new_callable=AsyncMock) as mock_prepare:
            mock_prepare.return_value = mock_preparation_result
            
            with pytest.raises(DataPreparationError, match="Data preparation failed"):
                await runner._prepare_data(sample_config)
    
    @pytest.mark.asyncio
    async def test_prepare_data_exception(self, runner, sample_config):
        """Test data preparation exception handling."""
        with patch.object(runner.data_preparer, 'prepare_backtest_data', new_callable=AsyncMock) as mock_prepare:
            mock_prepare.side_effect = Exception("Unexpected error")
            
            with pytest.raises(DataPreparationError, match="Failed to prepare backtest data"):
                await runner._prepare_data(sample_config)
    
    def test_create_data_feeds(self, runner, sample_config, tmp_path):
        """Test creating data feeds for multiple timeframes."""
        # Create mock data files
        for timeframe in ["1h", "4h"]:
            file_path = tmp_path / 'candles' / 'binance_futures' / 'BTCUSDT' / f"{timeframe}.parquet"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create sample data
            dates = pd.date_range(
                sample_config.start_date - timedelta(days=1), 
                sample_config.end_date + timedelta(days=1), 
                freq='D'
            )
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
        
        # Test creating data feeds
        data_feeds = runner._create_data_feeds(sample_config)
        
        assert len(data_feeds) == 2
        assert all(hasattr(feed, '_name') for feed in data_feeds)
        assert any('1h' in feed._name for feed in data_feeds)
        assert any('4h' in feed._name for feed in data_feeds)
    
    def test_create_data_feeds_missing_file(self, runner, sample_config):
        """Test creating data feeds when files are missing."""
        with pytest.raises(ValueError, match="No valid data feeds could be created"):
            runner._create_data_feeds(sample_config)
    
    def test_load_parquet_data_single_timeframe(self, runner, sample_config, tmp_path):
        """Test loading parquet data for a single timeframe."""
        timeframe = "1h"
        file_path = tmp_path / 'candles' / 'binance_futures' / 'BTCUSDT' / f"{timeframe}.parquet"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create sample data
        dates = pd.date_range(
            sample_config.start_date - timedelta(days=1), 
            sample_config.end_date + timedelta(days=1), 
            freq='D'
        )
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
        
        # Test loading data
        df = runner._load_parquet_data(sample_config, timeframe)
        
        assert len(df) == 33  # 33 days including start_date - 1 day to end_date + 1 day
        assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume']
        assert df.index.name == 'datetime'
        assert isinstance(df.index, pd.DatetimeIndex)
    
    def test_load_parquet_data_with_open_time(self, runner, sample_config, tmp_path):
        """Test loading parquet data with open_time column."""
        timeframe = "1h"
        file_path = tmp_path / 'candles' / 'binance_futures' / 'BTCUSDT' / f"{timeframe}.parquet"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create sample data with open_time column
        sample_data = pd.DataFrame({
            'open_time': [
                int((sample_config.start_date - timedelta(days=1)).timestamp() * 1000),
                int(sample_config.start_date.timestamp() * 1000),
                int(sample_config.end_date.timestamp() * 1000)
            ],
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [101, 102, 103],
            'volume': [1000, 1100, 1200]
        })
        
        # Save as parquet
        table = pa.Table.from_pandas(sample_data)
        pq.write_table(table, file_path)
        
        # Test loading data
        df = runner._load_parquet_data(sample_config, timeframe)
        
        assert len(df) == 3  # 3 data points: start_date - 1 day, start_date, and end_date
        assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume']
        assert df.index.name == 'datetime'
        assert isinstance(df.index, pd.DatetimeIndex)
    
    @pytest.mark.asyncio
    async def test_run_backtest_data_preparation_failure(self, runner, sample_config):
        """Test backtest execution when data preparation fails."""
        # Mock data preparation to fail
        with patch.object(runner, '_prepare_data', new_callable=AsyncMock) as mock_prepare:
            mock_prepare.side_effect = DataPreparationError("Data preparation failed")
            
            result = await runner.run_backtest(sample_config)
            
            assert result.status == "failed"
            assert "Data preparation failed" in result.error_message
            assert result.final_value == sample_config.initial_cash
    
    @pytest.mark.asyncio
    async def test_run_backtest_success(self, runner, sample_config, tmp_path):
        """Test successful backtest execution."""
        # Mock data preparation to succeed
        mock_preparation_result = {
            "symbol": "BTCUSDT",
            "timeframes": ["1h", "4h"],
            "total_files_downloaded": 1,
            "total_files_reused": 1,
            "errors": []
        }
        
        with patch.object(runner, '_prepare_data', new_callable=AsyncMock) as mock_prepare:
            mock_prepare.return_value = mock_preparation_result
            
            # Mock strategy class
            with patch.object(runner, '_get_strategy_class') as mock_get_strategy:
                mock_strategy = Mock()
                mock_get_strategy.return_value = mock_strategy
                
                # Mock Cerebro setup and execution
                with patch.object(runner, '_setup_cerebro') as mock_setup:
                    mock_cerebro = Mock()
                    mock_setup.return_value = mock_cerebro
                    
                    # Mock metrics calculation
                    with patch.object(runner, '_calculate_metrics_from_results') as mock_metrics:
                        mock_metrics.return_value = {
                            "final_value": 11000.0,
                            "total_return": 10.0,
                            "max_drawdown": 5.0,
                            "sharpe_ratio": 1.5,
                            "total_trades": 25,
                            "win_rate": 60.0,
                            "profit_factor": 1.8,
                            "avg_trade": 40.0,
                            "max_consecutive_losses": 3
                        }
                        
                        result = await runner.run_backtest(sample_config)
                        
                        assert result.status == "completed"
                        assert result.final_value == 11000.0
                        assert result.total_return == 10.0
                        assert result.win_rate == 60.0
                        assert result.total_trades == 25
    
    def test_backwards_compatibility_methods(self, runner, legacy_config):
        """Test backwards compatibility methods."""
        # Test legacy data loading
        with patch.object(runner, '_load_parquet_data') as mock_load:
            mock_load.return_value = pd.DataFrame()
            runner._load_parquet_data_legacy(legacy_config)
            mock_load.assert_called_once_with(legacy_config, "1h")
        
        # Test legacy data feed creation
        with patch.object(runner, '_load_parquet_data_legacy') as mock_load_legacy:
            mock_load_legacy.return_value = pd.DataFrame()
            runner._create_data_feed_legacy(legacy_config)
            mock_load_legacy.assert_called_once()


# Fixture for sample dates
@pytest.fixture
def sample_dates():
    """Sample date range for testing."""
    start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
    return start_date, end_date
