#!/usr/bin/env python3
"""
Demonstration of the backtests package functionality.

This script shows how to use the various components of the backtests package
without requiring backtrader or live trading.
"""

import asyncio
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to Python path so we can import from it
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import backtests components
from backtests.storage import BacktestStorage
from backtests.metrics import BacktestMetrics
from backtests.integrity import DataIntegrityChecker
from backtests.models import BacktestConfig, BacktestResult


async def demo_storage():
    """Demonstrate storage functionality."""
    print("=== Storage Demo ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = BacktestStorage(data_dir=temp_dir)
        print(f"Storage initialized at: {temp_dir}")
        
        # Create a sample backtest result
        config = BacktestConfig(
            symbol="BTCUSDT",
            strategy_name="SMC",
            timeframe="1h",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            initial_cash=10000.0
        )
        
        result = BacktestResult(
            id="demo_backtest_001",
            config=config,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=120.5,
            final_value=10500.0,
            total_return=5.0,
            max_drawdown=2.0,
            sharpe_ratio=1.5,
            total_trades=25,
            win_rate=64.0,
            profit_factor=1.8,
            avg_trade=20.0,
            max_consecutive_losses=3,
            status="completed"
        )
        
        # Save the result
        save_path = storage.save_backtest_result(result)
        print(f"Saved backtest result to: {save_path}")
        
        # Load the result
        loaded_result = storage.load_backtest_result("demo_backtest_001")
        print(f"Loaded backtest result: {loaded_result.id}")
        print(f"  Symbol: {loaded_result.config.symbol}")
        print(f"  Strategy: {loaded_result.config.strategy_name}")
        print(f"  Final Value: ${loaded_result.final_value:,.2f}")
        print(f"  Total Return: {loaded_result.total_return:.2f}%")
        print(f"  Win Rate: {loaded_result.win_rate:.1f}%")
        
        # List all results
        results = storage.list_backtest_results()
        print(f"Total backtest results: {len(results)}")
        
        # Get storage stats
        stats = storage.get_storage_stats()
        print(f"Storage stats: {stats}")


def demo_metrics():
    """Demonstrate metrics calculation."""
    print("\n=== Metrics Demo ===")
    
    metrics = BacktestMetrics()
    
    # Sample trade data
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
        },
        {
            "entry_date": datetime(2024, 1, 1, 14, 0, 0),
            "exit_date": datetime(2024, 1, 1, 15, 0, 0),
            "entry_price": 105.0,
            "exit_price": 115.0,
            "size": 1.0,
            "pnl": 10.0
        }
    ]
    
    # Calculate metrics
    detailed_metrics = metrics.calculate_all_metrics(
        trades=trades,
        initial_capital=10000.0,
        final_capital=10015.0,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31)
    )
    
    print("Performance Metrics:")
    perf = detailed_metrics["performance"]
    print(f"  Total Trades: {perf['total_trades']}")
    print(f"  Win Rate: {perf['win_rate']:.1f}%")
    print(f"  Total Return: {perf['total_return_pct']:.2f}%")
    print(f"  Profit Factor: {perf['profit_factor']:.2f}")
    print(f"  Average Trade: ${perf['avg_trade']:.2f}")
    
    print("\nRisk Metrics:")
    risk = detailed_metrics["risk"]
    print(f"  Max Drawdown: {risk['max_drawdown']:.2f}%")
    print(f"  VaR 95%: ${risk['var_95']:.2f}")
    print(f"  Expected Shortfall: ${risk['expected_shortfall']:.2f}")
    
    print("\nAdditional Metrics:")
    additional = detailed_metrics["additional"]
    print(f"  Total Commission: ${additional['total_commission']:.2f}")
    print(f"  Total Slippage: ${additional['total_slippage']:.2f}")
    print(f"  Long Trades: {additional['long_trades_count']}")
    print(f"  Short Trades: {additional['short_trades_count']}")


def demo_integrity():
    """Demonstrate data integrity checking."""
    print("\n=== Data Integrity Demo ===")
    
    checker = DataIntegrityChecker()
    
    # Create sample data with some issues
    import pandas as pd
    import numpy as np
    
    # Sample OHLCV data
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    data = {
        'timestamp': dates,
        'open': np.random.uniform(100, 200, 100),
        'high': np.random.uniform(100, 200, 100),
        'low': np.random.uniform(100, 200, 100),
        'close': np.random.uniform(100, 200, 100),
        'volume': np.random.uniform(1000, 10000, 100)
    }
    
    df = pd.DataFrame(data)
    
    # Introduce some data quality issues
    df.loc[10, 'high'] = 0  # Invalid price
    df.loc[20, 'volume'] = -1000  # Negative volume
    df.loc[30:35, 'timestamp'] = df.loc[30:35, 'timestamp'] + pd.Timedelta(hours=2)  # Gap
    
    # Check integrity
    report = checker.check_data_integrity(
        df=df,
        symbol="BTCUSDT",
        timeframe="1h",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 5)
    )
    
    print(f"Data Integrity Report for BTCUSDT (1h):")
    print(f"  Total Candles: {report.total_candles}")
    print(f"  Expected Candles: {report.expected_candles}")
    print(f"  Missing Candles: {report.missing_candles}")
    print(f"  Duplicate Candles: {report.duplicate_candles}")
    print(f"  Invalid Candles: {report.invalid_candles}")
    print(f"  Data Completeness: {report.data_completeness:.1f}%")
    print(f"  Summary: {report.summary}")
    
    if report.issues:
        print(f"\nFound {len(report.issues)} issues:")
        for i, issue in enumerate(report.issues[:5]):  # Show first 5 issues
            print(f"  {i+1}. {issue.issue_type} ({issue.severity}): {issue.description}")
    
    # Fix common issues
    print("\nFixing common data issues...")
    df_fixed = checker.fix_common_issues(df, "1h")
    print(f"Fixed data shape: {df_fixed.shape}")


async def main():
    """Run all demonstrations."""
    print("Backtests Package Demonstration")
    print("=" * 50)
    
    try:
        await demo_storage()
        demo_metrics()
        demo_integrity()
        
        print("\n" + "=" * 50)
        print("All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
