#!/usr/bin/env python3
"""Test script for View-Only mode functionality."""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.utils.trading_state import trading_state
from app.config import settings


def test_trading_state():
    """Test the trading state functionality."""
    print("🧪 Testing View-Only Mode Implementation")
    print("=" * 50)
    
    # Test 1: Check current trading state
    print(f"1. Current Trading Mode: {trading_state.mode}")
    print(f"   Trading Enabled: {trading_state.trading_enabled}")
    print(f"   Has API Keys: {trading_state.has_api_keys}")
    print(f"   Security Configured: {trading_state.security_configured}")
    print(f"   Can Trade: {trading_state.can_trade()}")
    
    # Test 2: Check configuration
    print(f"\n2. Configuration Status:")
    print(f"   API Key Present: {bool(settings.binance_api_key)}")
    print(f"   Secret Key Present: {bool(settings.binance_secret_key)}")
    print(f"   Execution Enabled: {settings.execution_enabled}")
    print(f"   Shared Secret Present: {bool(settings.shared_secret)}")
    
    # Test 3: Test status info
    print(f"\n3. Status Information:")
    status_info = trading_state.get_status_info()
    for key, value in status_info.items():
        if key == 'setup_required':
            print(f"   {key}: {', '.join(value) if value else 'None'}")
        else:
            print(f"   {key}: {value}")
    
    # Test 4: Test logging (this will show in console)
    print(f"\n4. Testing Trade Attempt Logging:")
    trading_state.log_trade_attempt("test_operation", "Test trade attempt")
    
    # Test 5: Test capabilities
    print(f"\n5. Capability Checks:")
    print(f"   Can Place Orders: {trading_state.can_place_orders()}")
    print(f"   Can Manage Positions: {trading_state.can_manage_positions()}")
    
    # Test 6: Security status
    print(f"\n6. Security Status:")
    if trading_state.security_configured:
        print(f"   ✓ Enhanced security enabled with shared secret")
    else:
        print(f"   ⚠ Running in basic security mode (no shared secret)")
    
    print("\n✅ View-Only Mode Test Completed!")
    print("\nTo enable full functionality:")
    print("1. Set BINANCE_API_KEY and BINANCE_SECRET_KEY in .env")
    print("2. Set EXECUTION_ENABLED=true in .env")
    print("3. Set SHARED_SECRET=your_secret_here in .env (optional but recommended)")
    print("4. Restart the application")


if __name__ == "__main__":
    test_trading_state()
