"""Backtest API endpoint."""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.storage.parquet_storage import ParquetStorage
from app.storage.cache_manager import cache
from app.models.backtest import BacktestResult, TradeResult
import uuid

router = APIRouter()
storage = ParquetStorage()


@router.get("/")
async def run_backtest(
    symbol: str = Query(..., description="Trading pair symbol"),
    tf: str = Query(..., description="Timeframe"),
    from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    sl_percent: float = Query(2.0, description="Stop loss percentage"),
    tp_percent: float = Query(4.0, description="Take profit percentage")
) -> dict:
    """Run backtest for a trading strategy."""
    try:
        # Parse dates
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        # Validate date range
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        if (end_date - start_date).days > 365:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
        
        # Check cache first
        cache_key = f"backtest:{symbol}:{tf}:{from_date}:{to_date}:{sl_percent}:{tp_percent}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Load candles for backtest period
        candles = storage.load_candles(
            symbol=symbol,
            timeframe=tf,
            start_date=start_date,
            end_date=end_date
        )
        
        if len(candles) < 10:
            raise HTTPException(status_code=400, detail="Insufficient data for backtest")
        
        # Run backtest simulation
        backtest_result = _run_backtest_simulation(
            candles=candles,
            symbol=symbol,
            timeframe=tf,
            start_date=start_date,
            end_date=end_date,
            sl_percent=sl_percent,
            tp_percent=tp_percent
        )
        
        # Save backtest result
        storage.save_backtest_result(backtest_result)
        
        # Export to CSV
        csv_url = storage.export_to_csv(backtest_result, symbol, tf)
        
        result = {
            "backtest_id": backtest_result.id,
            "symbol": symbol,
            "timeframe": tf,
            "period": f"{from_date} to {to_date}",
            "metrics": {
                "total_trades": backtest_result.total_trades,
                "win_rate": backtest_result.win_rate,
                "profit_factor": backtest_result.profit_factor,
                "average_r": backtest_result.average_r,
                "expectancy": backtest_result.expectancy,
                "max_drawdown_r": backtest_result.max_drawdown_r,
                "sharpe_like": backtest_result.sharpe_like,
                "time_in_market": backtest_result.time_in_market
            },
            "csv_url": csv_url,
            "parameters": {
                "sl_percent": sl_percent,
                "tp_percent": tp_percent
            }
        }
        
        # Cache the result
        cache.set(cache_key, result, ttl=3600)  # Cache for 1 hour
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")


