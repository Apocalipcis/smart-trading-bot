"""
Tests for the enhanced backtests router with multi-timeframe support.

This module tests:
- Multi-timeframe backtest creation
- Backward compatibility with legacy requests
- Strategy validation integration
- Deprecation warnings
- Error handling for invalid multi-timeframe requests
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestMultiTimeframeBacktestCreation:
    """Test multi-timeframe backtest creation."""
    
    def test_valid_multi_timeframe_backtest(self):
        """Test creating a valid multi-timeframe backtest."""
        request_data = {
            "strategy": "SimpleTestStrategy",  # Use SimpleTestStrategy which only requires LTF role
            "pairs": ["BTCUSDT"],
            "timeframes": ["1h"],
            "tf_roles": {"1h": "LTF"},
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-07T00:00:00Z",  # Match available data range
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "pairs" in data
        assert "strategy" in data
        assert "timeframes" in data
        assert "tf_roles" in data
    
    def test_multi_timeframe_backtest_with_parameters(self):
        """Test creating a multi-timeframe backtest with strategy parameters."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pairs": ["BTCUSDT"],
            "timeframes": ["1h", "15m"],
            "tf_roles": {"1h": "HTF", "15m": "LTF"},
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_balance": 10000.0,
            "parameters": {
                "risk_percent": 2.0,
                "leverage": 10
            }
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "parameters" in data
    
    def test_multi_timeframe_backtest_multiple_pairs(self):
        """Test creating a multi-timeframe backtest with multiple pairs."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pairs": ["BTCUSDT", "ETHUSDT"],
            "timeframes": ["1h", "15m"],
            "tf_roles": {"1h": "HTF", "15m": "LTF"},
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert len(data["pairs"]) == 2


class TestBackwardCompatibility:
    """Test backward compatibility with legacy single-timeframe requests."""
    
    def test_legacy_single_timeframe_request(self):
        """Test that legacy single-timeframe requests still work."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pair": "BTCUSDT",  # Legacy field
            "timeframe": "1h",   # Legacy field
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_capital": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "pairs" in data
        assert "timeframes" in data
        assert "tf_roles" in data
    
    def test_legacy_request_with_initial_capital(self):
        """Test legacy request with initial_capital field."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pair": "BTCUSDT",
            "timeframe": "1h",
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_capital": 10000.0  # Legacy field
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "initial_balance" in data
    
    def test_mixed_legacy_and_new_fields(self):
        """Test request with both legacy and new fields."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pairs": ["BTCUSDT"],  # New field
            "timeframes": ["1h"],   # New field
            "tf_roles": {"1h": "LTF"},  # New field
            "pair": "BTCUSDT",      # Legacy field
            "timeframe": "1h",      # Legacy field
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_capital": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 422  # Validation error for mixing fields
        
        data = response.json()
        assert "detail" in data


