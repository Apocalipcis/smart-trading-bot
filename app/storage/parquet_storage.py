"""Parquet storage layer for efficient data persistence."""

import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from app.config import settings
from app.models.candle import Candle
from app.models.signal import Signal
from app.models.backtest import BacktestResult


class ParquetStorage:
    """Parquet-based storage for candles, signals, and backtest results."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize storage with data directory."""
        self.data_dir = Path(data_dir or settings.data_dir)
        self.reports_dir = Path(settings.reports_dir)
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.data_dir / 'candles').mkdir(exist_ok=True)
        (self.data_dir / 'signals').mkdir(exist_ok=True)
        (self.data_dir / 'backtests').mkdir(exist_ok=True)
    
    def _get_candle_path(self, symbol: str, timeframe: str) -> Path:
        """Get path for candle data file."""
        return self.data_dir / 'candles' / f'{symbol}_{timeframe}.parquet'
    
    def _get_signal_path(self, symbol: str, timeframe: str) -> Path:
        """Get path for signal data file."""
        return self.data_dir / 'signals' / f'{symbol}_{timeframe}.parquet'
    
    def _get_backtest_path(self, backtest_id: str) -> Path:
        """Get path for backtest result file."""
        return self.data_dir / 'backtests' / f'{backtest_id}.parquet'
    
    def _get_csv_path(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> Path:
        """Get path for CSV report file."""
        return self.reports_dir / symbol / timeframe / f'{start_date}_{end_date}.csv'
    
    def save_candles(self, candles: List[Candle]) -> bool:
        """Save candles to Parquet file."""
        if not candles:
            return True
        
        # Group by symbol and timeframe
        grouped = {}
        for candle in candles:
            key = (candle.symbol, candle.timeframe)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(candle)
        
        # Save each group
        for (symbol, timeframe), candle_list in grouped.items():
            file_path = self._get_candle_path(symbol, timeframe)
            
            # Convert to DataFrame
            df = pd.DataFrame([candle.dict() for candle in candle_list])
            
            # Convert timestamp columns
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            # Save to Parquet
            df.to_parquet(file_path, index=False, compression='snappy')
        
        return True
    
    def load_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Candle]:
        """Load candles from Parquet file with optional filtering."""
        file_path = self._get_candle_path(symbol, timeframe)
        
        if not file_path.exists():
            return []
        
        try:
            # Read Parquet file
            df = pd.read_parquet(file_path)
            
            # Apply filters
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]
            
            # Apply limit
            if limit:
                df = df.tail(limit)
            
            # Convert to Candle objects
            candles = []
            for _, row in df.iterrows():
                candle_data = row.to_dict()
                # Convert pandas timestamps back to datetime
                for key in ['timestamp', 'created_at']:
                    if key in candle_data and pd.notna(candle_data[key]):
                        candle_data[key] = candle_data[key].to_pydatetime()
                candles.append(Candle(**candle_data))
            
            return candles
            
        except Exception as e:
            print(f"Error loading candles: {e}")
            return []
    
    def save_signals(self, signals: List[Signal]) -> bool:
        """Save signals to Parquet file."""
        if not signals:
            return True
        
        # Group by symbol and timeframe
        grouped = {}
        for signal in signals:
            key = (signal.symbol, signal.timeframe)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(signal)
        
        # Save each group
        for (symbol, timeframe), signal_list in grouped.items():
            file_path = self._get_signal_path(symbol, timeframe)
            
            # Convert to DataFrame
            df = pd.DataFrame([signal.dict() for signal in signal_list])
            
            # Convert timestamp columns
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            # Save to Parquet
            df.to_parquet(file_path, index=False, compression='snappy')
        
        return True
    
    def load_signals(
        self, 
        symbol: str, 
        timeframe: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        signal_kind: Optional[str] = None
    ) -> List[Signal]:
        """Load signals from Parquet file with optional filtering."""
        file_path = self._get_signal_path(symbol, timeframe)
        
        if not file_path.exists():
            return []
        
        try:
            # Read Parquet file
            df = pd.read_parquet(file_path)
            
            # Apply filters
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]
            if signal_kind:
                df = df[df['kind'] == signal_kind]
            
            # Convert to Signal objects
            signals = []
            for _, row in df.iterrows():
                signal_data = row.to_dict()
                # Convert pandas timestamps back to datetime
                for key in ['timestamp', 'created_at']:
                    if key in signal_data and pd.notna(signal_data[key]):
                        signal_data[key] = signal_data[key].to_pydatetime()
                signals.append(Signal(**signal_data))
            
            return signals
            
        except Exception as e:
            print(f"Error loading signals: {e}")
            return []
    
    def save_backtest_result(self, result: BacktestResult) -> bool:
        """Save backtest result to Parquet file."""
        try:
            file_path = self._get_backtest_path(result.id)
            
            # Convert to DataFrame
            df = pd.DataFrame([result.dict()])
            
            # Convert timestamp columns
            df['start_date'] = pd.to_datetime(df['start_date'])
            df['end_date'] = pd.to_datetime(df['end_date'])
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Save to Parquet
            df.to_parquet(file_path, index=False, compression='snappy')
            
            return True
            
        except Exception as e:
            print(f"Error saving backtest result: {e}")
            return False
    
    def export_to_csv(
        self, 
        backtest_result: BacktestResult,
        symbol: str,
        timeframe: str
    ) -> Optional[str]:
        """Export backtest result to CSV file."""
        try:
            # Create directory structure
            csv_dir = self.reports_dir / symbol / timeframe
            csv_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            start_str = backtest_result.start_date.strftime('%Y%m%d')
            end_str = backtest_result.end_date.strftime('%Y%m%d')
            csv_filename = f'{start_str}_{end_str}.csv'
            csv_path = csv_dir / csv_filename
            
            # Convert trades to DataFrame
            trades_data = []
            for trade in backtest_result.trades:
                trade_dict = trade.dict()
                # Convert timestamps to strings for CSV
                for key in ['signal_timestamp', 'entry_timestamp', 'exit_timestamp']:
                    if key in trade_dict and trade_dict[key]:
                        trade_dict[key] = trade_dict[key].strftime('%Y-%m-%d %H:%M:%S')
                trades_data.append(trade_dict)
            
            df = pd.DataFrame(trades_data)
            
            # Save to CSV
            df.to_csv(csv_path, index=False)
            
            # Return relative path for API
            return f'/reports/{symbol}/{timeframe}/{csv_filename}'
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return None
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols from stored data."""
        symbols = set()
        candles_dir = self.data_dir / 'candles'
        
        if candles_dir.exists():
            for file_path in candles_dir.glob('*.parquet'):
                # Extract symbol from filename (e.g., 'BTCUSDT_1m.parquet' -> 'BTCUSDT')
                symbol = file_path.stem.split('_')[0]
                symbols.add(symbol)
        
        return sorted(list(symbols))
    
    def get_available_timeframes(self, symbol: str) -> List[str]:
        """Get list of available timeframes for a symbol."""
        timeframes = []
        candles_dir = self.data_dir / 'candles'
        
        if candles_dir.exists():
            for file_path in candles_dir.glob(f'{symbol}_*.parquet'):
                # Extract timeframe from filename (e.g., 'BTCUSDT_1m.parquet' -> '1m')
                timeframe = file_path.stem.split('_')[1]
                timeframes.append(timeframe)
        
        return sorted(timeframes)
