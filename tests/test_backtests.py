"""Tests for the backtests package."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.backtests.runner import BacktestConfig, BacktestResult
from src.backtests.storage import BacktestStorage
from src.backtests.metrics import BacktestMetrics
from src.backtests.integrity import DataIntegrityChecker


class TestBacktestConfig:
    """Test BacktestConfig class."""
    
    def test_backtest_config_creation(self):
        """Test creating a BacktestConfig instance."""
        config = BacktestConfig(
            symbol="BTCUSDT",
            strategy_name="SMC",
            timeframe="1h",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            initial_cash=10000.0
        )
        
        assert config.symbol == "BTCUSDT"
        assert config.strategy_name == "SMC"
        assert config.timeframe == "1h"
        assert config.initial_cash == 10000.0
        assert config.commission == 0.001  # default value
        assert config.slippage == 0.0001   # default value
    
    def test_backtest_config_with_custom_params(self):
        """Test BacktestConfig with custom parameters."""
        config = BacktestConfig(
            symbol="ETHUSDT",
            strategy_name="CustomStrategy",
            strategy_params={"param1": "value1", "param2": 42},
            timeframe="15m",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            initial_cash=50000.0,
            commission=0.002,
            slippage=0.0002,
            random_seed=12345,
            leverage=2.0,
            funding_rate=0.0002
        )
        
        assert config.strategy_params["param1"] == "value1"
        assert config.strategy_params["param2"] == 42
        assert config.commission == 0.002
        assert config.slippage == 0.0002
        assert config.random_seed == 12345
        assert config.leverage == 2.0
        assert config.funding_rate == 0.0002


class TestBacktestResult:
    """Test BacktestResult class."""
    
    def test_backtest_result_creation(self):
        """Test creating a BacktestResult instance."""
        config = BacktestConfig(
            symbol="BTCUSDT",
            strategy_name="SMC",
            timeframe="1h",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            initial_cash=10000.0
        )
        
        result = BacktestResult(
            id="test_backtest_123",
            config=config,
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 5, 0),
            duration=300.0,
            final_value=10500.0,
            total_return=5.0,
            max_drawdown=2.0,
            sharpe_ratio=1.5,
            total_trades=10,
            win_rate=60.0,
            profit_factor=1.8,
            avg_trade=50.0,
            max_consecutive_losses=2,
            status="completed"
        )
        
        assert result.id == "test_backtest_123"
        assert result.config.symbol == "BTCUSDT"
        assert result.final_value == 10500.0
        assert result.total_return == 5.0
        assert result.win_rate == 60.0
        assert result.status == "completed"
    
    def test_backtest_result_failed(self):
        """Test creating a failed BacktestResult instance."""
        config = BacktestConfig(
            symbol="BTCUSDT",
            strategy_name="SMC",
            timeframe="1h",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            initial_cash=10000.0
        )
        
        result = BacktestResult(
            id="failed_backtest_123",
            config=config,
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 1, 0),
            duration=60.0,
            final_value=10000.0,
            total_return=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            total_trades=0,
            win_rate=0.0,
            profit_factor=0.0,
            avg_trade=0.0,
            max_consecutive_losses=0,
            status="failed",
            error_message="Strategy initialization failed"
        )
        
        assert result.status == "failed"
        assert result.error_message == "Strategy initialization failed"
        assert result.final_value == 10000.0  # Should be initial capital


class TestBacktestStorage:
    """Test BacktestStorage class."""
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create a temporary storage instance."""
        return BacktestStorage(data_dir=str(tmp_path))
    
    def test_storage_initialization(self, temp_storage):
        """Test storage initialization creates required directories."""
        assert temp_storage.backtests_dir.exists()
        assert temp_storage.artifacts_dir.exists()
        assert temp_storage.reports_dir.exists()
    
    def test_save_and_load_backtest_result(self, temp_storage):
        """Test saving and loading a backtest result."""
        config = BacktestConfig(
            symbol="BTCUSDT",
            strategy_name="SMC",
            timeframe="1h",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            initial_cash=10000.0
        )
        
        result = BacktestResult(
            id="test_save_load_123",
            config=config,
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 5, 0),
            duration=300.0,
            final_value=10500.0,
            total_return=5.0,
            max_drawdown=2.0,
            sharpe_ratio=1.5,
            total_trades=10,
            win_rate=60.0,
            profit_factor=1.8,
            avg_trade=50.0,
            max_consecutive_losses=2,
            status="completed"
        )
        
        # Save result
        save_path = temp_storage.save_backtest_result(result)
        assert save_path is not None
        
        # Load result
        loaded_result = temp_storage.load_backtest_result("test_save_load_123")
        assert loaded_result is not None
        assert loaded_result.id == result.id
        assert loaded_result.config.symbol == result.config.symbol
        assert loaded_result.final_value == result.final_value


class TestBacktestMetrics:
    """Test BacktestMetrics class."""
    
    def test_metrics_calculation_empty_trades(self):
        """Test metrics calculation with empty trades list."""
        metrics = BacktestMetrics()
        
        result = metrics.calculate_all_metrics(
            trades=[],
            initial_capital=10000.0,
            final_capital=10000.0,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        assert result["performance"]["total_trades"] == 0
        assert result["performance"]["win_rate"] == 0
        assert result["performance"]["total_return_pct"] == 0
    
    def test_metrics_calculation_with_trades(self):
        """Test metrics calculation with sample trades."""
        metrics = BacktestMetrics()
        
        # Sample trades
        trades = [
            {
                "entry_date": datetime(2024, 1, 1, 10, 0, 0),
                "exit_date": datetime(2024, 1, 1, 11, 0, 0),
                "entry_price": 100.0,
                "exit_price": 110.0,
                "size": 1.0,
                "pnl": 10.0
            },
            {
                "entry_date": datetime(2024, 1, 1, 12, 0, 0),
                "exit_date": datetime(2024, 1, 1, 13, 0, 0),
                "entry_price": 110.0,
                "exit_price": 105.0,
                "size": 1.0,
                "pnl": -5.0
            }
        ]
        
        result = metrics.calculate_all_metrics(
            trades=trades,
            initial_capital=10000.0,
            final_capital=10005.0,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        assert result["performance"]["total_trades"] == 2
        assert result["performance"]["win_rate"] == 50.0
        assert result["performance"]["total_return_pct"] == 0.05


class TestDataIntegrityChecker:
    """Test DataIntegrityChecker class."""
    
    def test_integrity_checker_initialization(self):
        """Test DataIntegrityChecker initialization."""
        checker = DataIntegrityChecker()
        
        assert "1m" in checker.timeframe_minutes
        assert "1h" in checker.timeframe_minutes
        assert "1d" in checker.timeframe_minutes
        assert checker.timeframe_minutes["1m"] == 1
        assert checker.timeframe_minutes["1h"] == 60
        assert checker.timeframe_minutes["1d"] == 1440
    
    def test_empty_data_report(self):
        """Test integrity check with empty data."""
        checker = DataIntegrityChecker()
        
        import pandas as pd
        empty_df = pd.DataFrame()
        
        report = checker.check_data_integrity(
            df=empty_df,
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        assert report.total_candles == 0
        assert report.data_completeness == 0.0
        assert "No data available" in report.summary


if __name__ == "__main__":
    pytest.main([__file__])