class TestStrategyValidation:
    """Test strategy validation integration in backtest creation."""
    
    def test_strategy_validation_failure_missing_roles(self):
        """Test that backtest creation fails when strategy requirements are not met."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pairs": ["BTCUSDT"],
            "timeframes": ["1h"],  # Missing LTF timeframe
            "tf_roles": {"1h": "HTF"},  # Missing LTF role
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "errors" in data["detail"]
        assert any("required role" in error.lower() for error in data["detail"]["errors"])
    
    def test_strategy_validation_failure_constraint_violation(self):
        """Test that backtest creation fails when timeframe constraints are violated."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pairs": ["BTCUSDT"],
            "timeframes": ["1m", "5m"],  # Both too small for HTF role
            "tf_roles": {"1m": "HTF", "5m": "LTF"},
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "errors" in data["detail"]
        assert any("too small" in error.lower() or "too large" in error.lower() for error in data["detail"]["errors"])
    
    def test_strategy_validation_success(self):
        """Test that backtest creation succeeds with valid strategy requirements."""
        request_data = {
            "strategy": "SimpleTestStrategy",  # Only requires LTF role
            "pairs": ["BTCUSDT"],
            "timeframes": ["15m"],
            "tf_roles": {"15m": "LTF"},
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "strategy" in data


class TestValidationErrors:
    """Test validation errors for multi-timeframe backtest requests."""
    
    def test_empty_timeframes_validation(self):
        """Test that empty timeframes list is rejected."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pairs": ["BTCUSDT"],
            "timeframes": [],
            "tf_roles": {},
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 422  # Validation error
        
        data = response.json()
        assert "detail" in data
    
    def test_duplicate_timeframes_validation(self):
        """Test that duplicate timeframes are rejected."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pairs": ["BTCUSDT"],
            "timeframes": ["1h", "1h"],
            "tf_roles": {"1h": "HTF"},
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 422  # Validation error
        
        data = response.json()
        assert "detail" in data
    
    def test_invalid_timeframe_format(self):
        """Test that invalid timeframe format is rejected."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pairs": ["BTCUSDT"],
            "timeframes": ["invalid"],
            "tf_roles": {"invalid": "LTF"},
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 422  # Validation error
        
        data = response.json()
        assert "detail" in data
    
    def test_empty_pairs_validation(self):
        """Test that empty pairs list is rejected."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pairs": [],
            "timeframes": ["1h"],
            "tf_roles": {"1h": "LTF"},
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 422  # Validation error
        
        data = response.json()
        assert "detail" in data
    
    def test_duplicate_pairs_validation(self):
        """Test that duplicate pairs are rejected."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pairs": ["BTCUSDT", "BTCUSDT"],
            "timeframes": ["1h"],
            "tf_roles": {"1h": "LTF"},
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 422  # Validation error
        
        data = response.json()
        assert "detail" in data
    
    def test_empty_strategy_validation(self):
        """Test that empty strategy name is rejected."""
        request_data = {
            "strategy": "",
            "pairs": ["BTCUSDT"],
            "timeframes": ["1h"],
            "tf_roles": {"1h": "LTF"},
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 422  # Validation error
        
        data = response.json()
        assert "detail" in data


class TestErrorHandling:
    """Test error handling in multi-timeframe backtest creation."""
    
    def test_nonexistent_strategy(self):
        """Test handling of non-existent strategy."""
        request_data = {
            "strategy": "NonExistentStrategy",
            "pairs": ["BTCUSDT"],
            "timeframes": ["1h"],
            "tf_roles": {"1h": "LTF"},
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "errors" in data["detail"]
        assert any("not found" in error.lower() for error in data["detail"]["errors"])
    
    def test_invalid_date_range(self):
        """Test handling of invalid date range."""
        request_data = {
            "strategy": "SMCSignalStrategy",
            "pairs": ["BTCUSDT"],
            "timeframes": ["1h"],
            "tf_roles": {"1h": "LTF"},
            "start_date": "2024-01-31T23:59:59Z",  # End date before start date
            "end_date": "2024-01-01T00:00:00Z",
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 422  # Validation error
        
        data = response.json()
        assert "detail" in data
    
    def test_malformed_request_data(self):
        """Test handling of malformed request data."""
        # Missing required fields
        request_data = {
            "strategy": "SMCSignalStrategy",
            # Missing pairs, timeframes, etc.
        }
        
        response = client.post("/api/v1/backtests", json=request_data)
        assert response.status_code == 422  # Validation error
        
        data = response.json()
        assert "detail" in data


class TestBacktestRetrieval:
    """Test retrieving backtest results."""
    
    def test_get_backtests_list(self):
        """Test getting list of backtests."""
        response = client.get("/api/v1/backtests")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_get_specific_backtest(self):
        """Test getting a specific backtest result."""
        # First create a backtest
        request_data = {
            "strategy": "SimpleTestStrategy",
            "pairs": ["BTCUSDT"],
            "timeframes": ["15m"],
            "tf_roles": {"15m": "LTF"},
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_balance": 10000.0
        }
        
        create_response = client.post("/api/v1/backtests", json=request_data)
        assert create_response.status_code == 200
        
        create_data = create_response.json()
        backtest_id = create_data["id"]
        
        # Then retrieve it
        response = client.get(f"/api/v1/backtests/{backtest_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["id"] == backtest_id
        assert "timeframes" in data
        assert "tf_roles" in data
    
    def test_get_nonexistent_backtest(self):
        """Test getting a non-existent backtest."""
        response = client.get("/api/v1/backtests/nonexistent-id")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
