"""Comprehensive backtest metrics calculation."""

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TradeMetrics(BaseModel):
    """Metrics for individual trades."""
    
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    size: float
    side: str  # "long" or "short"
    pnl: float
    pnl_comm: float
    pnl_slippage: float
    pnl_funding: float
    duration_hours: float
    return_pct: float
    max_favorable_excursion: float
    max_adverse_excursion: float
    entry_slippage: float
    exit_slippage: float


class RiskMetrics(BaseModel):
    """Risk management metrics."""
    
    max_drawdown: float
    max_drawdown_pct: float
    max_drawdown_duration: int  # days
    var_95: float  # Value at Risk 95%
    var_99: float  # Value at Risk 99%
    expected_shortfall: float
    downside_deviation: float
    calmar_ratio: float
    sortino_ratio: float
    ulcer_index: float


class PerformanceMetrics(BaseModel):
    """Performance metrics."""
    
    total_return: float
    total_return_pct: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    profit_factor: float
    win_rate: float
    loss_rate: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_trade: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    consecutive_wins: int
    consecutive_losses: int
    max_consecutive_wins: int
    max_consecutive_losses: int
    avg_trade_duration: float
    best_month: float
    worst_month: float
    profitable_months: int
    total_months: int


class BacktestMetrics:
    """Calculates comprehensive backtest metrics."""
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
    
    def calculate_all_metrics(self, 
                            trades: List[Dict[str, Any]],
                            initial_capital: float,
                            final_capital: float,
                            start_date: datetime,
                            end_date: datetime,
                            commission_rate: float = 0.001,
                            slippage_rate: float = 0.0001,
                            funding_rate: float = 0.0001) -> Dict[str, Any]:
        """Calculate all backtest metrics."""
        try:
            # Convert trades to TradeMetrics objects
            trade_metrics = self._process_trades(trades, commission_rate, slippage_rate, funding_rate)
            
            # Calculate performance metrics
            performance = self._calculate_performance_metrics(
                trade_metrics, initial_capital, final_capital, start_date, end_date
            )
            
            # Calculate risk metrics
            risk = self._calculate_risk_metrics(trade_metrics, initial_capital)
            
            # Calculate additional metrics
            additional = self._calculate_additional_metrics(trade_metrics, initial_capital)
            
            return {
                "performance": performance.model_dump(),
                "risk": risk.model_dump(),
                "additional": additional,
                "trade_metrics": [t.model_dump() for t in trade_metrics]
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {str(e)}")
            raise
    
    def _process_trades(self, trades: List[Dict[str, Any]], 
                       commission_rate: float, slippage_rate: float, 
                       funding_rate: float) -> List[TradeMetrics]:
        """Process raw trades into TradeMetrics objects."""
        trade_metrics = []
        
        for trade in trades:
            try:
                # Calculate basic metrics
                entry_price = trade.get("entry_price", 0)
                exit_price = trade.get("exit_price", 0)
                size = trade.get("size", 0)
                side = "long" if size > 0 else "short"
                
                # Calculate P&L components
                pnl = trade.get("pnl", 0)
                pnl_comm = abs(size * entry_price * commission_rate) + abs(size * exit_price * commission_rate)
                pnl_slippage = abs(size * entry_price * slippage_rate) + abs(size * exit_price * slippage_rate)
                
                # Calculate funding costs (for futures)
                entry_date = trade.get("entry_date")
                exit_date = trade.get("exit_date")
                if entry_date and exit_date:
                    duration_hours = (exit_date - entry_date).total_seconds() / 3600
                    # Funding occurs every 8 hours
                    funding_periods = math.ceil(duration_hours / 8)
                    pnl_funding = abs(size * entry_price * funding_rate * funding_periods)
                else:
                    duration_hours = 0
                    pnl_funding = 0
                
                # Calculate return percentage
                return_pct = (pnl / (abs(size) * entry_price)) * 100 if size != 0 and entry_price != 0 else 0
                
                # Calculate MFE/MAE (simplified - would need tick data for accurate calculation)
                max_favorable_excursion = 0
                max_adverse_excursion = 0
                
                # Calculate slippage (simplified)
                entry_slippage = entry_price * slippage_rate
                exit_slippage = exit_price * slippage_rate
                
                trade_metric = TradeMetrics(
                    entry_date=entry_date or datetime.utcnow(),
                    exit_date=exit_date or datetime.utcnow(),
                    entry_price=entry_price,
                    exit_price=exit_price,
                    size=size,
                    side=side,
                    pnl=pnl,
                    pnl_comm=pnl_comm,
                    pnl_slippage=pnl_slippage,
                    pnl_funding=pnl_funding,
                    duration_hours=duration_hours,
                    return_pct=return_pct,
                    max_favorable_excursion=max_favorable_excursion,
                    max_adverse_excursion=max_adverse_excursion,
                    entry_slippage=entry_slippage,
                    exit_slippage=exit_slippage
                )
                
                trade_metrics.append(trade_metric)
                
            except Exception as e:
                logger.warning(f"Failed to process trade: {str(e)}")
                continue
        
        return trade_metrics
    
    def _calculate_performance_metrics(self, trade_metrics: List[TradeMetrics],
                                     initial_capital: float, final_capital: float,
                                     start_date: datetime, end_date: datetime) -> PerformanceMetrics:
        """Calculate performance metrics."""
        if not trade_metrics:
            return PerformanceMetrics(
                total_return=0, total_return_pct=0, annualized_return=0,
                sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0,
                profit_factor=0, win_rate=0, loss_rate=0,
                avg_win=0, avg_loss=0, largest_win=0, largest_loss=0,
                avg_trade=0, total_trades=0, winning_trades=0, losing_trades=0,
                consecutive_wins=0, consecutive_losses=0, max_consecutive_wins=0,
                max_consecutive_losses=0, avg_trade_duration=0,
                best_month=0, worst_month=0, profitable_months=0, total_months=0
            )
        
        # Basic returns
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100 if initial_capital > 0 else 0
        
        # Annualized return
        days = (end_date - start_date).days
        annualized_return = ((final_capital / initial_capital) ** (365 / days) - 1) * 100 if days > 0 else 0
        
        # Trade analysis
        winning_trades = [t for t in trade_metrics if t.pnl > 0]
        losing_trades = [t for t in trade_metrics if t.pnl < 0]
        
        total_trades = len(trade_metrics)
        winning_trades_count = len(winning_trades)
        losing_trades_count = len(losing_trades)
        
        win_rate = (winning_trades_count / total_trades) * 100 if total_trades > 0 else 0
        loss_rate = (losing_trades_count / total_trades) * 100 if total_trades > 0 else 0
        
        # P&L analysis
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        largest_win = max([t.pnl for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t.pnl for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum([t.pnl for t in winning_trades]) if winning_trades else 0
        gross_loss = abs(sum([t.pnl for t in losing_trades])) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average trade
        avg_trade = np.mean([t.pnl for t in trade_metrics]) if trade_metrics else 0
        
        # Consecutive wins/losses
        consecutive_wins, consecutive_losses, max_consecutive_wins, max_consecutive_losses = \
            self._calculate_consecutive_streaks(trade_metrics)
        
        # Average trade duration
        avg_trade_duration = np.mean([t.duration_hours for t in trade_metrics]) if trade_metrics else 0
        
        # Monthly analysis (simplified)
        best_month, worst_month, profitable_months, total_months = \
            self._calculate_monthly_metrics(trade_metrics, start_date, end_date)
        
        # Risk-adjusted returns
        returns = [t.pnl for t in trade_metrics]
        sharpe_ratio = self._calculate_sharpe_ratio(returns, initial_capital)
        sortino_ratio = self._calculate_sortino_ratio(returns, initial_capital)
        calmar_ratio = self._calculate_calmar_ratio(total_return_pct, 0)  # Will be updated with drawdown
        
        return PerformanceMetrics(
            total_return=total_return,
            total_return_pct=total_return_pct,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            profit_factor=profit_factor,
            win_rate=win_rate,
            loss_rate=loss_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            avg_trade=avg_trade,
            total_trades=total_trades,
            winning_trades=winning_trades_count,
            losing_trades=losing_trades_count,
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            avg_trade_duration=avg_trade_duration,
            best_month=best_month,
            worst_month=worst_month,
            profitable_months=profitable_months,
            total_months=total_months
        )
    
    def _calculate_risk_metrics(self, trade_metrics: List[TradeMetrics], 
                               initial_capital: float) -> RiskMetrics:
        """Calculate risk metrics."""
        if not trade_metrics:
            return RiskMetrics(
                max_drawdown=0, max_drawdown_pct=0, max_drawdown_duration=0,
                var_95=0, var_99=0, expected_shortfall=0, downside_deviation=0,
                calmar_ratio=0, sortino_ratio=0, ulcer_index=0
            )
        
        # Calculate equity curve
        equity_curve = self._calculate_equity_curve(trade_metrics, initial_capital)
        
        # Maximum drawdown
        max_drawdown, max_drawdown_pct, max_drawdown_duration = \
            self._calculate_max_drawdown(equity_curve)
        
        # Value at Risk
        returns = [t.pnl for t in trade_metrics]
        var_95 = np.percentile(returns, 5) if returns else 0
        var_99 = np.percentile(returns, 1) if returns else 0
        
        # Expected shortfall (Conditional VaR)
        expected_shortfall = np.mean([r for r in returns if r <= var_95]) if returns else 0
        
        # Downside deviation
        downside_returns = [r for r in returns if r < 0]
        downside_deviation = np.std(downside_returns) if downside_returns else 0
        
        # Risk-adjusted ratios
        calmar_ratio = 0  # Will be updated with performance metrics
        sortino_ratio = 0  # Will be updated with performance metrics
        
        # Ulcer Index
        ulcer_index = self._calculate_ulcer_index(equity_curve)
        
        return RiskMetrics(
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            max_drawdown_duration=max_drawdown_duration,
            var_95=var_95,
            var_99=var_99,
            expected_shortfall=expected_shortfall,
            downside_deviation=downside_deviation,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            ulcer_index=ulcer_index
        )
    
    def _calculate_additional_metrics(self, trade_metrics: List[TradeMetrics], 
                                    initial_capital: float) -> Dict[str, Any]:
        """Calculate additional metrics."""
        if not trade_metrics:
            return {}
        
        # Commission analysis
        total_commission = sum([t.pnl_comm for t in trade_metrics])
        total_slippage = sum([t.pnl_slippage for t in trade_metrics])
        total_funding = sum([t.pnl_funding for t in trade_metrics])
        
        # Slippage analysis
        avg_entry_slippage = np.mean([t.entry_slippage for t in trade_metrics])
        avg_exit_slippage = np.mean([t.exit_slippage for t in trade_metrics])
        
        # Duration analysis
        durations = [t.duration_hours for t in trade_metrics]
        avg_duration = np.mean(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # Side analysis
        long_trades = [t for t in trade_metrics if t.side == "long"]
        short_trades = [t for t in trade_metrics if t.side == "short"]
        
        long_pnl = sum([t.pnl for t in long_trades])
        short_pnl = sum([t.pnl for t in short_trades])
        
        return {
            "total_commission": total_commission,
            "total_slippage": total_slippage,
            "total_funding": total_funding,
            "avg_entry_slippage": avg_entry_slippage,
            "avg_exit_slippage": avg_exit_slippage,
            "avg_duration": avg_duration,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "long_trades_count": len(long_trades),
            "short_trades_count": len(short_trades),
            "long_pnl": long_pnl,
            "short_pnl": short_pnl,
            "long_win_rate": (len([t for t in long_trades if t.pnl > 0]) / len(long_trades) * 100) if long_trades else 0,
            "short_win_rate": (len([t for t in short_trades if t.pnl > 0]) / len(short_trades) * 100) if short_trades else 0
        }
    
    def _calculate_consecutive_streaks(self, trade_metrics: List[TradeMetrics]) -> Tuple[int, int, int, int]:
        """Calculate consecutive win/loss streaks."""
        if not trade_metrics:
            return 0, 0, 0, 0
        
        current_wins = 0
        current_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for trade in trade_metrics:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
        
        return current_wins, current_losses, max_consecutive_wins, max_consecutive_losses
    
    def _calculate_equity_curve(self, trade_metrics: List[TradeMetrics], 
                               initial_capital: float) -> List[float]:
        """Calculate equity curve over time."""
        if not trade_metrics:
            return [initial_capital]
        
        # Sort trades by entry date
        sorted_trades = sorted(trade_metrics, key=lambda x: x.entry_date)
        
        equity_curve = [initial_capital]
        current_equity = initial_capital
        
        for trade in sorted_trades:
            current_equity += trade.pnl
            equity_curve.append(current_equity)
        
        return equity_curve
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> Tuple[float, float, int]:
        """Calculate maximum drawdown and duration."""
        if len(equity_curve) < 2:
            return 0, 0, 0
        
        peak = equity_curve[0]
        max_drawdown = 0
        max_drawdown_pct = 0
        drawdown_start = 0
        max_drawdown_duration = 0
        
        for i, equity in enumerate(equity_curve):
            if equity > peak:
                peak = equity
                drawdown_start = i
            else:
                drawdown = peak - equity
                drawdown_pct = (drawdown / peak) * 100 if peak > 0 else 0
                
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_pct = drawdown_pct
                    max_drawdown_duration = i - drawdown_start
        
        return max_drawdown, max_drawdown_pct, max_drawdown_duration
    
    def _calculate_monthly_metrics(self, trade_metrics: List[TradeMetrics], 
                                 start_date: datetime, end_date: datetime) -> Tuple[float, float, int, int]:
        """Calculate monthly performance metrics."""
        if not trade_metrics:
            return 0, 0, 0, 0
        
        # Group trades by month
        monthly_pnl = {}
        for trade in trade_metrics:
            month_key = trade.entry_date.strftime("%Y-%m")
            if month_key not in monthly_pnl:
                monthly_pnl[month_key] = 0
            monthly_pnl[month_key] += trade.pnl
        
        if not monthly_pnl:
            return 0, 0, 0, 0
        
        monthly_returns = list(monthly_pnl.values())
        best_month = max(monthly_returns)
        worst_month = min(monthly_returns)
        profitable_months = len([r for r in monthly_returns if r > 0])
        total_months = len(monthly_returns)
        
        return best_month, worst_month, profitable_months, total_months
    
    def _calculate_sharpe_ratio(self, returns: List[float], initial_capital: float) -> float:
        """Calculate Sharpe ratio."""
        if not returns:
            return 0
        
        # Convert to percentage returns
        pct_returns = [(r / initial_capital) * 100 for r in returns]
        
        if len(pct_returns) < 2:
            return 0
        
        avg_return = np.mean(pct_returns)
        std_return = np.std(pct_returns)
        
        if std_return == 0:
            return 0
        
        # Annualized Sharpe ratio (assuming daily data)
        sharpe = (avg_return - self.risk_free_rate) / std_return
        return sharpe * math.sqrt(252)  # Annualize
    
    def _calculate_sortino_ratio(self, returns: List[float], initial_capital: float) -> float:
        """Calculate Sortino ratio."""
        if not returns:
            return 0
        
        # Convert to percentage returns
        pct_returns = [(r / initial_capital) * 100 for r in returns]
        
        if len(pct_returns) < 2:
            return 0
        
        avg_return = np.mean(pct_returns)
        downside_returns = [r for r in pct_returns if r < 0]
        
        if not downside_returns:
            return float('inf')
        
        downside_deviation = np.std(downside_returns)
        
        if downside_deviation == 0:
            return 0
        
        # Annualized Sortino ratio
        sortino = (avg_return - self.risk_free_rate) / downside_deviation
        return sortino * math.sqrt(252)  # Annualize
    
    def _calculate_calmar_ratio(self, total_return_pct: float, max_drawdown_pct: float) -> float:
        """Calculate Calmar ratio."""
        if max_drawdown_pct == 0:
            return 0
        
        return total_return_pct / abs(max_drawdown_pct)
    
    def _calculate_ulcer_index(self, equity_curve: List[float]) -> float:
        """Calculate Ulcer Index."""
        if len(equity_curve) < 2:
            return 0
        
        # Calculate drawdowns
        peak = equity_curve[0]
        drawdowns = []
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown_pct = (peak - equity) / peak if peak > 0 else 0
            drawdowns.append(drawdown_pct)
        
        # Calculate Ulcer Index
        squared_drawdowns = [d * d for d in drawdowns]
        avg_squared_drawdown = np.mean(squared_drawdowns)
        
        return math.sqrt(avg_squared_drawdown) * 100
