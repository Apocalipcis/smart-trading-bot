"""Backtest runner using Backtrader Cerebro."""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import backtrader as bt
import pandas as pd

from .models import BacktestConfig, BacktestResult
from ..data.feed import BinanceDataFeed
from ..strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


class BacktestRunner:
    """Runs backtests using Backtrader Cerebro."""
    
    def __init__(self, data_dir: str = "/data"):
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
    
    def _create_data_feed(self, config: BacktestConfig) -> BinanceDataFeed:
        """Create data feed for the backtest."""
        # Convert timeframe to Backtrader format
        timeframe_map = {
            "1m": bt.TimeFrame.Minutes,
            "5m": bt.TimeFrame.Minutes,
            "15m": bt.TimeFrame.Minutes,
            "30m": bt.TimeFrame.Minutes,
            "1h": bt.TimeFrame.Minutes,
            "4h": bt.TimeFrame.Minutes,
            "1d": bt.TimeFrame.Days,
        }
        
        compression_map = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1,
        }
        
        if config.timeframe not in timeframe_map:
            raise ValueError(f"Unsupported timeframe: {config.timeframe}")
            
        # Create data feed
        data_feed = BinanceDataFeed(
            symbol=config.symbol,
            timeframe=timeframe_map[config.timeframe],
            compression=compression_map[config.timeframe],
            fromdate=config.start_date,
            todate=config.end_date,
            data_dir=self.data_dir,
        )
        
        return data_feed
    
    def _get_strategy_class(self, strategy_name: str) -> type:
        """Get strategy class by name."""
        # This will be implemented when strategies package is created
        # For now, return a placeholder
        from ..strategies.base import BaseStrategy
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
        
        # Get analyzer results
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()
        returns = strat.analyzers.returns.get_analysis()
        
        # Calculate metrics
        metrics = {
            "final_value": final_value,
            "total_return": total_return,
            "max_drawdown": drawdown.get("max", {}).get("drawdown", 0) * 100,
            "sharpe_ratio": sharpe.get("sharperatio", 0),
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
        
        # Extract trade information
        for trade in strat.trades:
            trade_info = {
                "entry_date": trade.dtopen,
                "exit_date": trade.dtclose,
                "entry_price": trade.price,
                "exit_price": trade.pclose,
                "size": trade.size,
                "pnl": trade.pnl,
                "pnl_comm": trade.pnlcomm,
                "status": "closed" if trade.isclosed else "open",
            }
            trades.append(trade_info)
            
        return trades
    
    def get_portfolio_history(self) -> List[Dict[str, Any]]:
        """Get portfolio value history from the last backtest."""
        if not self.cerebro:
            return []
            
        # This would require adding a portfolio analyzer
        # For now, return empty list
        return []
