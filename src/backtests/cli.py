"""Command-line interface for running backtests."""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .runner import BacktestRunner, BacktestConfig
from .storage import BacktestStorage
from .integrity import DataIntegrityChecker
from .metrics import BacktestMetrics

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_date(date_str: str) -> datetime:
    """Parse date string in various formats."""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse date: {date_str}")


def create_backtest_config(args) -> BacktestConfig:
    """Create backtest configuration from command line arguments."""
    # Parse dates
    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)
    
    # Parse strategy parameters
    strategy_params = {}
    if args.strategy_params:
        try:
            strategy_params = json.loads(args.strategy_params)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid strategy parameters JSON: {e}")
            sys.exit(1)
    
    return BacktestConfig(
        symbol=args.symbol,
        strategy_name=args.strategy,
        strategy_params=strategy_params,
        timeframe=args.timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_cash=args.initial_cash,
        commission=args.commission,
        slippage=args.slippage,
        random_seed=args.random_seed,
        leverage=args.leverage,
        funding_rate=args.funding_rate
    )


async def run_backtest(args):
    """Run a backtest with the given configuration."""
    try:
        # Create configuration
        config = create_backtest_config(args)
        
        # Initialize components
        runner = BacktestRunner(data_dir=args.data_dir)
        storage = BacktestStorage(data_dir=args.data_dir)
        
        logger.info(f"Starting backtest for {config.symbol} with {config.strategy_name}")
        logger.info(f"Timeframe: {config.timeframe}")
        logger.info(f"Date range: {config.start_date} to {config.end_date}")
        logger.info(f"Initial capital: ${config.initial_cash:,.2f}")
        
        # Run backtest
        result = await runner.run_backtest(config)
        
        if result.status == "completed":
            logger.info("Backtest completed successfully!")
            logger.info(f"Final value: ${result.final_value:,.2f}")
            logger.info(f"Total return: {result.total_return:.2f}%")
            logger.info(f"Win rate: {result.win_rate:.2f}%")
            logger.info(f"Total trades: {result.total_trades}")
            logger.info(f"Max drawdown: {result.max_drawdown:.2f}%")
            logger.info(f"Sharpe ratio: {result.sharpe_ratio:.2f}")
            
            # Save result
            storage_path = storage.save_backtest_result(result)
            logger.info(f"Results saved to: {storage_path}")
            
            # Save detailed metrics if requested
            if args.save_metrics:
                metrics_calculator = BacktestMetrics()
                trade_history = runner.get_trade_history()
                
                detailed_metrics = metrics_calculator.calculate_all_metrics(
                    trades=trade_history,
                    initial_capital=config.initial_cash,
                    final_capital=result.final_value,
                    start_date=config.start_date,
                    end_date=config.end_date,
                    commission_rate=config.commission,
                    slippage_rate=config.slippage,
                    funding_rate=config.funding_rate
                )
                
                # Save metrics as artifact
                metrics_path = storage.save_artifact(
                    result.id,
                    "detailed_metrics",
                    json.dumps(detailed_metrics, indent=2, default=str),
                    {"type": "detailed_metrics", "version": "1.0"}
                )
                logger.info(f"Detailed metrics saved to: {metrics_path}")
            
            # Check data integrity if requested
            if args.check_integrity:
                logger.info("Checking data integrity...")
                integrity_checker = DataIntegrityChecker()
                
                # This would require loading the actual data used in the backtest
                # For now, just log that integrity checking was requested
                logger.info("Data integrity checking requested (requires data access)")
            
            return result
            
        else:
            logger.error(f"Backtest failed: {result.error_message}")
            return result
            
    except Exception as e:
        logger.error(f"Failed to run backtest: {str(e)}")
        raise


def list_backtests(args):
    """List existing backtest results."""
    try:
        storage = BacktestStorage(data_dir=args.data_dir)
        
        # Apply filters
        symbol = args.symbol if hasattr(args, 'symbol') else None
        strategy = args.strategy if hasattr(args, 'strategy') else None
        start_date = parse_date(args.start_date) if hasattr(args, 'start_date') and args.start_date else None
        end_date = parse_date(args.end_date) if hasattr(args, 'end_date') and args.end_date else None
        
        results = storage.list_backtest_results(
            symbol=symbol,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date
        )
        
        if not results:
            print("No backtest results found.")
            return
        
        print(f"\nFound {len(results)} backtest results:\n")
        print(f"{'ID':<50} {'Symbol':<10} {'Strategy':<15} {'Timeframe':<8} {'Status':<10} {'Return':<10}")
        print("-" * 120)
        
        for result in results:
            print(f"{result.id:<50} {result.config.symbol:<10} {result.config.strategy_name:<15} "
                  f"{result.config.timeframe:<8} {result.status:<10} {result.total_return_pct:>8.2f}%")
        
        print()
        
    except Exception as e:
        logger.error(f"Failed to list backtests: {str(e)}")
        sys.exit(1)


