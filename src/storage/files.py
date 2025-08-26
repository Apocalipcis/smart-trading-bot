"""File management helpers for the trading bot."""

import gzip
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import structlog

logger = structlog.get_logger(__name__)


class FileManager:
    """Manages file operations for the trading bot data hierarchy."""
    
    def __init__(self, data_dir: str = None):
        # Use environment variable or default based on context
        if data_dir is None:
            import os
            data_dir = os.getenv("DATA_DIR", "data")
        self.data_dir = Path(data_dir)
        self.candles_dir = self.data_dir / "candles"
        self.backtests_dir = self.data_dir / "backtests"
        self.reports_dir = self.data_dir / "reports"
        self.artifacts_dir = self.data_dir / "artifacts"
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.data_dir,
            self.candles_dir,
            self.backtests_dir,
            self.reports_dir,
            self.artifacts_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("Data directories ensured", data_dir=str(self.data_dir))
    
    # =============================================================================
    # Candle Data Management
    # =============================================================================
    
    def get_candle_path(self, exchange: str, symbol: str, timeframe: str, format: str = "parquet") -> Path:
        """Get the path for candle data file."""
        # Normalize symbol (remove special characters, uppercase)
        normalized_symbol = symbol.upper().replace("/", "").replace("-", "")
        
        # Create directory structure: data/candles/{exchange}/{symbol}/
        candle_dir = self.candles_dir / exchange.lower() / normalized_symbol
        candle_dir.mkdir(parents=True, exist_ok=True)
        
        # File path: {tf}.{format}
        filename = f"{timeframe.lower()}.{format}"
        return candle_dir / filename
    
    def save_candles(self, df: pd.DataFrame, exchange: str, symbol: str, timeframe: str, 
                    format: str = "parquet", compress: bool = True) -> Path:
        """Save candle data to file."""
        file_path = self.get_candle_path(exchange, symbol, timeframe, format)
        
        try:
            if format.lower() == "parquet":
                if compress:
                    df.to_parquet(file_path, compression="gzip")
                else:
                    df.to_parquet(file_path)
            elif format.lower() == "csv":
                df.to_csv(file_path, index=True)
            elif format.lower() == "json":
                df.to_json(file_path, orient="records", indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info("Candles saved", 
                       exchange=exchange, 
                       symbol=symbol, 
                       timeframe=timeframe, 
                       format=format,
                       rows=len(df),
                       file_path=str(file_path))
            
            return file_path
            
        except Exception as e:
            logger.error("Failed to save candles", 
                        exchange=exchange, 
                        symbol=symbol, 
                        timeframe=timeframe, 
                        error=str(e))
            raise
    
    def load_candles(self, exchange: str, symbol: str, timeframe: str, 
                    format: str = "parquet") -> Optional[pd.DataFrame]:
        """Load candle data from file."""
        file_path = self.get_candle_path(exchange, symbol, timeframe, format)
        
        if not file_path.exists():
            logger.warning("Candle file not found", file_path=str(file_path))
            return None
        
        try:
            if format.lower() == "parquet":
                df = pd.read_parquet(file_path)
            elif format.lower() == "csv":
                df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            elif format.lower() == "json":
                df = pd.read_json(file_path, orient="records")
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info("Candles loaded", 
                       exchange=exchange, 
                       symbol=symbol, 
                       timeframe=timeframe, 
                       rows=len(df),
                       file_path=str(file_path))
            
            return df
            
        except Exception as e:
            logger.error("Failed to load candles", 
                        exchange=exchange, 
                        symbol=symbol, 
                        timeframe=timeframe, 
                        error=str(e))
            return None
    
    def list_candle_files(self, exchange: str = None, symbol: str = None) -> List[Path]:
        """List all candle data files."""
        files = []
        
        if exchange and symbol:
            # Specific exchange and symbol
            normalized_symbol = symbol.upper().replace("/", "").replace("-", "")
            candle_dir = self.candles_dir / exchange.lower() / normalized_symbol
            if candle_dir.exists():
                files.extend(candle_dir.glob("*.*"))
        elif exchange:
            # All files for exchange
            exchange_dir = self.candles_dir / exchange.lower()
            if exchange_dir.exists():
                files.extend(exchange_dir.rglob("*.*"))
        else:
            # All files
            files.extend(self.candles_dir.rglob("*.*"))
        
        return sorted(files)
    
    # =============================================================================
    # Backtest Data Management
    # =============================================================================
    
    def get_backtest_path(self, backtest_id: str, date: datetime = None) -> Path:
        """Get the path for backtest result file."""
        if date is None:
            date = datetime.now()
        
        # Create date-based directory: data/backtests/{YYYY-MM-DD}/
        date_dir = self.backtests_dir / date.strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # File path: {backtest_id}.json
        return date_dir / f"{backtest_id}.json"
    
    def save_backtest_result(self, backtest_id: str, result: Dict[str, Any], 
                           date: datetime = None) -> Path:
        """Save backtest result to file."""
        file_path = self.get_backtest_path(backtest_id, date)
        
        try:
            with open(file_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            logger.info("Backtest result saved", 
                       backtest_id=backtest_id, 
                       file_path=str(file_path))
            
            return file_path
            
        except Exception as e:
            logger.error("Failed to save backtest result", 
                        backtest_id=backtest_id, 
                        error=str(e))
            raise
    
    def load_backtest_result(self, backtest_id: str, date: datetime = None) -> Optional[Dict[str, Any]]:
        """Load backtest result from file."""
        file_path = self.get_backtest_path(backtest_id, date)
        
        if not file_path.exists():
            logger.warning("Backtest file not found", file_path=str(file_path))
            return None
        
        try:
            with open(file_path, 'r') as f:
                result = json.load(f)
            
            logger.info("Backtest result loaded", 
                       backtest_id=backtest_id, 
                       file_path=str(file_path))
            
            return result
            
        except Exception as e:
            logger.error("Failed to load backtest result", 
                        backtest_id=backtest_id, 
                        error=str(e))
            return None
    
    def list_backtest_files(self, date: datetime = None) -> List[Path]:
        """List all backtest result files."""
        if date:
            date_dir = self.backtests_dir / date.strftime("%Y-%m-%d")
            if date_dir.exists():
                return sorted(date_dir.glob("*.json"))
            return []
        else:
            return sorted(self.backtests_dir.rglob("*.json"))
    
    # =============================================================================
    # Report Management
    # =============================================================================
    
    def get_report_path(self, report_id: str) -> Path:
        """Get the path for report directory."""
        return self.reports_dir / report_id
    
    def save_report(self, report_id: str, data: Union[str, bytes, pd.DataFrame], 
                   filename: str, format: str = None) -> Path:
        """Save report data to file."""
        report_dir = self.get_report_path(report_id)
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine format from filename if not provided
        if format is None:
            format = Path(filename).suffix.lstrip(".")
        
        file_path = report_dir / filename
        
        try:
            if isinstance(data, pd.DataFrame):
                if format.lower() == "parquet":
                    data.to_parquet(file_path)
                elif format.lower() == "csv":
                    data.to_csv(file_path, index=True)
                elif format.lower() == "json":
                    data.to_json(file_path, orient="records", indent=2)
                else:
                    raise ValueError(f"Unsupported format for DataFrame: {format}")
            elif isinstance(data, str):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(data)
            elif isinstance(data, bytes):
                with open(file_path, 'wb') as f:
                    f.write(data)
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")
            
            logger.info("Report saved", 
                       report_id=report_id, 
                       filename=filename, 
                       file_path=str(file_path))
            
            return file_path
            
        except Exception as e:
            logger.error("Failed to save report", 
                        report_id=report_id, 
                        filename=filename, 
                        error=str(e))
            raise
    
    def list_report_files(self, report_id: str) -> List[Path]:
        """List all files in a report directory."""
        report_dir = self.get_report_path(report_id)
        if report_dir.exists():
            return sorted(report_dir.glob("*"))
        return []
    
    # =============================================================================
    # Artifact Management
    # =============================================================================
    
    def get_artifact_path(self, backtest_id: str, artifact_type: str, 
                         filename: str = None) -> Path:
        """Get the path for artifact file."""
        artifact_dir = self.artifacts_dir / backtest_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        if filename:
            return artifact_dir / filename
        else:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return artifact_dir / f"{artifact_type}_{timestamp}"
    
    def save_artifact(self, backtest_id: str, artifact_type: str, 
                     data: Union[str, bytes, pd.DataFrame], 
                     filename: str = None, format: str = None) -> Path:
        """Save artifact data to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{artifact_type}_{timestamp}"
        
        file_path = self.get_artifact_path(backtest_id, artifact_type, filename)
        
        try:
            if isinstance(data, pd.DataFrame):
                if format is None:
                    format = "parquet"
                
                if format.lower() == "parquet":
                    data.to_parquet(file_path)
                elif format.lower() == "csv":
                    data.to_csv(file_path, index=True)
                elif format.lower() == "json":
                    data.to_json(file_path, orient="records", indent=2)
                else:
                    raise ValueError(f"Unsupported format for DataFrame: {format}")
            elif isinstance(data, str):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(data)
            elif isinstance(data, bytes):
                with open(file_path, 'wb') as f:
                    f.write(data)
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")
            
            logger.info("Artifact saved", 
                       backtest_id=backtest_id, 
                       artifact_type=artifact_type, 
                       filename=filename,
                       file_path=str(file_path))
            
            return file_path
            
        except Exception as e:
            logger.error("Failed to save artifact", 
                        backtest_id=backtest_id, 
                        artifact_type=artifact_type, 
                        error=str(e))
            raise
    
    def list_artifact_files(self, backtest_id: str = None) -> List[Path]:
        """List all artifact files."""
        if backtest_id:
            artifact_dir = self.artifacts_dir / backtest_id
            if artifact_dir.exists():
                return sorted(artifact_dir.glob("*"))
            return []
        else:
            return sorted(self.artifacts_dir.rglob("*"))
    
    # =============================================================================
    # Data Retention and Cleanup
    # =============================================================================
    
    def cleanup_old_data(self, retention_days: int = 365) -> Dict[str, int]:
        """Clean up old data files based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_counts = {
            "candles": 0,
            "backtests": 0,
            "reports": 0,
            "artifacts": 0
        }
        
        try:
            # Clean up old backtest files
            for backtest_file in self.list_backtest_files():
                try:
                    file_date = datetime.fromtimestamp(backtest_file.stat().st_mtime)
                    if file_date < cutoff_date:
                        backtest_file.unlink()
                        deleted_counts["backtests"] += 1
                except Exception as e:
                    logger.warning("Failed to delete old backtest file", 
                                 file_path=str(backtest_file), 
                                 error=str(e))
            
            # Clean up old report directories
            for report_dir in self.reports_dir.iterdir():
                if report_dir.is_dir():
                    try:
                        dir_date = datetime.fromtimestamp(report_dir.stat().st_mtime)
                        if dir_date < cutoff_date:
                            shutil.rmtree(report_dir)
                            deleted_counts["reports"] += 1
                    except Exception as e:
                        logger.warning("Failed to delete old report directory", 
                                     dir_path=str(report_dir), 
                                     error=str(e))
            
            # Clean up old artifact directories
            for artifact_dir in self.artifacts_dir.iterdir():
                if artifact_dir.is_dir():
                    try:
                        dir_date = datetime.fromtimestamp(artifact_dir.stat().st_mtime)
                        if dir_date < cutoff_date:
                            shutil.rmtree(artifact_dir)
                            deleted_counts["artifacts"] += 1
                    except Exception as e:
                        logger.warning("Failed to delete old artifact directory", 
                                     dir_path=str(artifact_dir), 
                                     error=str(e))
            
            logger.info("Data cleanup completed", 
                       retention_days=retention_days, 
                       deleted_counts=deleted_counts)
            
            return deleted_counts
            
        except Exception as e:
            logger.error("Failed to cleanup old data", error=str(e))
            raise
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        stats = {
            "total_size_bytes": 0,
            "file_counts": {
                "candles": 0,
                "backtests": 0,
                "reports": 0,
                "artifacts": 0
            },
            "directory_sizes": {}
        }
        
        try:
            # Calculate sizes and counts for each directory
            for dir_name, dir_path in [
                ("candles", self.candles_dir),
                ("backtests", self.backtests_dir),
                ("reports", self.reports_dir),
                ("artifacts", self.artifacts_dir)
            ]:
                if dir_path.exists():
                    dir_size = 0
                    file_count = 0
                    
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file():
                            dir_size += file_path.stat().st_size
                            file_count += 1
                    
                    stats["file_counts"][dir_name] = file_count
                    stats["directory_sizes"][dir_name] = dir_size
                    stats["total_size_bytes"] += dir_size
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get storage stats", error=str(e))
            return stats


# Global file manager instance
_file_manager: Optional[FileManager] = None


def get_file_manager(data_dir: str = None) -> FileManager:
    # Use environment variable or default based on context
    if data_dir is None:
        import os
        data_dir = os.getenv("DATA_DIR", "data")
    """Get the global file manager instance."""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager(data_dir)
    return _file_manager
