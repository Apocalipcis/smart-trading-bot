"""
Tests for the markets router endpoints.

This module tests:
- GET /markets/timeframes endpoint
- GET /markets/timeframes/roles endpoint
- GET /markets/timeframes/{timeframe} endpoint
- GET /markets/timeframes/validate endpoint
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestMarketsTimeframes:
    """Test /markets/timeframes endpoints."""
    
    def test_get_available_timeframes(self):
        """Test getting all available timeframes."""
        response = client.get("/api/v1/markets/timeframes")
        assert response.status_code == 200
        
        data = response.json()
        assert "timeframes" in data
        assert "default_htf" in data
        assert "default_ltf" in data
        assert "role_constraints" in data
        
        # Check that timeframes list is not empty
        assert len(data["timeframes"]) > 0
        
        # Check that each timeframe has required fields
        for tf in data["timeframes"]:
            assert "timeframe" in tf
            assert "description" in tf
            assert "minutes" in tf
            assert "supported_roles" in tf
            assert "is_active" in tf
    
    def test_get_timeframe_role_constraints(self):
        """Test getting timeframe role constraints."""
        response = client.get("/api/v1/markets/timeframes/roles")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check that each constraint has required fields
        for constraint in data:
            assert "role" in constraint
            assert "min_timeframe" in constraint
            assert "max_timeframe" in constraint
            assert "description" in constraint
    
    def test_get_specific_timeframe_info(self):
        """Test getting information about a specific timeframe."""
        # Test with a valid timeframe
        response = client.get("/api/v1/markets/timeframes/1h")
        assert response.status_code == 200
        
        data = response.json()
        assert data["timeframe"] == "1h"
        assert "description" in data
        assert "minutes" in data
        assert "supported_roles" in data
        assert "is_active" in data
    
    def test_get_nonexistent_timeframe_info(self):
        """Test getting information about a non-existent timeframe."""
        response = client.get("/api/v1/markets/timeframes/invalid")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_validate_timeframe_roles_valid(self):
        """Test validating valid timeframe role assignments."""
        params = {
            "timeframes": ["1h", "15m"],
            "tf_roles": {"1h": "HTF", "15m": "LTF"}
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_validate_timeframe_roles_invalid_timeframe(self):
        """Test validating with invalid timeframe."""
        params = {
            "timeframes": ["invalid", "15m"],
            "tf_roles": {"invalid": "HTF", "15m": "LTF"}
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "errors" in data["data"]
        assert any("not available" in error for error in data["data"]["errors"])
    
    def test_validate_timeframe_roles_missing_role_assignment(self):
        """Test validating with missing role assignment."""
        params = {
            "timeframes": ["1h", "15m"],
            "tf_roles": {"1h": "HTF"}  # Missing 15m role
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        # This should still be valid as not all timeframes need roles assigned
        assert data["success"] is True
    
    def test_validate_timeframe_roles_constraint_violation(self):
        """Test validating with role constraint violations."""
        # Try to assign LTF role to a timeframe that's too large
        params = {
            "timeframes": ["1d"],
            "tf_roles": {"1d": "LTF"}  # 1d is too large for LTF
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "errors" in data["data"]
        assert any("too large for role" in error for error in data["data"]["errors"])
    
    def test_validate_timeframe_roles_unsupported_role(self):
        """Test validating with unsupported role for timeframe."""
        # This test depends on the specific timeframes and their supported roles
        # We'll test with a timeframe that might not support HTF
        params = {
            "timeframes": ["1m"],
            "tf_roles": {"1m": "HTF"}  # 1m might not support HTF role
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        # This might generate warnings but not necessarily errors
        assert "data" in data


class TestMarketsTimeframesEdgeCases:
    """Test edge cases for timeframe validation."""
    
    def test_validate_empty_timeframes(self):
        """Test validating with empty timeframes list."""
        params = {
            "timeframes": [],
            "tf_roles": {}
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True  # Empty list is valid
    
    def test_validate_empty_tf_roles(self):
        """Test validating with empty tf_roles."""
        params = {
            "timeframes": ["1h", "15m"],
            "tf_roles": {}
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True  # No role assignments is valid
    
    def test_validate_duplicate_timeframes(self):
        """Test validating with duplicate timeframes."""
        params = {
            "timeframes": ["1h", "1h"],
            "tf_roles": {"1h": "HTF"}
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        # The validation should handle duplicates gracefully
        assert "data" in data
    
    def test_validate_invalid_role_value(self):
        """Test validating with invalid role values."""
        params = {
            "timeframes": ["1h"],
            "tf_roles": {"1h": "INVALID_ROLE"}
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        # Invalid roles should generate warnings, not errors
        assert data["success"] is True  # The validation should still pass
        assert "warnings" in data["data"]
        assert any("not typically used" in warning for warning in data["data"]["warnings"])


class TestMarketsTimeframesDataIntegrity:
    """Test data integrity of timeframe endpoints."""
    
    def test_timeframe_data_consistency(self):
        """Test that timeframe data is consistent across endpoints."""
        # Get all timeframes
        all_response = client.get("/api/v1/markets/timeframes")
        assert all_response.status_code == 200
        all_data = all_response.json()
        
        # Get specific timeframe info for each timeframe
        for tf in all_data["timeframes"]:
            tf_name = tf["timeframe"]
            specific_response = client.get(f"/api/v1/markets/timeframes/{tf_name}")
            assert specific_response.status_code == 200
            
            specific_data = specific_response.json()
            # Data should be consistent
            assert specific_data["timeframe"] == tf["timeframe"]
            assert specific_data["description"] == tf["description"]
            assert specific_data["minutes"] == tf["minutes"]
            assert specific_data["supported_roles"] == tf["supported_roles"]
            assert specific_data["is_active"] == tf["is_active"]
    
    def test_role_constraints_consistency(self):
        """Test that role constraints are consistent."""
        # Get role constraints
        constraints_response = client.get("/api/v1/markets/timeframes/roles")
        assert constraints_response.status_code == 200
        constraints_data = constraints_response.json()
        
        # Get all timeframes
        timeframes_response = client.get("/api/v1/markets/timeframes")
        assert timeframes_response.status_code == 200
        timeframes_data = timeframes_response.json()
        
        # Check that role constraints in timeframes match the roles endpoint
        assert len(constraints_data) == len(timeframes_data["role_constraints"])
        
        # Check that each constraint has valid timeframe formats
        for constraint in constraints_data:
            # Test that min_timeframe and max_timeframe are valid formats
            min_tf = constraint["min_timeframe"]
            max_tf = constraint["max_timeframe"]
            
            # These should be valid timeframe formats
            assert any(tf["timeframe"] == min_tf for tf in timeframes_data["timeframes"])
            assert any(tf["timeframe"] == max_tf for tf in timeframes_data["timeframes"])


class TestMarketsTimeframesValidation:
    """Test timeframe validation edge cases and constraints."""
    
    def test_validate_timeframe_roles_duplicate_roles(self):
        """Test validating with duplicate role assignments."""
        params = {
            "timeframes": ["1h", "4h"],
            "tf_roles": {"1h": "HTF", "4h": "HTF"}  # Both assigned to HTF
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        # This should be valid as multiple timeframes can have the same role
        assert data["success"] is True
    
    def test_validate_timeframe_roles_mixed_valid_invalid(self):
        """Test validating with mix of valid and invalid assignments."""
        params = {
            "timeframes": ["1h", "invalid", "15m"],
            "tf_roles": {"1h": "HTF", "invalid": "LTF", "15m": "LTF"}
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "errors" in data["data"]
        assert any("not available" in error for error in data["data"]["errors"])
    
    def test_validate_timeframe_roles_unsupported_role_for_timeframe(self):
        """Test validating with role not supported by timeframe."""
        # Test with 1m which only supports LTF, trying to assign HTF
        params = {
            "timeframes": ["1m"],
            "tf_roles": {"1m": "HTF"}
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        # This should generate warnings but not necessarily fail
        assert "data" in data
        if "warnings" in data["data"]:
            assert any("not typically used" in warning for warning in data["data"]["warnings"])
    
    def test_validate_timeframe_roles_missing_timeframe_in_tf_roles(self):
        """Test validating when tf_roles has timeframe not in timeframes list."""
        params = {
            "timeframes": ["1h"],
            "tf_roles": {"1h": "HTF", "15m": "LTF"}  # 15m not in timeframes
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "errors" in data["data"]
        assert any("non-existent timeframe" in error for error in data["data"]["errors"])
    
    def test_validate_timeframe_roles_empty_request(self):
        """Test validating with completely empty request."""
        params = {}
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 422  # Validation error for missing required fields
    
    def test_validate_timeframe_roles_malformed_request(self):
        """Test validating with malformed request data."""
        params = {
            "timeframes": "not_a_list",  # Should be a list
            "tf_roles": "not_a_dict"     # Should be a dict
        }
        response = client.post("/api/v1/markets/timeframes/validate", json=params)
        assert response.status_code == 422  # Validation error for wrong types


class TestMarketsTimeframesAPIStructure:
    """Test API response structure and data types."""
    
    def test_timeframes_response_structure(self):
        """Test that timeframes endpoint returns correct structure."""
        response = client.get("/api/v1/markets/timeframes")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check top-level structure
        assert "timeframes" in data
        assert "default_htf" in data
        assert "default_ltf" in data
        assert "role_constraints" in data
        
        # Check data types
        assert isinstance(data["timeframes"], list)
        assert isinstance(data["default_htf"], str)
        assert isinstance(data["default_ltf"], str)
        assert isinstance(data["role_constraints"], list)
        
        # Check timeframe structure
        for tf in data["timeframes"]:
            assert isinstance(tf["timeframe"], str)
            assert isinstance(tf["description"], str)
            assert isinstance(tf["minutes"], int)
            assert isinstance(tf["supported_roles"], list)
            assert isinstance(tf["is_active"], bool)
            
            # Check that minutes is positive
            assert tf["minutes"] > 0
            
            # Check that supported_roles contains valid role values
            for role in tf["supported_roles"]:
                assert role in ["HTF", "LTF"]
    
    def test_role_constraints_response_structure(self):
        """Test that role constraints endpoint returns correct structure."""
        response = client.get("/api/v1/markets/timeframes/roles")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        for constraint in data:
            assert "role" in constraint
            assert "min_timeframe" in constraint
            assert "max_timeframe" in constraint
            assert "description" in constraint
            
            # Check data types
            assert isinstance(constraint["role"], str)
            assert isinstance(constraint["min_timeframe"], str)
            assert isinstance(constraint["max_timeframe"], str)
            assert isinstance(constraint["description"], str)
            
            # Check that role is valid
            assert constraint["role"] in ["HTF", "LTF"]
    
    def test_specific_timeframe_response_structure(self):
        """Test that specific timeframe endpoint returns correct structure."""
        response = client.get("/api/v1/markets/timeframes/1h")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check structure
        assert "timeframe" in data
        assert "description" in data
        assert "minutes" in data
        assert "supported_roles" in data
        assert "is_active" in data
        
        # Check data types
        assert isinstance(data["timeframe"], str)
        assert isinstance(data["description"], str)
        assert isinstance(data["minutes"], int)
        assert isinstance(data["supported_roles"], list)
        assert isinstance(data["is_active"], bool)
        
        # Check specific values for 1h
        assert data["timeframe"] == "1h"
        assert data["minutes"] == 60
        assert data["is_active"] is True 
