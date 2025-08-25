"""Tests for the storage package."""

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import pytest

from src.storage import (
    DatabaseManager,
    SettingsManager,
    FileManager,
    initialize_database,
    close_database,
    get_settings_manager,
    get_file_manager,
    get_db_manager,
)


class TestDatabaseManager:
    """Test database manager functionality."""
    
    @pytest.fixture
    async def db_manager(self):
        """Create a temporary database for testing."""
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test.db"
            manager = DatabaseManager(str(db_path))
            await manager.initialize()
            yield manager
        finally:
            try:
                await manager.close()
                import asyncio
                await asyncio.sleep(0.1)
                if temp_dir and Path(temp_dir).exists():
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"Database manager cleanup warning: {e}")
                pass
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, db_manager):
        """Test database initialization."""
        # Check that tables were created
        results = await db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row['name'] for row in results]
        
        expected_tables = ['settings', 'pairs', 'signals', 'orders', 'backtest_metadata']
        for table in expected_tables:
            assert table in table_names
    
    @pytest.mark.asyncio
    async def test_default_settings_insertion(self, db_manager):
        """Test that default settings are inserted."""
        results = await db_manager.execute_query("SELECT COUNT(*) as count FROM settings")
        count = results[0]['count']
        assert count > 0
        
        # Check for specific default settings
        trading_enabled = await db_manager.execute_query(
            "SELECT value FROM settings WHERE key = 'TRADING_ENABLED'"
        )
        assert len(trading_enabled) == 1
        assert trading_enabled[0]['value'] == 'false'
    
    @pytest.mark.asyncio
    async def test_health_check(self, db_manager):
        """Test database health check."""
        health = await db_manager.health_check()
        
        assert health['status'] == 'healthy'
        assert 'settings_count' in health
        assert 'db_size_bytes' in health
        assert 'db_path' in health
        assert 'timestamp' in health


class TestSettingsManager:
    """Test settings manager functionality."""
    
    @pytest.fixture
    async def settings_manager(self):
        """Create a settings manager with temporary database."""
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test.db"
            await initialize_database(str(db_path))
            manager = await get_settings_manager()
            yield manager
        finally:
            try:
                await close_database()
                import asyncio
                await asyncio.sleep(0.1)
                if temp_dir and Path(temp_dir).exists():
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"Settings manager cleanup warning: {e}")
                pass
    
    @pytest.mark.asyncio
    async def test_get_setting(self, settings_manager):
        """Test getting a setting."""
        setting = await settings_manager.get_setting("TRADING_ENABLED")
        assert setting is not None
        assert setting.key == "TRADING_ENABLED"
        assert setting.value == "false"
        assert setting.type == "bool"
    
    @pytest.mark.asyncio
    async def test_get_setting_value(self, settings_manager):
        """Test getting a setting value with type conversion."""
        # Test boolean
        value = await settings_manager.get_setting_value("TRADING_ENABLED")
        assert value is False
        
        # Test integer
        value = await settings_manager.get_setting_value("MAX_OPEN_POSITIONS")
        assert value == 5
        
        # Test float
        value = await settings_manager.get_setting_value("MAX_RISK_PER_TRADE")
        assert value == 2.0
    
    @pytest.mark.asyncio
    async def test_set_setting(self, settings_manager):
        """Test setting a value."""
        # Set a new setting
        setting = await settings_manager.set_setting("TEST_SETTING", "test_value", "string", "Test description")
        assert setting.key == "TEST_SETTING"
        assert setting.value == "test_value"
        assert setting.type == "string"
        
        # Verify it was saved
        retrieved = await settings_manager.get_setting("TEST_SETTING")
        assert retrieved is not None
        assert retrieved.value == "test_value"
    
    @pytest.mark.asyncio
    async def test_bulk_update_settings(self, settings_manager):
        """Test bulk update of settings."""
        settings_to_update = {
            "TEST_BOOL": True,
            "TEST_INT": 42,
            "TEST_FLOAT": 3.14,
            "TEST_STRING": "hello world"
        }
        
        updated_settings = await settings_manager.bulk_update_settings(settings_to_update)
        assert len(updated_settings) == 4
        
        # Verify all settings were updated
        for key, expected_value in settings_to_update.items():
            value = await settings_manager.get_setting_value(key)
            assert value == expected_value
    
    @pytest.mark.asyncio
    async def test_validate_settings(self, settings_manager):
        """Test settings validation."""
        # Test with valid settings
        errors = await settings_manager.validate_settings()
        assert len(errors) == 0
        
        # Test with invalid settings
        await settings_manager.set_setting("MAX_OPEN_POSITIONS", -1)
        await settings_manager.set_setting("MAX_RISK_PER_TRADE", 150)
        
        errors = await settings_manager.validate_settings()
        assert "MAX_OPEN_POSITIONS" in errors
        assert "MAX_RISK_PER_TRADE" in errors


