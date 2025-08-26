"""Tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Trading Bot API"
    assert data["version"] == "1.0.0"


def test_api_root_endpoint():
    """Test the API root endpoint."""
    response = client.get("/api/v1")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Trading Bot API v1"
    assert "endpoints" in data


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/api/v1/status/health")
    assert response.status_code == 200
    data = response.json()
    # Health check can be unhealthy if database is not initialized in tests
    assert data["status"] in ["healthy", "unhealthy", "degraded"]
    assert "version" in data
    assert "uptime" in data


def test_get_pairs():
    """Test getting trading pairs."""
    response = client.get("/api/v1/pairs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


def test_create_pair():
    """Test creating a trading pair."""
    pair_data = {
        "symbol": "BTCUSDT",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "is_active": True
    }
    response = client.post("/api/v1/pairs", json=pair_data)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTCUSDT"
    assert data["base_asset"] == "BTC"


def test_get_signals():
    """Test getting signals."""
    response = client.get("/api/v1/signals")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_get_backtests():
    """Test getting backtests."""
    response = client.get("/api/v1/backtests")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_get_settings():
    """Test getting settings."""
    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    data = response.json()
    assert "trading_enabled" in data
    assert "order_confirmation_required" in data


def test_orders_requires_trading_enabled():
    """Test that orders endpoint requires trading to be enabled."""
    response = client.get("/api/v1/orders")
    assert response.status_code == 403
    data = response.json()
    assert "Trading is not enabled" in data["detail"]


def test_notifications_requires_config():
    """Test that notifications endpoint requires proper configuration."""
    response = client.post("/api/v1/notifications/test", json={
        "message": "Test message",
        "notification_type": "test"
    })
    assert response.status_code == 400
    data = response.json()
    assert "Telegram notifications are not enabled" in data["detail"]


def test_correlation_id_header():
    """Test that correlation ID is added to response headers."""
    response = client.get("/api/v1/status/health")
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    correlation_id = response.headers["X-Correlation-ID"]
    assert correlation_id is not None
    assert len(correlation_id) > 0


if __name__ == "__main__":
    pytest.main([__file__])