def delete_backtest(args):
    """Delete a backtest result."""
    try:
        storage = BacktestStorage(data_dir=args.data_dir)
        
        if args.delete_all:
            count = storage.delete_all_backtest_results()
            print(f"Deleted {count} backtest results and all artifacts.")
        else:
            success = storage.delete_backtest_result(args.backtest_id)
            if success:
                print(f"Successfully deleted backtest: {args.backtest_id}")
            else:
                print(f"Failed to delete backtest: {args.backtest_id}")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Failed to delete backtest: {str(e)}")
        sys.exit(1)


def show_backtest_details(args):
    """Show detailed information about a specific backtest."""
    try:
        storage = BacktestStorage(data_dir=args.data_dir)
        result = storage.load_backtest_result(args.backtest_id)
        
        if not result:
            print(f"Backtest not found: {args.backtest_id}")
            sys.exit(1)
        
        print(f"\nBacktest Details: {args.backtest_id}")
        print("=" * 60)
        print(f"Symbol: {result.config.symbol}")
        print(f"Strategy: {result.config.strategy_name}")
        print(f"Timeframe: {result.config.timeframe}")
        print(f"Date Range: {result.config.start_date} to {result.config.end_date}")
        print(f"Status: {result.status}")
        print(f"Duration: {result.duration:.2f} seconds")
        print()
        
        if result.status == "completed":
            print("Performance Metrics:")
            print(f"  Initial Capital: ${result.config.initial_cash:,.2f}")
            print(f"  Final Value: ${result.final_value:,.2f}")
            print(f"  Total Return: {result.total_return_pct:.2f}%")
            print(f"  Max Drawdown: {result.max_drawdown:.2f}%")
            print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"  Win Rate: {result.win_rate:.2f}%")
            print(f"  Total Trades: {result.total_trades}")
            print(f"  Profit Factor: {result.profit_factor:.2f}")
            print(f"  Average Trade: ${result.avg_trade:.2f}")
            print(f"  Max Consecutive Losses: {result.max_consecutive_losses}")
        else:
            print(f"Error: {result.error_message}")
        
        print()
        
    except Exception as e:
        logger.error(f"Failed to show backtest details: {str(e)}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Trading Bot Backtest CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a backtest
  python -m src.backtests.cli run --symbol BTCUSDT --strategy SMC --timeframe 1h --start-date 2024-01-01 --end-date 2024-01-31
  
  # List all backtests
  python -m src.backtests.cli list
  
  # Show backtest details
  python -m src.backtests.cli show --backtest-id BTCUSDT_SMC_1h_20240101_120000
  
  # Delete a backtest
  python -m src.backtests.cli delete --backtest-id BTCUSDT_SMC_1h_20240101_120000
        """
    )
    
    parser.add_argument('--data-dir', default='data', help='Data directory path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a backtest')
    run_parser.add_argument('--symbol', required=True, help='Trading pair symbol')
    run_parser.add_argument('--strategy', required=True, help='Strategy name')
    run_parser.add_argument('--timeframe', required=True, choices=['1m', '5m', '15m', '30m', '1h', '4h', '1d'], help='Timeframe')
    run_parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    run_parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    run_parser.add_argument('--initial-cash', type=float, default=10000.0, help='Initial capital')
    run_parser.add_argument('--commission', type=float, default=0.001, help='Commission rate')
    run_parser.add_argument('--slippage', type=float, default=0.0001, help='Slippage rate')
    run_parser.add_argument('--random-seed', type=int, help='Random seed for reproducibility')
    run_parser.add_argument('--leverage', type=float, default=1.0, help='Leverage multiplier')
    run_parser.add_argument('--funding-rate', type=float, default=0.0001, help='Funding rate')
    run_parser.add_argument('--strategy-params', help='Strategy parameters as JSON string')
    run_parser.add_argument('--save-metrics', action='store_true', help='Save detailed metrics')
    run_parser.add_argument('--check-integrity', action='store_true', help='Check data integrity')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List backtest results')
    list_parser.add_argument('--symbol', help='Filter by symbol')
    list_parser.add_argument('--strategy', help='Filter by strategy')
    list_parser.add_argument('--start-date', help='Filter by start date')
    list_parser.add_argument('--end-date', help='Filter by end date')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show backtest details')
    show_parser.add_argument('--backtest-id', required=True, help='Backtest ID')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete backtest results')
    delete_parser.add_argument('--backtest-id', help='Backtest ID to delete')
    delete_parser.add_argument('--delete-all', action='store_true', help='Delete all backtest results')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(args.verbose)
    
    try:
        if args.command == 'run':
            asyncio.run(run_backtest(args))
        elif args.command == 'list':
            list_backtests(args)
        elif args.command == 'show':
            show_backtest_details(args)
        elif args.command == 'delete':
            delete_backtest(args)
        else:
            parser.print_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Operation failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
