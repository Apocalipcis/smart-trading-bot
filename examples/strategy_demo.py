#!/usr/bin/env python3
"""
Strategy Package Demonstration

This script demonstrates how to use the strategies package,
including the base strategy class, registry system, and SMC strategy.
"""

import sys
from pathlib import Path

# Add the src directory to Python path so we can import from it
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from strategies.registry import get_registry, StrategyRegistry
from strategies.base import BaseStrategy, Signal
from strategies.smc import SMCStrategy


def demo_strategy_registry():
    """Demonstrate the strategy registry functionality."""
    print("=== Strategy Registry Demo ===")
    
    # Get the global registry
    registry = get_registry()
    print(f"Registry initialized at: {registry.strategies_dir}")
    
    # List all discovered strategies
    strategies = registry.list_strategies()
    print(f"\nDiscovered {len(strategies)} strategies:")
    
    for strategy in strategies:
        print(f"  - {strategy['name']} v{strategy['version']}")
        print(f"    Description: {strategy['description'][:100]}...")
        print(f"    Parameters: {len(strategy['parameters'])} parameters")
        print()
    
    # Get specific strategy information
    if 'SMC' in registry.strategies:
        smc_info = registry.get_strategy_info('SMC')
        print(f"SMC Strategy Details:")
        print(f"  File: {smc_info.file_path}")
        print(f"  Version: {smc_info.version}")
        print(f"  Registration Date: {smc_info.registration_date}")
        print(f"  Parameters: {smc_info.parameters}")
        print()
    
    # Validate strategies
    print("Strategy Validation:")
    for strategy_name in registry.strategies:
        validation = registry.validate_strategy(strategy_name)
        status = "✓ VALID" if validation['valid'] else "✗ INVALID"
        print(f"  {strategy_name}: {status}")
        
        if not validation['valid']:
            for error in validation['errors']:
                print(f"    Error: {error}")
        print()


def demo_smc_strategy():
    """Demonstrate the SMC strategy functionality."""
    print("=== SMC Strategy Demo ===")
    
    # Create SMC strategy class info (not instance)
    print(f"SMC Strategy class loaded successfully")
    print(f"Version: {SMCStrategy.version}")
    print(f"Parameters:")
    
    # Extract parameters safely
    try:
        params_dict = SMCStrategy.params._asdict()
        for param_name, param_value in params_dict.items():
            print(f"  {param_name}: {param_value}")
    except AttributeError:
        # Fallback for different param formats
        try:
            params_dict = dict(SMCStrategy.params)
            for param_name, param_value in params_dict.items():
                print(f"  {param_name}: {param_value}")
        except (TypeError, ValueError):
            print("  Parameters: Unable to extract")
    
    print()
    
    # Show strategy class information
    print("Strategy Class Information:")
    print(f"  Name: {SMCStrategy.__name__}")
    print(f"  Module: {SMCStrategy.__module__}")
    print(f"  Base Classes: {[base.__name__ for base in SMCStrategy.__bases__]}")
    print(f"  Has generate_signals method: {hasattr(SMCStrategy, 'generate_signals')}")
    print()


def demo_signal_generation():
    """Demonstrate signal generation concepts."""
    print("=== Signal Generation Demo ===")
    
    # Create sample signals
    long_signal = Signal(
        side='long',
        entry=100.0,
        stop_loss=95.0,
        take_profit=115.0,
        confidence=0.85,
        metadata={
            'strategy': 'SMC',
            'trend': 'bullish',
            'rsi': 45.0,
            'volume_ratio': 1.8
        }
    )
    
    short_signal = Signal(
        side='short',
        entry=100.0,
        stop_loss=105.0,
        take_profit=85.0,
        confidence=0.75,
        metadata={
            'strategy': 'SMC',
            'trend': 'bearish',
            'rsi': 65.0,
            'volume_ratio': 1.6
        }
    )
    
    print("Sample Long Signal:")
    print(f"  Side: {long_signal.side}")
    print(f"  Entry: ${long_signal.entry:.2f}")
    print(f"  Stop Loss: ${long_signal.stop_loss:.2f}")
    print(f"  Take Profit: ${long_signal.take_profit:.2f}")
    print(f"  Confidence: {long_signal.confidence:.1%}")
    print(f"  Risk-Reward: {(long_signal.take_profit - long_signal.entry) / (long_signal.entry - long_signal.stop_loss):.1f}:1")
    print(f"  Metadata: {long_signal.metadata}")
    print()
    
    print("Sample Short Signal:")
    print(f"  Side: {short_signal.side}")
    print(f"  Entry: ${short_signal.entry:.2f}")
    print(f"  Stop Loss: ${short_signal.stop_loss:.2f}")
    print(f"  Take Profit: ${short_signal.take_profit:.2f}")
    print(f"  Confidence: {short_signal.confidence:.1%}")
    print(f"  Risk-Reward: {(short_signal.entry - short_signal.take_profit) / (short_signal.stop_loss - short_signal.entry):.1f}:1")
    print(f"  Metadata: {short_signal.metadata}")
    print()


def demo_custom_strategy():
    """Demonstrate how to create a custom strategy."""
    print("=== Custom Strategy Demo ===")
    
    class SimpleMovingAverageStrategy(BaseStrategy):
        """
        Simple Moving Average Crossover Strategy.
        
        This is a basic example of how to create a custom strategy
        by inheriting from BaseStrategy.
        """
        
        version = "1.0.0"
        
        params = (
            ('fast_period', 10),
            ('slow_period', 20),
            ('risk_per_trade', 0.02),
            ('min_risk_reward', 2.0),
        )
        
        def __init__(self):
            super().__init__()
            # Strategy-specific initialization would go here
            self.fast_ma = None
            self.slow_ma = None
        
        def generate_signals(self):
            """Generate signals based on moving average crossover."""
            # This is a simplified example - in practice you'd implement
            # actual moving average calculations and crossover logic
            
            # For demo purposes, return a sample signal
            return [
                Signal(
                    side='long',
                    entry=100.0,
                    stop_loss=98.0,
                    take_profit=104.0,
                    confidence=0.7,
                    metadata={
                        'strategy': 'SMA_Crossover',
                        'fast_ma': 101.0,
                        'slow_ma': 99.5
                    }
                )
            ]
    
    # Show custom strategy class info
    print(f"Custom strategy class: {SimpleMovingAverageStrategy.__name__}")
    print(f"Version: {SimpleMovingAverageStrategy.version}")
    print(f"Parameters: {SimpleMovingAverageStrategy.params}")
    
    # Show class structure
    print(f"Base class: {SimpleMovingAverageStrategy.__bases__[0].__name__}")
    print(f"Has generate_signals method: {hasattr(SimpleMovingAverageStrategy, 'generate_signals')}")
    print(f"Method signature: {SimpleMovingAverageStrategy.generate_signals.__doc__}")
    
    print()


def main():
    """Run all demonstrations."""
    print("Strategy Package Demonstration")
    print("=" * 60)
    
    try:
        demo_strategy_registry()
        demo_smc_strategy()
        demo_signal_generation()
        demo_custom_strategy()
        
        print("=" * 60)
        print("All demonstrations completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  ✓ Strategy registry with auto-discovery")
        print("  ✓ Base strategy class with signal contract")
        print("  ✓ SMC strategy implementation")
        print("  ✓ Signal validation and risk management")
        print("  ✓ Custom strategy creation")
        print("  ✓ Parameter management and validation")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
