"""Storage management for backtest results and artifacts."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel

from .models import BacktestResult, BacktestConfig

logger = logging.getLogger(__name__)


class BacktestArtifact(BaseModel):
    """Represents a backtest artifact (chart, report, etc.)."""
    
    id: str
    backtest_id: str
    type: str  # chart, report, trade_log, etc.
    file_path: str
    created_at: datetime
    metadata: Dict[str, Any] = {}


class BacktestStorage:
    """Manages storage of backtest results and artifacts."""
    
    def __init__(self, data_dir: str = "/data"):
        self.data_dir = Path(data_dir)
        self.backtests_dir = self.data_dir / "backtests"
        self.artifacts_dir = self.data_dir / "artifacts"
        self.reports_dir = self.data_dir / "reports"
        
        # Create directories if they don't exist
        self.backtests_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def save_backtest_result(self, result: BacktestResult) -> str:
        """Save backtest result to storage."""
        try:
            # Create date-based directory structure
            date_dir = self.backtests_dir / result.start_time.strftime("%Y-%m-%d")
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename
            filename = f"{result.id}.json"
            file_path = date_dir / filename
            
            # Convert result to dict and handle datetime serialization
            result_dict = result.dict()
            result_dict["start_time"] = result.start_time.isoformat()
            result_dict["end_time"] = result.end_time.isoformat()
            result_dict["config"]["start_date"] = result.config.start_date.isoformat()
            result_dict["config"]["end_date"] = result.config.end_date.isoformat()
            
            # Save to JSON
            with open(file_path, 'w') as f:
                json.dump(result_dict, f, indent=2, default=str)
            
            logger.info(f"Saved backtest result to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save backtest result: {str(e)}")
            raise
    
    def load_backtest_result(self, backtest_id: str) -> Optional[BacktestResult]:
        """Load backtest result by ID."""
        try:
            # Search for the backtest file
            for date_dir in self.backtests_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                    
                for file_path in date_dir.glob("*.json"):
                    if backtest_id in file_path.name:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Convert datetime strings back to datetime objects
                        data["start_time"] = datetime.fromisoformat(data["start_time"])
                        data["end_time"] = datetime.fromisoformat(data["end_time"])
                        data["config"]["start_date"] = datetime.fromisoformat(data["config"]["start_date"])
                        data["config"]["end_date"] = datetime.fromisoformat(data["config"]["end_date"])
                        
                        return BacktestResult(**data)
            
            logger.warning(f"Backtest result not found: {backtest_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load backtest result {backtest_id}: {str(e)}")
            return None
    
    def list_backtest_results(self, 
                            symbol: Optional[str] = None,
                            strategy: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> List[BacktestResult]:
        """List all backtest results with optional filtering."""
        results = []
        
        try:
            for date_dir in self.backtests_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                
                # Check if date is within range
                if start_date or end_date:
                    try:
                        dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                        if start_date and dir_date < start_date:
                            continue
                        if end_date and dir_date > end_date:
                            continue
                    except ValueError:
                        continue
                
                for file_path in date_dir.glob("*.json"):
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Apply filters
                        if symbol and data["config"]["symbol"] != symbol:
                            continue
                        if strategy and data["config"]["strategy_name"] != strategy:
                            continue
                        
                        # Convert datetime strings back to datetime objects
                        data["start_time"] = datetime.fromisoformat(data["start_time"])
                        data["end_time"] = datetime.fromisoformat(data["end_time"])
                        data["config"]["start_date"] = datetime.fromisoformat(data["config"]["start_date"])
                        data["config"]["end_date"] = datetime.fromisoformat(data["config"]["end_date"])
                        
                        results.append(BacktestResult(**data))
                        
                    except Exception as e:
                        logger.warning(f"Failed to load {file_path}: {str(e)}")
                        continue
            
            # Sort by start time (newest first)
            results.sort(key=lambda x: x.start_time, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list backtest results: {str(e)}")
        
        return results
    
    def delete_backtest_result(self, backtest_id: str) -> bool:
        """Delete a backtest result and its artifacts."""
        try:
            # Find and delete the result file
            result_deleted = False
            for date_dir in self.backtests_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                    
                for file_path in date_dir.glob("*.json"):
                    if backtest_id in file_path.name:
                        file_path.unlink()
                        result_deleted = True
                        logger.info(f"Deleted backtest result: {file_path}")
                        break
                
                if result_deleted:
                    break
            
            # Delete associated artifacts
            artifacts_deleted = self._delete_artifacts(backtest_id)
            
            # Delete associated reports
            reports_deleted = self._delete_reports(backtest_id)
            
            if result_deleted:
                logger.info(f"Successfully deleted backtest {backtest_id}")
                return True
            else:
                logger.warning(f"Backtest result not found: {backtest_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete backtest result {backtest_id}: {str(e)}")
            return False
    
    def delete_all_backtest_results(self) -> int:
        """Delete all backtest results and artifacts."""
        try:
            count = 0
            
            # Delete all result files
            for date_dir in self.backtests_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                    
                for file_path in date_dir.glob("*.json"):
                    file_path.unlink()
                    count += 1
            
            # Delete all artifacts
            for artifact_file in self.artifacts_dir.rglob("*"):
                if artifact_file.is_file():
                    artifact_file.unlink()
            
            # Delete all reports
            for report_file in self.reports_dir.rglob("*"):
                if report_file.is_file():
                    report_file.unlink()
            
            logger.info(f"Deleted {count} backtest results and all artifacts")
            return count
            
        except Exception as e:
            logger.error(f"Failed to delete all backtest results: {str(e)}")
            return 0
    
    def save_artifact(self, backtest_id: str, artifact_type: str, 
                      data: Union[str, bytes, pd.DataFrame], 
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save a backtest artifact."""
        try:
            # Create artifact directory
            artifact_dir = self.artifacts_dir / backtest_id
            artifact_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{artifact_type}_{timestamp}"
            
            if isinstance(data, pd.DataFrame):
                file_path = artifact_dir / f"{filename}.parquet"
                data.to_parquet(file_path)
            elif isinstance(data, str):
                file_path = artifact_dir / f"{filename}.txt"
                with open(file_path, 'w') as f:
                    f.write(data)
            elif isinstance(data, bytes):
                file_path = artifact_dir / f"{filename}.bin"
                with open(file_path, 'wb') as f:
                    f.write(data)
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")
            
            # Create artifact record
            artifact = BacktestArtifact(
                id=f"{backtest_id}_{artifact_type}_{timestamp}",
                backtest_id=backtest_id,
                type=artifact_type,
                file_path=str(file_path),
                created_at=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Save artifact metadata
            metadata_file = artifact_dir / f"{artifact_type}_{timestamp}_meta.json"
            with open(metadata_file, 'w') as f:
                json.dump(artifact.dict(), f, indent=2, default=str)
            
            logger.info(f"Saved artifact {artifact.id} to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save artifact: {str(e)}")
            raise
    
    def load_artifact(self, artifact_id: str) -> Optional[BacktestArtifact]:
        """Load artifact metadata by ID."""
        try:
            # Search for artifact metadata files
            for metadata_file in self.artifacts_dir.rglob("*_meta.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        data = json.load(f)
                    
                    if data["id"] == artifact_id:
                        data["created_at"] = datetime.fromisoformat(data["created_at"])
                        return BacktestArtifact(**data)
                        
                except Exception as e:
                    logger.warning(f"Failed to load metadata {metadata_file}: {str(e)}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load artifact {artifact_id}: {str(e)}")
            return None
    
    def _delete_artifacts(self, backtest_id: str) -> bool:
        """Delete artifacts for a specific backtest."""
        try:
            artifact_dir = self.artifacts_dir / backtest_id
            if artifact_dir.exists():
                import shutil
                shutil.rmtree(artifact_dir)
                logger.info(f"Deleted artifacts for backtest {backtest_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete artifacts for {backtest_id}: {str(e)}")
            return False
    
    def _delete_reports(self, backtest_id: str) -> bool:
        """Delete reports for a specific backtest."""
        try:
            report_dir = self.reports_dir / backtest_id
            if report_dir.exists():
                import shutil
                shutil.rmtree(report_dir)
                logger.info(f"Deleted reports for backtest {backtest_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete reports for {backtest_id}: {str(e)}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            stats = {
                "total_backtests": 0,
                "total_artifacts": 0,
                "total_reports": 0,
                "storage_size_mb": 0,
                "oldest_backtest": None,
                "newest_backtest": None,
            }
            
            # Count backtests
            for date_dir in self.backtests_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                stats["total_backtests"] += len(list(date_dir.glob("*.json")))
            
            # Count artifacts
            stats["total_artifacts"] = len(list(self.artifacts_dir.rglob("*")))
            
            # Count reports
            stats["total_reports"] = len(list(self.reports_dir.rglob("*")))
            
            # Calculate storage size
            total_size = 0
            for path in [self.backtests_dir, self.artifacts_dir, self.reports_dir]:
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            
            stats["storage_size_mb"] = round(total_size / (1024 * 1024), 2)
            
            # Get date range
            backtest_results = self.list_backtest_results()
            if backtest_results:
                stats["oldest_backtest"] = min(r.start_time for r in backtest_results)
                stats["newest_backtest"] = max(r.start_time for r in backtest_results)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {}