class TestFileManager:
    """Test file manager functionality."""
    
    @pytest.fixture
    def file_manager(self):
        """Create a file manager with temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FileManager(temp_dir)
            yield manager
    
    def test_directory_creation(self, file_manager):
        """Test that directories are created."""
        assert file_manager.data_dir.exists()
        assert file_manager.candles_dir.exists()
        assert file_manager.backtests_dir.exists()
        assert file_manager.reports_dir.exists()
        assert file_manager.artifacts_dir.exists()
    
    def test_get_candle_path(self, file_manager):
        """Test candle path generation."""
        path = file_manager.get_candle_path("binance", "BTCUSDT", "1h", "parquet")
        
        # Check path structure
        assert "candles" in str(path)
        assert "binance" in str(path)
        assert "BTCUSDT" in str(path)
        assert path.suffix == ".parquet"
        assert path.name == "1h.parquet"
    
    def test_save_and_load_candles(self, file_manager):
        """Test saving and loading candle data."""
        # Create sample data
        dates = pd.date_range('2023-01-01', periods=100, freq='1H')
        df = pd.DataFrame({
            'open': [100 + i for i in range(100)],
            'high': [101 + i for i in range(100)],
            'low': [99 + i for i in range(100)],
            'close': [100.5 + i for i in range(100)],
            'volume': [1000 + i for i in range(100)]
        }, index=dates)
        
        # Save candles
        saved_path = file_manager.save_candles(df, "binance", "BTCUSDT", "1h", "parquet")
        assert saved_path.exists()
        
        # Load candles
        loaded_df = file_manager.load_candles("binance", "BTCUSDT", "1h", "parquet")
        assert loaded_df is not None
        assert len(loaded_df) == 100
        assert list(loaded_df.columns) == ['open', 'high', 'low', 'close', 'volume']
    
    def test_get_backtest_path(self, file_manager):
        """Test backtest path generation."""
        test_date = datetime(2023, 1, 15)
        path = file_manager.get_backtest_path("test_backtest_123", test_date)
        
        # Check path structure
        assert "backtests" in str(path)
        assert "2023-01-15" in str(path)
        assert path.name == "test_backtest_123.json"
    
    def test_save_and_load_backtest_result(self, file_manager):
        """Test saving and loading backtest results."""
        # Create sample backtest result
        result = {
            "id": "test_backtest_123",
            "pair": "BTCUSDT",
            "strategy": "SMC",
            "metrics": {
                "total_return": 0.15,
                "win_rate": 0.65,
                "total_trades": 25
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save backtest result
        saved_path = file_manager.save_backtest_result("test_backtest_123", result)
        assert saved_path.exists()
        
        # Load backtest result
        loaded_result = file_manager.load_backtest_result("test_backtest_123")
        assert loaded_result is not None
        assert loaded_result["id"] == "test_backtest_123"
        assert loaded_result["pair"] == "BTCUSDT"
        assert loaded_result["strategy"] == "SMC"
    
    def test_storage_stats(self, file_manager):
        """Test storage statistics."""
        # Create some test files
        test_df = pd.DataFrame({'test': [1, 2, 3]})
        file_manager.save_candles(test_df, "binance", "BTCUSDT", "1h", "parquet")
        file_manager.save_backtest_result("test_123", {"test": "data"})
        
        # Get stats
        stats = file_manager.get_storage_stats()
        
        assert "total_size_bytes" in stats
        assert "file_counts" in stats
        assert "directory_sizes" in stats
        assert stats["file_counts"]["candles"] >= 1
        assert stats["file_counts"]["backtests"] >= 1


class TestStorageIntegration:
    """Test integration between storage components."""
    
    @pytest.mark.asyncio
    async def test_storage_integration(self):
        """Test that all storage components work together."""
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp()
            
            # Initialize database
            db_path = Path(temp_dir) / "test.db"
            await initialize_database(str(db_path))
            
            # Test settings manager
            settings_manager = await get_settings_manager()
            await settings_manager.set_setting("TEST_INTEGRATION", "test_value")
            value = await settings_manager.get_setting_value("TEST_INTEGRATION")
            assert value == "test_value"
            
            # Test file manager
            file_manager = get_file_manager(temp_dir)
            test_df = pd.DataFrame({'test': [1, 2, 3]})
            file_path = file_manager.save_candles(test_df, "binance", "BTCUSDT", "1h")
            assert file_path.exists()
            
            # Test database health
            db_manager = await get_db_manager()
            health = await db_manager.health_check()
            assert health['status'] == 'healthy'
            
        finally:
            # Cleanup - ensure this always runs
            try:
                await close_database()
                
                # Give Windows time to release file handles
                import asyncio
                await asyncio.sleep(0.2)
                
                # Clean up temp directory
                if temp_dir and Path(temp_dir).exists():
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
            except Exception as e:
                # Log cleanup errors but don't fail the test
                print(f"Cleanup warning: {e}")
                pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
