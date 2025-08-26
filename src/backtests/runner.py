"""Backtest runner using Backtrader Cerebro."""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import backtrader as bt
import pandas as pd
import pyarrow.parquet as pq

from .models import BacktestConfig, BacktestResult
from ..strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


class BacktestRunner:
    """Runs backtests using Backtrader Cerebro."""
    
    def __init__(self, data_dir: str = None):
        # Use environment variable or default based on context
        if data_dir is None:
            import os
            data_dir = os.getenv("DATA_DIR", "data")
        self.data_dir = Path(data_dir)
        self.cerebro = None
        
    def _setup_cerebro(self, config: BacktestConfig) -> bt.Cerebro:
        """Set up Cerebro with the given configuration."""
        cerebro = bt.Cerebro()
        
        # Set initial cash
        cerebro.broker.setcash(config.initial_cash)
        
        # Set commission
        cerebro.broker.setcommission(commission=config.commission)
        
        # Set slippage
        cerebro.broker.set_slippage_perc(config.slippage)
        
        # Set random seed for reproducibility
        if config.random_seed is not None:
            cerebro.runopt(seed=config.random_seed)
            
        # Add data feed
        data_feed = self._create_data_feed(config)
        cerebro.adddata(data_feed)
        
        # Add strategy
        strategy_class = self._get_strategy_class(config.strategy_name)
        cerebro.addstrategy(strategy_class, **config.strategy_params)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        
        return cerebro
    
    def _load_parquet_data(self, config: BacktestConfig) -> pd.DataFrame:
        """Load data from parquet file and prepare it for Backtrader."""
        # Construct file path
        file_path = self.data_dir / 'candles' / 'binance_futures' / config.symbol / f"{config.timeframe}.parquet"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        logger.info(f"Loading data from {file_path}")
        
        # Read Parquet file
        table = pq.read_table(file_path)
        df = table.to_pandas()
        
        logger.info(f"Loaded DataFrame with shape: {df.shape}, columns: {list(df.columns)}")
        
        # Check if datetime is already the index
        if df.index.name == 'datetime' or isinstance(df.index, pd.DatetimeIndex):
            # Data already has datetime as index, no need to convert
            pass
        elif 'open_time' in df.columns:
            # Convert timestamp to datetime
            df['datetime'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
            df.set_index('datetime', inplace=True)
        elif 'datetime' in df.columns:
            # Convert datetime column to index
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
        else:
            raise ValueError("No datetime column or index found in data")
        
        # Sort by datetime to ensure chronological order
        df.sort_index(inplace=True)
        
        # Filter by date range if specified
        if config.start_date:
            # Convert start_date to UTC timezone if it's naive
            start_date = config.start_date
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=pd.Timestamp.utcnow().tz)
            df = df[df.index >= start_date]
        if config.end_date:
            # Convert end_date to UTC timezone if it's naive
            end_date = config.end_date
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=pd.Timestamp.utcnow().tz)
            df = df[df.index <= end_date]
        
        # Ensure we have the required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Validate data integrity
        if len(df) == 0:
            raise ValueError("No data available after filtering")
        
        if df.isnull().any().any():
            raise ValueError("Data contains null values")
        
        logger.info(f"Prepared data with {len(df)} candles from {df.index[0]} to {df.index[-1]}")
        
        return df
    
    def _create_data_feed(self, config: BacktestConfig) -> bt.feeds.PandasData:
        """Create data feed for the backtest using standard Backtrader PandasData."""
        # Load data first
        df = self._load_parquet_data(config)
        
        # Create standard Backtrader PandasData feed
        data_feed = bt.feeds.PandasData(
            dataname=df,
            datetime=None,  # Use index as datetime
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=None
        )
        
        return data_feed
    
    def _get_strategy_class(self, strategy_name: str) -> type:
        """Get strategy class by name."""
        from ..strategies.registry import get_strategy
        from ..strategies.base import BaseStrategy
        
        # Try to get strategy from registry
        strategy_class = get_strategy(strategy_name)
        if strategy_class:
            return strategy_class
        
        # Fallback to direct import for common strategies
        if strategy_name.upper() == 'SMC':
            from ..strategies.smc import SMCStrategy
            return SMCStrategy
        elif strategy_name.upper() == 'SIMPLE_TEST':
            from ..strategies.simple_test import SimpleTestStrategy
            return SimpleTestStrategy
        
        # Default fallback
        logger.warning(f"Strategy '{strategy_name}' not found in registry, using BaseStrategy")
        return BaseStrategy
    
    def _calculate_metrics(self, cerebro: bt.Cerebro, config: BacktestConfig) -> Dict[str, Any]:
        """Calculate backtest metrics from Cerebro results."""
        results = cerebro.run()
        if not results:
            raise RuntimeError("No results from backtest")
            
        strat = results[0]
        
        # Get final portfolio value
        final_value = cerebro.broker.getvalue()
        initial_cash = config.initial_cash
        total_return = ((final_value - initial_cash) / initial_cash) * 100
        
        # Get analyzer results with error handling
        try:
            sharpe = strat.analyzers.sharpe.get_analysis()
        except Exception:
            sharpe = {}
            
        try:
            drawdown = strat.analyzers.drawdown.get_analysis()
        except Exception:
            drawdown = {}
            
        try:
            trades = strat.analyzers.trades.get_analysis()
        except Exception:
            trades = {}
            
        try:
            returns = strat.analyzers.returns.get_analysis()
        except Exception:
            returns = {}
        
        # Calculate metrics with proper None handling
        sharpe_ratio = sharpe.get("sharperatio")
        if sharpe_ratio is None:
            sharpe_ratio = 0.0
        
        metrics = {
            "final_value": final_value,
            "total_return": total_return,
            "max_drawdown": drawdown.get("max", {}).get("drawdown", 0) * 100,
            "sharpe_ratio": sharpe_ratio,
            "total_trades": trades.get("total", {}).get("total", 0),
            "win_rate": 0,
            "profit_factor": 0,
            "avg_trade": 0,
            "max_consecutive_losses": 0,
        }
        
        # Calculate win rate and profit factor
        if metrics["total_trades"] > 0:
            won = trades.get("won", {}).get("total", 0)
            lost = trades.get("lost", {}).get("total", 0)
            
            metrics["win_rate"] = (won / metrics["total_trades"]) * 100 if metrics["total_trades"] > 0 else 0
            
            # Calculate profit factor
            gross_profit = trades.get("won", {}).get("pnl", {}).get("gross", 0)
            gross_loss = abs(trades.get("lost", {}).get("pnl", {}).get("gross", 0))
            
            metrics["profit_factor"] = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Calculate average trade
            total_pnl = trades.get("pnl", {}).get("net", 0)
            metrics["avg_trade"] = total_pnl / metrics["total_trades"]
            
            # Calculate max consecutive losses
            metrics["max_consecutive_losses"] = trades.get("streak", {}).get("current", 0)
        
        return metrics
    
    async def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """Run a backtest with the given configuration."""
        start_time = datetime.utcnow()
        backtest_id = f"{config.symbol}_{config.strategy_name}_{config.timeframe}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"Starting backtest {backtest_id}")
            
            # Set up Cerebro
            self.cerebro = self._setup_cerebro(config)
            
            # Run backtest
            start_exec = datetime.utcnow()
            self.cerebro.run()
            execution_time = (datetime.utcnow() - start_exec).total_seconds()
            
            # Calculate metrics
            metrics = self._calculate_metrics(self.cerebro, config)
            
            # Create result
            result = BacktestResult(
                id=backtest_id,
                config=config,
                start_time=start_time,
                end_time=datetime.utcnow(),
                duration=execution_time,
                status="completed",
                **metrics
            )
            
            logger.info(f"Backtest {backtest_id} completed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Backtest {backtest_id} failed: {str(e)}")
            result = BacktestResult(
                id=backtest_id,
                config=config,
                start_time=start_time,
                end_time=datetime.utcnow(),
                duration=0,
                status="failed",
                error_message=str(e),
                final_value=config.initial_cash,
                total_return=0,
                max_drawdown=0,
                sharpe_ratio=0,
                total_trades=0,
                win_rate=0,
                profit_factor=0,
                avg_trade=0,
                max_consecutive_losses=0,
            )
            return result
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Get detailed trade history from the last backtest."""
        if not self.cerebro:
            return []
            
        results = self.cerebro.run()
        if not results:
            return []
            
        strat = results[0]
        trades = []
        
        # Extract trade information from analyzer
        if hasattr(strat, 'analyzers') and hasattr(strat.analyzers, 'trades'):
            trade_analysis = strat.analyzers.trades.get_analysis()
            # Convert trade analysis to list format
            # This is a simplified version - you might need to adjust based on actual analyzer output
            if trade_analysis:
                trades.append({
                    "analysis": trade_analysis,
                    "status": "completed"
                })
        
        return trades
    
    def get_portfolio_history(self) -> List[Dict[str, Any]]:
        """Get portfolio value history from the last backtest."""
        if not self.cerebro:
            return []
            
        # This would require adding a portfolio analyzer
        # For now, return empty list
        return []
