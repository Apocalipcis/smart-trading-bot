"""
Tests for the strategies router endpoints.

This module tests:
- GET /strategies endpoint
- GET /strategies/{strategy_name} endpoint
- GET /strategies/{strategy_name}/validate endpoint
- GET /strategies/{strategy_name}/parameters endpoint
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestStrategiesEndpoints:
    """Test /strategies endpoints."""
    
    def test_get_strategies(self):
        """Test getting all available strategies."""
        response = client.get("/api/v1/strategies")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check that each strategy has required fields
        for strategy in data:
            assert "name" in strategy
            assert "description" in strategy
            assert "required_roles" in strategy
            assert "role_constraints" in strategy
            assert "parameters" in strategy
            assert "is_active" in strategy
    
    def test_get_specific_strategy(self):
        """Test getting information about a specific strategy."""
        # Test with a valid strategy - use the actual name from registry
        response = client.get("/api/v1/strategies/SMCSignalStrategy")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "SMCSignalStrategy"
        assert "description" in data
        assert "required_roles" in data
        assert "role_constraints" in data
        assert "parameters" in data
        assert "is_active" in data
    
    def test_get_nonexistent_strategy(self):
        """Test getting information about a non-existent strategy."""
        response = client.get("/api/v1/strategies/NonExistentStrategy")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_validate_strategy_requirements_valid(self):
        """Test validating valid strategy requirements."""
        params = {
            "timeframes": ["1h", "15m"],
            "tf_roles": {"1h": "HTF", "15m": "LTF"}
        }
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_validate_strategy_requirements_missing_roles(self):
        """Test validating strategy requirements with missing required roles."""
        # SMCSignalStrategy requires both HTF and LTF roles
        params = {
            "timeframes": ["1h"],
            "tf_roles": {"1h": "HTF"}  # Missing LTF role
        }
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "errors" in data["data"]
        assert any("required role" in error.lower() for error in data["data"]["errors"])
    
    def test_validate_strategy_requirements_constraint_violation(self):
        """Test validating strategy requirements with constraint violations."""
        # Try to use timeframes that don't meet the strategy's constraints
        params = {
            "timeframes": ["1m", "5m"],  # Both too small for HTF role
            "tf_roles": {"1m": "HTF", "5m": "LTF"}
        }
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "errors" in data["data"]
        assert any("too small" in error.lower() or "too large" in error.lower() for error in data["data"]["errors"])
    
    def test_get_strategy_parameters(self):
        """Test getting strategy parameters."""
        response = client.get("/api/v1/strategies/SMCSignalStrategy/parameters")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        # The data field contains the parameters directly
        assert isinstance(data["data"], dict)
    
    def test_get_nonexistent_strategy_parameters(self):
        """Test getting parameters for non-existent strategy."""
        response = client.get("/api/v1/strategies/NonExistentStrategy/parameters")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestStrategiesValidationEdgeCases:
    """Test edge cases for strategy validation."""
    
    def test_validate_empty_timeframes(self):
        """Test validating with empty timeframes list."""
        params = {
            "timeframes": [],
            "tf_roles": {}
        }
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False  # Should fail because SMCSignalStrategy requires roles
        assert "errors" in data["data"]
    
    def test_validate_empty_tf_roles(self):
        """Test validating with empty tf_roles."""
        params = {
            "timeframes": ["1h", "15m"],
            "tf_roles": {}
        }
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False  # Should fail because no roles assigned
        assert "errors" in data["data"]
    
    def test_validate_duplicate_timeframes(self):
        """Test validating with duplicate timeframes."""
        params = {
            "timeframes": ["1h", "1h"],
            "tf_roles": {"1h": "HTF"}
        }
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        # Should fail because SMCSignalStrategy requires both HTF and LTF
        assert data["success"] is False
        assert "errors" in data["data"]
    
    def test_validate_invalid_role_value(self):
        """Test validating with invalid role values."""
        params = {
            "timeframes": ["1h", "15m"],
            "tf_roles": {"1h": "INVALID_ROLE", "15m": "LTF"}
        }
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "errors" in data["data"]


class TestStrategiesDataIntegrity:
    """Test data integrity of strategy endpoints."""
    
    def test_strategy_data_consistency(self):
        """Test that strategy data is consistent across endpoints."""
        # Get all strategies
        all_response = client.get("/api/v1/strategies")
        assert all_response.status_code == 200
        all_data = all_response.json()
        
        # Get specific strategy info for each strategy
        for strategy in all_data:
            strategy_name = strategy["name"]
            specific_response = client.get(f"/api/v1/strategies/{strategy_name}")
            assert specific_response.status_code == 200
            
            specific_data = specific_response.json()
            # Data should be consistent
            assert specific_data["name"] == strategy["name"]
            assert specific_data["description"] == strategy["description"]
            assert specific_data["required_roles"] == strategy["required_roles"]
            assert specific_data["role_constraints"] == strategy["role_constraints"]
            assert specific_data["parameters"] == strategy["parameters"]
            assert specific_data["is_active"] == strategy["is_active"]
    
    def test_strategy_parameters_consistency(self):
        """Test that strategy parameters are consistent."""
        # Get all strategies
        all_response = client.get("/api/v1/strategies")
        assert all_response.status_code == 200
        all_data = all_response.json()
        
        # Get parameters for each strategy
        for strategy in all_data:
            strategy_name = strategy["name"]
            params_response = client.get(f"/api/v1/strategies/{strategy_name}/parameters")
            assert params_response.status_code == 200
            
            params_data = params_response.json()
            # Parameters should match
            assert params_data["data"] == strategy["parameters"]


class TestStrategiesValidationLogic:
    """Test specific validation logic for different strategies."""
    
    def test_smc_strategy_validation(self):
        """Test SMCSignalStrategy specific validation."""
        # SMCSignalStrategy requires both HTF and LTF roles
        valid_params = {
            "timeframes": ["1h", "15m"],
            "tf_roles": {"1h": "HTF", "15m": "LTF"}
        }
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json=valid_params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # Test with only HTF role
        invalid_params = {
            "timeframes": ["1h"],
            "tf_roles": {"1h": "HTF"}
        }
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json=invalid_params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "errors" in data["data"]
    
    def test_simple_test_strategy_validation(self):
        """Test SimpleTestStrategy validation."""
        # SimpleTestStrategy only requires LTF role
        valid_params = {
            "timeframes": ["15m"],
            "tf_roles": {"15m": "LTF"}
        }
        response = client.post("/api/v1/strategies/SimpleTestStrategy/validate", json=valid_params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
    
    def test_strategy_constraint_validation(self):
        """Test that strategy constraints are properly validated."""
        # Test with timeframes that violate constraints
        invalid_params = {
            "timeframes": ["1m", "5m"],  # Both too small for HTF role in SMCSignalStrategy
            "tf_roles": {"1m": "HTF", "5m": "LTF"}
        }
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json=invalid_params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "errors" in data["data"]
        # Should have errors about timeframe constraints
        assert any("too small" in error.lower() or "too large" in error.lower() for error in data["data"]["errors"])


class TestStrategiesErrorHandling:
    """Test error handling in strategy endpoints."""
    
    def test_malformed_validation_params(self):
        """Test handling of malformed validation parameters."""
        # Test with missing required parameters
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json={})
        assert response.status_code == 422  # Validation error
        
        # Test with invalid parameter types
        params = {
            "timeframes": "invalid",  # Should be list
            "tf_roles": "invalid"     # Should be dict
        }
        response = client.post("/api/v1/strategies/SMCSignalStrategy/validate", json=params)
        assert response.status_code == 422
    
    def test_strategy_name_encoding(self):
        """Test handling of special characters in strategy names."""
        # Test with URL-encoded strategy names
        response = client.get("/api/v1/strategies/SMCSignalStrategy%20Strategy")  # Space encoded
        assert response.status_code == 404  # Should not exist
        
        # Test with strategy names that might have special characters
        response = client.get("/api/v1/strategies/SMCSignalStrategy-Strategy")  # Hyphen
        assert response.status_code == 404  # Should not exist
