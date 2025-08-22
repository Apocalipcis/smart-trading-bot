"""Mock backtest engine for view-only mode."""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import uuid

logger = logging.getLogger(__name__)


class MockBacktestEngine:
    """Mock backtest engine for generating sample results in view-only mode."""
    
    def __init__(self):
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        self.timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        
    def run_backtest(self, symbol: str, timeframe: str, start_date: str, end_date: str, 
                    sl_percent: float = 2.0, tp_percent: float = 4.0) -> Dict[str, Any]:
        """Run mock backtest and return sample results."""
        logger.info(f"Running mock backtest for {symbol} on {timeframe} timeframe")
        
        # Generate mock trades
        trades = self._generate_mock_trades(symbol, timeframe, start_date, end_date, sl_percent, tp_percent)
        
        # Calculate mock performance metrics
        metrics = self._calculate_mock_metrics(trades)
        
        # Create backtest result
        result = {
            'id': str(uuid.uuid4()),
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': start_date,
            'end_date': end_date,
            'trades': trades,
            'total_trades': len(trades),
            'win_rate': metrics['win_rate'],
            'profit_factor': metrics['profit_factor'],
            'total_return': metrics['total_return'],
            'max_drawdown': metrics['max_drawdown'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'avg_r_multiple': metrics['avg_r_multiple'],
            'expectancy': metrics['expectancy'],
            'created_at': datetime.utcnow().isoformat()
        }
        
        return result
        
    def _generate_mock_trades(self, symbol: str, timeframe: str, start_date: str, 
                             end_date: str, sl_percent: float, tp_percent: float) -> List[Dict[str, Any]]:
        """Generate mock trade data."""
        trades = []
        
        # Generate 8-15 mock trades
        num_trades = random.randint(8, 15)
        
        for i in range(num_trades):
            # Generate random trade
            direction = random.choice(['LONG', 'SHORT'])
            is_winner = random.random() < 0.65  # 65% win rate
            
            # Generate mock prices
            base_price = 50000 if symbol == 'BTCUSDT' else 3000 if symbol == 'ETHUSDT' else 300
            entry_price = base_price * random.uniform(0.9, 1.1)
            
            if direction == 'LONG':
                if is_winner:
                    exit_price = entry_price * (1 + random.uniform(0.02, 0.08))  # 2-8% profit
                else:
                    exit_price = entry_price * (1 - random.uniform(0.01, 0.04))  # 1-4% loss
            else:  # SHORT
                if is_winner:
                    exit_price = entry_price * (1 - random.uniform(0.02, 0.08))  # 2-8% profit
                else:
                    exit_price = entry_price * (1 + random.uniform(0.01, 0.04))  # 1-4% loss
            
            # Calculate stop loss and take profit
            if direction == 'LONG':
                stop_loss = entry_price * (1 - sl_percent / 100)
                take_profit = entry_price * (1 + tp_percent / 100)
            else:
                stop_loss = entry_price * (1 + sl_percent / 100)
                take_profit = entry_price * (1 - tp_percent / 100)
            
            # Generate timestamps
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            entry_time = start_dt + timedelta(
                days=random.randint(0, (end_dt - start_dt).days),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Trade duration: 1 hour to 7 days
            duration_hours = random.randint(1, 168)
            exit_time = entry_time + timedelta(hours=duration_hours)
            
            # Calculate R-multiple
            if direction == 'LONG':
                r_multiple = (exit_price - entry_price) / (entry_price - stop_loss) if entry_price != stop_loss else 0
            else:
                r_multiple = (entry_price - exit_price) / (stop_loss - entry_price) if stop_loss != entry_price else 0
            
            trade = {
                'id': str(uuid.uuid4()),
                'symbol': symbol,
                'timeframe': timeframe,
                'direction': direction,
                'entry_price': round(entry_price, 2),
                'exit_price': round(exit_price, 2),
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'entry_time': entry_time.isoformat(),
                'exit_time': exit_time.isoformat(),
                'r_multiple': round(r_multiple, 2),
                'pnl': round(exit_price - entry_price if direction == 'LONG' else entry_price - exit_price, 2),
                'pnl_percent': round(((exit_price - entry_price) / entry_price * 100) if direction == 'LONG' else ((entry_price - exit_price) / entry_price * 100), 2),
                'is_winner': is_winner,
                'exit_reason': 'TP' if is_winner else 'SL'
            }
            
            trades.append(trade)
            
        return trades
        
    def _calculate_mock_metrics(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate mock performance metrics from trades."""
        if not trades:
            return {
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_return': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'avg_r_multiple': 0.0,
                'expectancy': 0.0
            }
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['is_winner']]
        losing_trades = [t for t in trades if not t['is_winner']]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Profit metrics
        total_profit = sum(t['pnl'] for t in winning_trades)
        total_loss = abs(sum(t['pnl'] for t in losing_trades))
        
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Return metrics
        total_return = sum(t['pnl'] for t in trades)
        
        # R-multiple metrics
        r_multiples = [t['r_multiple'] for t in trades]
        avg_r_multiple = sum(r_multiples) / len(r_multiples) if r_multiples else 0
        
        # Expectancy
        expectancy = (win_rate * avg_r_multiple) - ((1 - win_rate) * 1.0)
        
        return {
            'win_rate': round(win_rate, 3),
            'profit_factor': round(profit_factor, 2),
            'total_return': round(total_return, 2),
            'max_drawdown': round(random.uniform(0.05, 0.15), 3),  # Mock drawdown
            'sharpe_ratio': round(random.uniform(0.8, 2.5), 2),   # Mock Sharpe ratio
            'avg_r_multiple': round(avg_r_multiple, 2),
            'expectancy': round(expectancy, 2)
        }
