"""
Tests for multi-timeframe schema validations and new Pydantic models.

This module tests:
- TimeframeRole enum validation
- TimeframeConstraint validation
- StrategyMetadata validation
- BacktestRequest multi-timeframe validation
- BacktestResult multi-timeframe validation
- AvailableTimeframe and AvailableTimeframes validation
- StrategyInfo validation
"""

import pytest
from pydantic import ValidationError
from src.api.schemas import (
    TimeframeRole,
    TimeframeConstraint,
    StrategyMetadata,
    BacktestRequest,
    BacktestResult,
    AvailableTimeframe,
    AvailableTimeframes,
    StrategyInfo,
    APIResponse
)


class TestTimeframeRole:
    """Test TimeframeRole enum."""
    
    def test_timeframe_role_values(self):
        """Test that TimeframeRole has correct values."""
        assert TimeframeRole.HTF == "HTF"
        assert TimeframeRole.LTF == "LTF"
    
    def test_timeframe_role_membership(self):
        """Test that TimeframeRole values are valid."""
        assert TimeframeRole.HTF in TimeframeRole
        assert TimeframeRole.LTF in TimeframeRole
        assert "INVALID" not in [role.value for role in TimeframeRole]


class TestTimeframeConstraint:
    """Test TimeframeConstraint model validation."""
    
    def test_valid_timeframe_constraint(self):
        """Test creating a valid TimeframeConstraint."""
        constraint = TimeframeConstraint(
            role=TimeframeRole.HTF,
            min_timeframe="1h",
            max_timeframe="1d",
            description="Higher timeframes for trend analysis"
        )
        assert constraint.role == TimeframeRole.HTF
        assert constraint.min_timeframe == "1h"
        assert constraint.max_timeframe == "1d"
        assert constraint.description == "Higher timeframes for trend analysis"
    
    def test_invalid_timeframe_format_min(self):
        """Test that invalid min_timeframe format raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TimeframeConstraint(
                role=TimeframeRole.HTF,
                min_timeframe="invalid",
                max_timeframe="1d",
                description="Test"
            )
        assert "Timeframe must be in format" in str(exc_info.value)
    
    def test_invalid_timeframe_format_max(self):
        """Test that invalid max_timeframe format raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TimeframeConstraint(
                role=TimeframeRole.HTF,
                min_timeframe="1h",
                max_timeframe="invalid",
                description="Test"
            )
        assert "Timeframe must be in format" in str(exc_info.value)
    
    def test_valid_timeframe_formats(self):
        """Test various valid timeframe formats."""
        valid_formats = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]  # Removed "1w" as it's not supported
        for tf in valid_formats:
            constraint = TimeframeConstraint(
                role=TimeframeRole.LTF,
                min_timeframe=tf,
                max_timeframe=tf,
                description="Test"
            )
            assert constraint.min_timeframe == tf
            assert constraint.max_timeframe == tf