def _run_backtest_simulation(
    candles: list,
    symbol: str,
    timeframe: str,
    start_date: datetime,
    end_date: datetime,
    sl_percent: float,
    tp_percent: float
) -> BacktestResult:
    """Run backtest simulation on historical data."""
    
    # Simple breakout strategy simulation
    trades = []
    position = None
    entry_price = 0
    stop_loss = 0
    take_profit = 0
    entry_timestamp = None
    
    for i, candle in enumerate(candles):
        if position is None:
            # Look for entry signal (simple breakout)
            if i > 0:
                prev_candle = candles[i-1]
                
                # Long entry: break above previous high
                if candle.close > prev_candle.high and candle.volume > prev_candle.volume * 1.2:
                    position = "LONG"
                    entry_price = candle.close
                    stop_loss = entry_price * (1 - sl_percent / 100)
                    take_profit = entry_price * (1 + tp_percent / 100)
                    entry_timestamp = candle.timestamp
                
                # Short entry: break below previous low
                elif candle.close < prev_candle.low and candle.volume > prev_candle.volume * 1.2:
                    position = "SHORT"
                    entry_price = candle.close
                    stop_loss = entry_price * (1 + sl_percent / 100)
                    take_profit = entry_price * (1 - tp_percent / 100)
                    entry_timestamp = candle.timestamp
        
        else:
            # Check exit conditions
            exit_reason = None
            exit_price = 0
            exit_timestamp = candle.timestamp
            
            if position == "LONG":
                # Check stop loss
                if candle.low <= stop_loss:
                    exit_reason = "SL"
                    exit_price = stop_loss
                # Check take profit
                elif candle.high >= take_profit:
                    exit_reason = "TP"
                    exit_price = take_profit
                # Check time-based exit (end of period)
                elif i == len(candles) - 1:
                    exit_reason = "TIME"
                    exit_price = candle.close
            
            elif position == "SHORT":
                # Check stop loss
                if candle.high >= stop_loss:
                    exit_reason = "SL"
                    exit_price = stop_loss
                # Check take profit
                elif candle.low <= take_profit:
                    exit_reason = "TP"
                    exit_price = take_profit
                # Check time-based exit (end of period)
                elif i == len(candles) - 1:
                    exit_reason = "TIME"
                    exit_price = candle.close
            
            if exit_reason:
                # Calculate trade metrics
                if position == "LONG":
                    r_multiple = (exit_price - entry_price) / (entry_price - stop_loss)
                else:
                    r_multiple = (entry_price - exit_price) / (stop_loss - entry_price)
                
                # Calculate MAE and MFE
                mae, mfe = _calculate_mae_mfe(candles, entry_timestamp, exit_timestamp, position, entry_price)
                
                # Create trade result
                trade = TradeResult(
                    id=str(uuid.uuid4()),
                    symbol=symbol,
                    timeframe=timeframe,
                    signal_kind="BREAKOUT",
                    signal_timestamp=entry_timestamp,
                    direction=position,
                    entry_timestamp=entry_timestamp,
                    entry_price=entry_price,
                    stop_loss_price=stop_loss,
                    take_profit_price=take_profit,
                    exit_reason=exit_reason,
                    exit_timestamp=exit_timestamp,
                    exit_price=exit_price,
                    r_multiple=r_multiple,
                    mae=mae,
                    mfe=mfe
                )
                
                trades.append(trade)
                
                # Reset position
                position = None
                entry_price = 0
                stop_loss = 0
                take_profit = 0
                entry_timestamp = None
    
    # Calculate performance metrics
    metrics = _calculate_performance_metrics(trades)
    
    # Create backtest result
    backtest_result = BacktestResult(
        id=str(uuid.uuid4()),
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        trades=trades,
        **metrics
    )
    
    return backtest_result


def _calculate_mae_mfe(candles: list, entry_time: datetime, exit_time: datetime, position: str, entry_price: float) -> tuple:
    """Calculate Maximum Adverse Excursion and Maximum Favorable Excursion."""
    mae = 0
    mfe = 0
    
    for candle in candles:
        if entry_time <= candle.timestamp <= exit_time:
            if position == "LONG":
                # Calculate drawdown from entry
                drawdown = (entry_price - candle.low) / entry_price
                mae = max(mae, drawdown)
                
                # Calculate profit from entry
                profit = (candle.high - entry_price) / entry_price
                mfe = max(mfe, profit)
            
            elif position == "SHORT":
                # Calculate drawdown from entry
                drawdown = (candle.high - entry_price) / entry_price
                mae = max(mae, drawdown)
                
                # Calculate profit from entry
                profit = (entry_price - candle.low) / entry_price
                mfe = max(mfe, profit)
    
    return mae, mfe


def _calculate_performance_metrics(trades: list) -> dict:
    """Calculate performance metrics from trades."""
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "average_r": 0.0,
            "expectancy": 0.0,
            "max_drawdown_r": 0.0,
            "sharpe_like": 0.0,
            "time_in_market": 0.0
        }
    
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t.r_multiple > 0])
    losing_trades = len([t for t in trades if t.r_multiple < 0])
    
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    
    # Calculate profit factor
    gross_profit = sum([t.r_multiple for t in trades if t.r_multiple > 0])
    gross_loss = abs(sum([t.r_multiple for t in trades if t.r_multiple < 0]))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Calculate average R
    average_r = sum([t.r_multiple for t in trades]) / total_trades
    
    # Calculate expectancy
    expectancy = average_r
    
    # Calculate max drawdown
    max_drawdown_r = min([t.r_multiple for t in trades]) if trades else 0
    
    # Calculate Sharpe-like ratio (simplified)
    returns = [t.r_multiple for t in trades]
    sharpe_like = (sum(returns) / len(returns)) / (sum([(r - average_r) ** 2 for r in returns]) ** 0.5) if len(returns) > 1 else 0
    
    # Calculate time in market (simplified)
    time_in_market = 50.0  # Placeholder - would need more complex calculation
    
    return {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "average_r": average_r,
        "expectancy": expectancy,
        "max_drawdown_r": max_drawdown_r,
        "sharpe_like": sharpe_like,
        "time_in_market": time_in_market
    }
