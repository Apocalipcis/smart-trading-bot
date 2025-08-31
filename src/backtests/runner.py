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
from .preparation import BacktestDataPreparer, DataPreparationError
try:
    from src.strategies.base import BaseStrategy
except ImportError:
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
        self.data_preparer = BacktestDataPreparer(data_dir)
        
    async def _prepare_data(self, config: BacktestConfig) -> Dict[str, Any]:
        """Prepare all required data before running the backtest."""
        try:
            # Get timeframes to prepare
            timeframes = config.get_primary_timeframes()
            
            logger.info(f"Preparing data for {config.symbol} timeframes: {timeframes}")
            
            # Prepare data using the data preparation module
            preparation_result = await self.data_preparer.prepare_backtest_data(
                symbol=config.symbol,
                timeframes=timeframes,
                start_date=config.start_date,
                end_date=config.end_date,
                force_update=False
            )
            
            # Check for preparation errors
            if preparation_result.get("errors"):
                error_msg = f"Data preparation failed: {'; '.join(preparation_result['errors'])}"
                logger.error(error_msg)
                raise DataPreparationError(error_msg)
            
            logger.info(f"Data preparation completed successfully: {preparation_result['total_files_downloaded']} downloaded, {preparation_result['total_files_reused']} reused")
            
            return preparation_result
            
        except Exception as e:
            logger.error(f"Data preparation failed: {str(e)}")
            raise DataPreparationError(f"Failed to prepare backtest data: {str(e)}")
    
    def _setup_cerebro(self, config: BacktestConfig) -> bt.Cerebro:
        """Set up Cerebro with the given configuration."""
        try:
            cerebro = bt.Cerebro()
            
            # Set initial cash with fallback
            if not hasattr(config, 'initial_cash') or config.initial_cash is None:
                config.initial_cash = 10000.0
            cerebro.broker.setcash(config.initial_cash)
            
            # Set commission with fallback
            if hasattr(config, 'commission') and config.commission is not None:
                cerebro.broker.setcommission(commission=config.commission)
            else:
                cerebro.broker.setcommission(commission=0.001)  # Default commission
            
            # Set slippage with fallback
            if hasattr(config, 'slippage') and config.slippage is not None:
                cerebro.broker.set_slippage_perc(config.slippage)
            else:
                cerebro.broker.set_slippage_perc(0.0001)  # Default slippage
            
            # Set random seed for reproducibility
            if hasattr(config, 'random_seed') and config.random_seed is not None:
                cerebro.runopt(seed=config.random_seed)
                
            # Add data feeds for all timeframes
            data_feeds = self._create_data_feeds(config)
            if not data_feeds:
                raise ValueError("No valid data feeds could be created")
                
            for data_feed in data_feeds:
                cerebro.adddata(data_feed)
            
            # Add strategy
            strategy_class = self._get_strategy_class(config.strategy_name)
            if strategy_class is None:
                raise ValueError(f"Strategy class '{config.strategy_name}' could not be loaded - all import attempts failed")
                
            strategy_params = getattr(config, 'strategy_params', {}) or {}
            cerebro.addstrategy(strategy_class, **strategy_params)
            
            # Add analyzers
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            
            return cerebro
            
        except Exception as e:
            logger.error(f"Failed to setup Cerebro: {str(e)}")
            raise RuntimeError(f"Cerebro setup failed: {str(e)}")
    
    def _create_data_feeds(self, config: BacktestConfig) -> List[bt.feeds.PandasData]:
        """Create data feeds for all timeframes in the configuration."""
        try:
            timeframes = config.get_primary_timeframes()
            if not timeframes:
                raise ValueError("No timeframes specified in configuration")
                
            data_feeds = []
            
            for timeframe in timeframes:
                try:
                    data_feed = self._create_single_data_feed(config, timeframe)
                    if data_feed is not None:
                        data_feeds.append(data_feed)
                        logger.info(f"Created data feed for {timeframe}")
                    else:
                        logger.warning(f"Failed to create data feed for {timeframe}: returned None")
                except Exception as e:
                    logger.error(f"Failed to create data feed for {timeframe}: {str(e)}")
                    # Continue with other timeframes instead of failing completely
                    continue
            
            if not data_feeds:
                raise ValueError("No valid data feeds could be created")
                
            return data_feeds
            
        except Exception as e:
            logger.error(f"Failed to create data feeds: {str(e)}")
            raise
    
    def _create_single_data_feed(self, config: BacktestConfig, timeframe: str) -> Optional[bt.feeds.PandasData]:
        """Create a single data feed for a specific timeframe."""
        try:
            # Load data for this timeframe
            df = self._load_parquet_data(config, timeframe)
            
            if df is None or df.empty:
                logger.warning(f"No data available for timeframe {timeframe}")
                return None
            
            # Ensure required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns for {timeframe}: {missing_columns}")
                return None
            
            # Create Backtrader PandasData feed
            data_feed = bt.feeds.PandasData(
                dataname=df,
                datetime=None,  # Use index as datetime
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest=None,
                name=f"{config.symbol}_{timeframe}"  # Give each feed a unique name
            )
            
            return data_feed
            
        except Exception as e:
            logger.error(f"Failed to create data feed for {timeframe}: {str(e)}")
            return None
    
    def _load_parquet_data(self, config: BacktestConfig, timeframe: str) -> Optional[pd.DataFrame]:
        """Load data from parquet file for a specific timeframe and prepare it for Backtrader."""
        try:
            # Construct file path
            file_path = self.data_dir / 'candles' / 'binance_futures' / config.symbol / f"{timeframe}.parquet"
            
            if not file_path.exists():
                logger.warning(f"Data file not found: {file_path}")
                return None
            
            logger.info(f"Loading {timeframe} data from {file_path}")
            
            # Read Parquet file
            table = pq.read_table(file_path)
            df = table.to_pandas()
            
            if df.empty:
                logger.warning(f"Data file {file_path} is empty")
                return None
            
            logger.info(f"Loaded DataFrame with shape: {df.shape}, columns: {list(df.columns)}")
            
            # Check if datetime is already the index
            if df.index.name == 'datetime' or isinstance(df.index, pd.DatetimeIndex):
                # Data already has datetime as index, no need to convert
                pass
            elif 'open_time' in df.columns:
                # Convert timestamp to datetime
                df['datetime'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
                df.set_index('datetime', inplace=True)
                # Remove the open_time column since it's now the index
                df.drop(columns=['open_time'], inplace=True)
            elif 'datetime' in df.columns:
                # Convert datetime column to index
                df['datetime'] = pd.to_datetime(df['datetime'])
                df.set_index('datetime', inplace=True)
            else:
                logger.warning(f"No datetime column found in {timeframe} data")
                return None
            
            # Ensure data is sorted by datetime
            df.sort_index(inplace=True)
            
            # Remove any rows with NaN values in critical columns
            critical_columns = ['open', 'high', 'low', 'close']
            df = df.dropna(subset=critical_columns)
            
            if df.empty:
                logger.warning(f"After cleaning, no data remains for {timeframe}")
                return None
            
            logger.info(f"Final DataFrame shape after cleaning: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load parquet data for {timeframe}: {str(e)}")
            return None
    
    # Legacy method for backwards compatibility
    def _load_parquet_data_legacy(self, config: BacktestConfig) -> pd.DataFrame:
        """Legacy method to load data from parquet file (maintained for backwards compatibility)."""
        # Use the primary timeframe for legacy compatibility
        primary_timeframe = config.get_primary_timeframe()
        if not primary_timeframe:
            raise ValueError("No timeframe specified in BacktestConfig")
        
        return self._load_parquet_data(config, primary_timeframe)
    
    # Legacy method for backwards compatibility
    def _create_data_feed_legacy(self, config: BacktestConfig) -> bt.feeds.PandasData:
        """Legacy method to create data feed (maintained for backwards compatibility)."""
        # Load data first
        df = self._load_parquet_data_legacy(config)
        
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
    
    def _get_strategy_class(self, strategy_name: str) -> Optional[type]:
        """Get strategy class by name with improved error handling and import resolution."""
        try:
            # First try direct imports with absolute paths to avoid relative import issues
            if strategy_name.upper() == 'SMC':
                try:
                    from src.strategies.smc_signal import SMCSignalStrategy
                    logger.info(f"Successfully loaded SMC Signal strategy via absolute import")
                    return SMCSignalStrategy
                except ImportError:
                    try:
                        from ..strategies.smc_signal import SMCSignalStrategy
                        logger.info(f"Successfully loaded SMC Signal strategy via relative import")
                        return SMCSignalStrategy
                    except ImportError as e:
                        logger.warning(f"Failed to load SMC Signal strategy: {e}")
            elif strategy_name.upper() == 'SIMPLE_TEST':
                try:
                    from src.strategies.simple_test import SimpleTestStrategy
                    logger.info(f"Successfully loaded SimpleTest strategy via absolute import")
                    return SimpleTestStrategy
                except ImportError:
                    try:
                        from ..strategies.simple_test import SimpleTestStrategy
                        logger.info(f"Successfully loaded SimpleTest strategy via relative import")
                        return SimpleTestStrategy
                    except ImportError as e:
                        logger.warning(f"Failed to load SimpleTest strategy: {e}")
            
            elif strategy_name.upper() == 'BASE':
                try:
                    from src.strategies.base import BaseStrategy
                    logger.info(f"Successfully loaded Base strategy via absolute import")
                    return BaseStrategy
                except ImportError:
                    try:
                        from ..strategies.base import BaseStrategy
                        logger.info(f"Successfully loaded Base strategy via relative import")
                        return BaseStrategy
                    except ImportError as e:
                        logger.warning(f"Failed to load Base strategy: {e}")
            
            # Try to get strategy from registry as fallback
            try:
                from ..strategies.registry import get_strategy
                strategy_class = get_strategy(strategy_name)
                if strategy_class:
                    logger.info(f"Successfully loaded strategy '{strategy_name}' from registry")
                    return strategy_class
            except ImportError as e:
                logger.warning(f"Strategy registry not available, skipping registry lookup for '{strategy_name}': {e}")
            except Exception as e:
                logger.warning(f"Failed to load strategy '{strategy_name}' from registry: {e}")
            
            # Try dynamic import with better error handling
            try:
                import importlib
                import sys
                
                # Try multiple import paths
                possible_paths = [
                    f"src.strategies.{strategy_name.lower()}",
                    f"strategies.{strategy_name.lower()}",
                    f"..strategies.{strategy_name.lower()}"
                ]
                
                for module_path in possible_paths:
                    try:
                        module = importlib.import_module(module_path)
                        logger.info(f"Successfully imported module: {module_path}")
                        
                        # Look for class with matching name
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (isinstance(attr, type) and 
                                hasattr(attr, '__bases__') and
                                any('BaseStrategy' in str(base) for base in attr.__bases__)):
                                logger.info(f"Found strategy '{strategy_name}' via dynamic import: {attr_name}")
                                return attr
                                
                    except ImportError as e:
                        logger.debug(f"Failed to import {module_path}: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Error processing module {module_path}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Dynamic import failed for '{strategy_name}': {e}")
            
            # Final fallback to BaseStrategy with better error handling
            logger.warning(f"Strategy '{strategy_name}' not found, using BaseStrategy as fallback")
            try:
                from src.strategies.base import BaseStrategy
                logger.info("Successfully loaded BaseStrategy via absolute import as fallback")
                return BaseStrategy
            except ImportError:
                try:
                    from ..strategies.base import BaseStrategy
                    logger.info("Successfully loaded BaseStrategy via relative import as fallback")
                    return BaseStrategy
                except ImportError as e:
                    logger.error(f"Critical error: Even BaseStrategy import failed - {e}")
                    # Return None to indicate complete failure
                    return None
            
        except Exception as e:
            logger.error(f"Critical error in strategy loading for '{strategy_name}': {e}")
            # Return BaseStrategy as ultimate fallback
            try:
                from src.strategies.base import BaseStrategy
                return BaseStrategy
            except ImportError:
                try:
                    from ..strategies.base import BaseStrategy
                    return BaseStrategy
                except ImportError:
                    logger.error("Even BaseStrategy import failed - this is a critical error")
                    return None
    
    def _calculate_metrics_from_results(self, results, config: BacktestConfig) -> Dict[str, Any]:
        """Calculate backtest metrics from Cerebro results."""
        if not results:
            raise RuntimeError("No results from backtest")
            
        strat = results[0]
        
        # Get final portfolio value
        final_value = self.cerebro.broker.getvalue()
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
            trades_analyzer = strat.analyzers.trades.get_analysis()
        except Exception:
            trades_analyzer = {}
            
        try:
            returns = strat.analyzers.returns.get_analysis()
        except Exception:
            returns = {}
        
        # Calculate metrics with proper None handling
        sharpe_ratio = sharpe.get("sharperatio")
        if sharpe_ratio is None:
            sharpe_ratio = 0.0
        
        # Get detailed trade information
        trades = self._get_detailed_trades(strat)
        
        # Calculate additional required metrics
        win_rate = self._calculate_win_rate(trades)
        profitable_trades = len([t for t in trades if t.get("pnl", 0) > 0])
        
        # Calculate profit factor
        total_profit = sum([t.get("pnl", 0) for t in trades if t.get("pnl", 0) > 0])
        total_loss = abs(sum([t.get("pnl", 0) for t in trades if t.get("pnl", 0) < 0]))
        profit_factor = total_profit / total_loss if total_loss > 0 else (total_profit if total_profit > 0 else 1.0)
        
        # Calculate average trade P&L
        avg_trade = sum([t.get("pnl", 0) for t in trades]) / len(trades) if trades else 0.0
        
        # Calculate max consecutive losses
        max_consecutive_losses = self._calculate_max_consecutive_losses(trades)
        
        metrics = {
            "final_value": final_value,
            "total_return": total_return,
            "max_drawdown": drawdown.get("max", {}).get("drawdown", 0) * 100,
            "sharpe_ratio": sharpe_ratio,
            "total_trades": len(trades),
            "trades": trades,
            "win_rate": win_rate,
            "profitable_trades": profitable_trades,
            "profit_factor": profit_factor,
            "avg_trade": avg_trade,
            "max_consecutive_losses": max_consecutive_losses
        }
        
        return metrics
    
    def _get_detailed_trades(self, strat) -> List[Dict[str, Any]]:
        """Extract detailed trade information from strategy."""
        trades = []
        
        # Get trades from strategy trade_history if available
        if hasattr(strat, 'trade_history') and strat.trade_history:
            logger.info(f"Found {len(strat.trade_history)} trades in strategy trade_history")
            for trade in strat.trade_history:
                # Simple conversion - only include fields that exist
                size = trade.get('size', 0)
                
                # Convert strategy trade format to API format
                trade_info = {
                    'entry_date': trade.get('entry_date'),
                    'exit_date': trade.get('exit_date'),
                    'entry_price': trade.get('entry_price'),
                    'exit_price': trade.get('exit_price'),
                    'size': size,
                    'pnl': trade.get('pnl', 0),
                    'pnl_comm': trade.get('pnlcomm', 0),
                    # Add minimal required fields with defaults
                    'side': 'long' if size > 0 else 'short',
                    'return_pct': 0,  # Will be calculated by frontend if needed
                    'exit_reason': 'Strategy End',  # Default reason
                    'stop_loss': None,
                    'take_profit': None,
                    'duration_hours': 0,
                    'pnl_slippage': 0,
                    'metadata': {}
                }
                
                # Validate required fields
                if trade_info['entry_date'] is None or trade_info['exit_date'] is None:
                    logger.warning(f"Trade missing dates: entry_date={trade_info['entry_date']}, exit_date={trade_info['exit_date']}")
                if trade_info['entry_price'] is None or trade_info['exit_price'] is None:
                    logger.warning(f"Trade missing prices: entry_price={trade_info['entry_price']}, exit_price={trade_info['exit_price']}")
                trades.append(trade_info)
        
        # Fallback: Get trades from broker if strategy trade_history is empty
        if not trades and hasattr(strat, 'broker') and strat.broker and hasattr(strat.broker, 'trades') and strat.broker.trades:
            logger.info(f"Falling back to broker trades: {len(strat.broker.trades)} found")
            for trade in strat.broker.trades:
                if hasattr(trade, 'status') and trade.status == trade.Status.Closed:
                    try:
                        trade_info = {
                            'entry_date': getattr(trade, 'dtopen', None),
                            'exit_date': getattr(trade, 'dtclose', None),
                            'entry_price': getattr(trade, 'price', 0),
                            'exit_price': getattr(trade, 'pclose', 0),
                            'size': getattr(trade, 'size', 0),
                            'side': 'long' if getattr(trade, 'size', 0) > 0 else 'short',
                            'pnl': getattr(trade, 'pnl', 0),
                            'pnl_comm': getattr(trade, 'pnlcomm', 0),
                            'pnl_slippage': 0,  # Would need to calculate from slippage
                            'return_pct': 0,  # Simplified calculation
                            'exit_reason': self._determine_exit_reason(trade),
                            'stop_loss': None,  # Would need to track from strategy
                            'take_profit': None,  # Would need to track from strategy
                            'duration_hours': 0,  # Simplified calculation
                            'metadata': {
                                'trade_id': getattr(trade, 'id', 'unknown'),
                                'commission': getattr(trade, 'commission', 0)
                            }
                        }
                        
                        # Validate trade data before adding
                        if (trade_info['entry_date'] is not None and 
                            trade_info['exit_date'] is not None and
                            trade_info['entry_price'] is not None and
                            trade_info['exit_price'] is not None):
                            trades.append(trade_info)
                        else:
                            logger.warning(f"Skipping trade with missing data: {trade_info}")
                            
                    except Exception as e:
                        logger.warning(f"Error processing broker trade: {e}")
                        continue
        
        logger.info(f"Extracted {len(trades)} trades for API response")
        
        # Debug logging for trade data
        if trades:
            logger.info(f"First trade sample: {trades[0]}")
            logger.info(f"Trade keys: {list(trades[0].keys()) if trades else 'No trades'}")
        else:
            logger.warning("No trades extracted - this will cause UI to show 'No trades executed'")
            
        return trades
    
    def _determine_exit_reason(self, trade) -> str:
        """Determine how the trade was closed."""
        # This is a simplified approach - in a real implementation,
        # you'd track the actual exit reason from the strategy
        if hasattr(trade, 'exit_reason'):
            return trade.exit_reason
        
        # Default to manual if no specific reason is tracked
        return "manual"
    

    
    def _calculate_max_consecutive_losses(self, trades: List[Dict[str, Any]]) -> int:
        """Calculate the maximum number of consecutive losing trades."""
        if not trades:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in trades:
            pnl = trade.get("pnl", 0)
            if pnl < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
        
        # Try to infer from price movement
        if trade.size > 0:  # Long position
            if trade.pnl > 0:
                return "Take Profit"  # Likely TP
            else:
                return "Stop Loss"    # Likely SL
        else:  # Short position
            if trade.pnl > 0:
                return "Take Profit"  # Likely TP
            else:
                return "Stop Loss"    # Likely SL
    
    def _calculate_win_rate(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate win rate from trades."""
        if not trades:
            return 0.0
        
        winning_trades = len([t for t in trades if t.get("pnl", 0) > 0])
        return (winning_trades / len(trades)) * 100
    
    async def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """Run a backtest with the given configuration."""
        start_time = datetime.utcnow()
        backtest_id = f"{config.symbol}_{config.strategy_name}_{'_'.join(config.get_primary_timeframes())}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"Starting backtest {backtest_id}")
            
            # Prepare data before running backtest
            logger.info("Preparing backtest data...")
            preparation_result = await self._prepare_data(config)
            logger.info("Data preparation completed successfully")
            
            # Set up Cerebro
            self.cerebro = self._setup_cerebro(config)
            
            # Run backtest and get results
            start_exec = datetime.utcnow()
            results = self.cerebro.run()
            execution_time = (datetime.utcnow() - start_exec).total_seconds()
            
            # Calculate metrics using the results
            metrics = self._calculate_metrics_from_results(results, config)
            
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
            
        except DataPreparationError as e:
            logger.error(f"Backtest {backtest_id} failed during data preparation: {str(e)}")
            result = BacktestResult(
                id=backtest_id,
                config=config,
                start_time=start_time,
                end_time=datetime.utcnow(),
                duration=0,
                status="failed",
                error_message=f"Data preparation failed: {str(e)}",
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