class TestStrategyMetadata:
    """Test StrategyMetadata model validation."""
    
    def test_valid_strategy_metadata(self):
        """Test creating valid StrategyMetadata."""
        metadata = StrategyMetadata(
            name="test_strategy",
            version="1.0.0",
            description="Test strategy",
            required_roles=[TimeframeRole.HTF, TimeframeRole.LTF],
            role_constraints=[
                TimeframeConstraint(
                    role=TimeframeRole.HTF,
                    min_timeframe="1h",
                    max_timeframe="1d",
                    description="HTF constraint"
                ),
                TimeframeConstraint(
                    role=TimeframeRole.LTF,
                    min_timeframe="1m",
                    max_timeframe="30m",
                    description="LTF constraint"
                )
            ]
        )
        assert metadata.name == "test_strategy"
        assert len(metadata.required_roles) == 2
        assert len(metadata.role_constraints) == 2
    
    def test_duplicate_roles_validation(self):
        """Test that duplicate roles are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            StrategyMetadata(
                name="test_strategy",
                version="1.0.0",
                description="Test strategy",
                required_roles=[TimeframeRole.HTF, TimeframeRole.HTF],
                role_constraints=[]
            )
        assert "required roles must be unique" in str(exc_info.value).lower()
    
    def test_duplicate_role_constraints_validation(self):
        """Test that duplicate role constraints are rejected."""
        constraint = TimeframeConstraint(
            role=TimeframeRole.HTF,
            min_timeframe="1h",
            max_timeframe="1d",
            description="HTF constraint"
        )
        with pytest.raises(ValidationError) as exc_info:
            StrategyMetadata(
                name="test_strategy",
                version="1.0.0",
                description="Test strategy",
                required_roles=[TimeframeRole.HTF],
                role_constraints=[constraint, constraint]
            )
        assert "multiple constraints defined for role" in str(exc_info.value).lower()


class TestBacktestRequestMultiTimeframe:
    """Test BacktestRequest multi-timeframe validation."""
    
    def test_valid_multi_timeframe_request(self):
        """Test creating a valid multi-timeframe backtest request."""
        request = BacktestRequest(
            strategy="SMCSignalStrategy",
            pairs=["BTCUSDT"],
            timeframes=["1h", "15m"],
            tf_roles={"1h": TimeframeRole.HTF, "15m": TimeframeRole.LTF},
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=10000.0
        )
        assert request.strategy == "SMCSignalStrategy"
        assert request.pairs == ["BTCUSDT"]
        assert request.timeframes == ["1h", "15m"]
        assert request.tf_roles == {"1h": TimeframeRole.HTF, "15m": TimeframeRole.LTF}
    
    def test_backward_compatibility_legacy_fields(self):
        """Test that legacy fields are accepted for backward compatibility."""
        request = BacktestRequest(
            strategy="SMCSignalStrategy",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=10000.0,
            # Legacy fields only
            pair="BTCUSDT",
            timeframe="1h"
        )
        assert request.pair == "BTCUSDT"
        assert request.timeframe == "1h"
        assert request.pairs is None
        assert request.timeframes is None
        assert request.tf_roles is None
    
    def test_empty_timeframes_validation(self):
        """Test that empty timeframes list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestRequest(
                strategy="SMCSignalStrategy",
                pairs=["BTCUSDT"],
                timeframes=[],
                tf_roles={},
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=10000.0
            )
        assert "at least one timeframe" in str(exc_info.value).lower()
    
    def test_duplicate_timeframes_validation(self):
        """Test that duplicate timeframes are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestRequest(
                strategy="SMCSignalStrategy",
                pairs=["BTCUSDT"],
                timeframes=["1h", "1h"],
                tf_roles={"1h": TimeframeRole.LTF},
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=10000.0
            )
        assert "duplicate timeframes" in str(exc_info.value).lower()
    
    def test_invalid_timeframe_format(self):
        """Test that invalid timeframe format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestRequest(
                strategy="SMCSignalStrategy",
                pairs=["BTCUSDT"],
                timeframes=["invalid"],
                tf_roles={"invalid": TimeframeRole.LTF},
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=10000.0
            )
        assert "invalid timeframe format" in str(exc_info.value).lower()
    
    def test_empty_pairs_validation(self):
        """Test that empty pairs list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestRequest(
                strategy="SMCSignalStrategy",
                pairs=[],
                timeframes=["1h"],
                tf_roles={"1h": TimeframeRole.LTF},
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=10000.0
            )
        assert "at least one trading pair must be specified" in str(exc_info.value).lower()
    
    def test_duplicate_pairs_validation(self):
        """Test that duplicate pairs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestRequest(
                strategy="SMCSignalStrategy",
                pairs=["BTCUSDT", "BTCUSDT"],
                timeframes=["1h"],
                tf_roles={"1h": TimeframeRole.LTF},
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=10000.0
            )
        assert "duplicate trading pairs are not allowed" in str(exc_info.value).lower()
    
    def test_empty_strategy_validation(self):
        """Test that empty strategy name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestRequest(
                strategy="",
                pairs=["BTCUSDT"],
                timeframes=["1h"],
                tf_roles={"1h": TimeframeRole.LTF},
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=10000.0
            )
        assert "strategy name must not be empty" in str(exc_info.value).lower()


class TestBacktestResultMultiTimeframe:
    """Test BacktestResult multi-timeframe validation."""
    
    def test_valid_multi_timeframe_result(self):
        """Test creating a valid multi-timeframe backtest result."""
        result = BacktestResult(
            id="550e8400-e29b-41d4-a716-446655440000",  # Valid UUID
            strategy="SMCSignalStrategy",
            pairs=["BTCUSDT"],
            timeframes=["1h", "15m"],
            tf_roles={"1h": TimeframeRole.HTF, "15m": TimeframeRole.LTF},
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_balance=10000.0,
            final_balance=11000.0,
            total_return=0.1,
            win_rate=0.6,
            total_trades=100,
            profitable_trades=60,
            max_drawdown=0.05,
            sharpe_ratio=1.2,
            profit_factor=1.5,
            avg_trade=10.0,
            max_consecutive_losses=3,
            status="completed"
        )
        assert result.strategy == "SMCSignalStrategy"
        assert result.pairs == ["BTCUSDT"]
        assert result.timeframes == ["1h", "15m"]
        assert result.tf_roles == {"1h": TimeframeRole.HTF, "15m": TimeframeRole.LTF}
    
    def test_backward_compatibility_legacy_fields(self):
        """Test that legacy fields are accepted for backward compatibility."""
        result = BacktestResult(
            id="550e8400-e29b-41d4-a716-446655440000",  # Valid UUID
            strategy="SMCSignalStrategy",
            pairs=["BTCUSDT"],
            timeframes=["1h"],
            tf_roles={"1h": TimeframeRole.LTF},
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_balance=10000.0,
            final_balance=11000.0,
            total_return=0.1,
            win_rate=0.6,
            total_trades=100,
            profitable_trades=60,
            max_drawdown=0.05,
            sharpe_ratio=1.2,
            profit_factor=1.5,
            avg_trade=10.0,
            max_consecutive_losses=3,
            status="completed",
            # Legacy fields
            pair="BTCUSDT",
            timeframe="1h",
            initial_capital=10000.0
        )
        assert result.pair == "BTCUSDT"
        assert result.timeframe == "1h"
        assert result.initial_capital == 10000.0


class TestAvailableTimeframe:
    """Test AvailableTimeframe model."""
    
    def test_valid_available_timeframe(self):
        """Test creating a valid AvailableTimeframe."""
        tf = AvailableTimeframe(
            timeframe="1h",
            description="One hour candles",
            minutes=60,
            supported_roles=[TimeframeRole.HTF, TimeframeRole.LTF],
            is_active=True
        )
        assert tf.timeframe == "1h"
        assert tf.description == "One hour candles"
        assert tf.minutes == 60
        assert tf.supported_roles == [TimeframeRole.HTF, TimeframeRole.LTF]
        assert tf.is_active is True


class TestAvailableTimeframes:
    """Test AvailableTimeframes model."""
    
    def test_valid_available_timeframes(self):
        """Test creating valid AvailableTimeframes."""
        timeframes = [
            AvailableTimeframe(
                timeframe="1h",
                description="One hour candles",
                minutes=60,
                supported_roles=[TimeframeRole.HTF],
                is_active=True
            ),
            AvailableTimeframe(
                timeframe="15m",
                description="Fifteen minute candles",
                minutes=15,
                supported_roles=[TimeframeRole.LTF],
                is_active=True
            )
        ]
        
        constraints = [
            TimeframeConstraint(
                role=TimeframeRole.HTF,
                min_timeframe="1h",
                max_timeframe="1d",
                description="HTF constraint"
            )
        ]
        
        available = AvailableTimeframes(
            timeframes=timeframes,
            default_htf="1h",
            default_ltf="15m",
            role_constraints=constraints
        )
        
        assert len(available.timeframes) == 2
        assert available.default_htf == "1h"
        assert available.default_ltf == "15m"
        assert len(available.role_constraints) == 1


class TestStrategyInfo:
    """Test StrategyInfo model."""
    
    def test_valid_strategy_info(self):
        """Test creating a valid StrategyInfo."""
        info = StrategyInfo(
            name="SMCSignalStrategy",
            version="1.0.0",
            description="Smart Money Concepts strategy",
            required_roles=[TimeframeRole.HTF, TimeframeRole.LTF],
            role_constraints=[
                TimeframeConstraint(
                    role=TimeframeRole.HTF,
                    min_timeframe="1h",
                    max_timeframe="1d",
                    description="HTF constraint"
                )
            ],
            parameters={"risk_percent": 2.0, "leverage": 10},
            is_active=True
        )
        assert info.name == "SMCSignalStrategy"
        assert len(info.required_roles) == 2
        assert len(info.role_constraints) == 1
        assert info.parameters["risk_percent"] == 2.0
        assert info.is_active is True


class TestAPIResponse:
    """Test APIResponse model."""
    
    def test_success_response(self):
        """Test creating a success API response."""
        response = APIResponse(
            success=True,
            data={"message": "Success"},
            message="Operation completed successfully"
        )
        assert response.success is True
        assert response.data["message"] == "Success"
        assert response.message == "Operation completed successfully"
    
    def test_error_response(self):
        """Test creating an error API response."""
        response = APIResponse(
            success=False,
            data={"error": "Validation failed"},
            message="Invalid input",
            error="Field 'timeframe' is required"
        )
        assert response.success is False
        assert response.data["error"] == "Validation failed"
        assert response.message == "Invalid input"
        assert response.error == "Field 'timeframe' is required"
