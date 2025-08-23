"""Basic tests for the backtests package (without backtrader dependency)."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

# Test only the classes that don't require backtrader
from src.backtests.storage import BacktestStorage
from src.backtests.metrics import BacktestMetrics
from src.backtests.integrity import DataIntegrityChecker


class TestBacktestStorage:
    """Test BacktestStorage class."""
    
    def test_storage_initialization(self):
        """Test storage initialization creates required directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = BacktestStorage(data_dir=temp_dir)
            
            assert storage.backtests_dir.exists()
            assert storage.artifacts_dir.exists()
            assert storage.reports_dir.exists()
            
            # Check paths are correct
            assert str(storage.backtests_dir) == str(Path(temp_dir) / "backtests")
            assert str(storage.artifacts_dir) == str(Path(temp_dir) / "artifacts")
            assert str(storage.reports_dir) == str(Path(temp_dir) / "reports")


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


class TestBacktestMetrics:
    """Test BacktestMetrics class."""
    
    def test_metrics_initialization(self):
        """Test BacktestMetrics initialization."""
        metrics = BacktestMetrics()
        assert metrics.risk_free_rate == 0.02
        
        # Test with custom risk-free rate
        metrics_custom = BacktestMetrics(risk_free_rate=0.03)
        assert metrics_custom.risk_free_rate == 0.03


if __name__ == "__main__":
    pytest.main([__file__])
