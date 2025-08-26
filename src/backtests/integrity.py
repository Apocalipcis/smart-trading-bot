"""Data integrity checker for candle data."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DataIssue(BaseModel):
    """Represents a data integrity issue."""
    
    issue_type: str  # "gap", "duplicate", "invalid_price", "invalid_volume", "timestamp_error"
    severity: str  # "low", "medium", "high", "critical"
    description: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    affected_rows: List[int] = []
    details: Dict[str, Any] = {}


class DataQualityReport(BaseModel):
    """Report of data quality and integrity issues."""
    
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    total_candles: int
    expected_candles: int
    missing_candles: int
    duplicate_candles: int
    invalid_candles: int
    data_completeness: float  # percentage
    issues: List[DataIssue] = []
    summary: str = ""


class DataIntegrityChecker:
    """Checks candle data for integrity issues."""
    
    def __init__(self):
        self.timeframe_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440
        }
    
    def check_data_integrity(self, 
                            df: pd.DataFrame,
                            symbol: str,
                            timeframe: str,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> DataQualityReport:
        """Check data integrity for a DataFrame of candle data."""
        try:
            if df.empty:
                return self._create_empty_report(symbol, timeframe, start_date, end_date)
            
            # Ensure required columns exist
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Convert timestamp to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Sort by timestamp
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Set date range
            if start_date is None:
                start_date = df['timestamp'].min()
            if end_date is None:
                end_date = df['timestamp'].max()
            
            # Filter data to date range
            df_filtered = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)].copy()
            
            # Check for various issues
            issues = []
            
            # Check for gaps
            gap_issues = self._check_for_gaps(df_filtered, timeframe, start_date, end_date)
            issues.extend(gap_issues)
            
            # Check for duplicates
            duplicate_issues = self._check_for_duplicates(df_filtered)
            issues.extend(duplicate_issues)
            
            # Check for invalid data
            invalid_issues = self._check_for_invalid_data(df_filtered)
            issues.extend(invalid_issues)
            
            # Check for timestamp errors
            timestamp_issues = self._check_timestamp_errors(df_filtered, timeframe)
            issues.extend(timestamp_issues)
            
            # Calculate statistics
            total_candles = len(df_filtered)
            expected_candles = self._calculate_expected_candles(start_date, end_date, timeframe)
            missing_candles = expected_candles - total_candles
            duplicate_candles = len([i for i in issues if i.issue_type == "duplicate"])
            invalid_candles = len([i for i in issues if i.issue_type == "invalid_price" or i.issue_type == "invalid_volume"])
            
            data_completeness = (total_candles / expected_candles) * 100 if expected_candles > 0 else 0
            
            # Create summary
            summary = self._create_summary(issues, data_completeness, missing_candles)
            
            return DataQualityReport(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                total_candles=total_candles,
                expected_candles=expected_candles,
                missing_candles=missing_candles,
                duplicate_candles=duplicate_candles,
                invalid_candles=invalid_candles,
                data_completeness=data_completeness,
                issues=issues,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Failed to check data integrity: {str(e)}")
            raise
    
    def _check_for_gaps(self, df: pd.DataFrame, timeframe: str, 
                        start_date: datetime, end_date: datetime) -> List[DataIssue]:
        """Check for gaps in the data."""
        issues = []
        
        if df.empty:
            return issues
        
        # Get expected timestamps
        expected_timestamps = self._generate_expected_timestamps(start_date, end_date, timeframe)
        
        # Find missing timestamps
        actual_timestamps = set(df['timestamp'])
        missing_timestamps = [ts for ts in expected_timestamps if ts not in actual_timestamps]
        
        if missing_timestamps:
            # Group consecutive missing timestamps
            gaps = self._group_consecutive_timestamps(missing_timestamps)
            
            for gap_start, gap_end in gaps:
                gap_duration = (gap_end - gap_start).total_seconds() / 60  # minutes
                
                if gap_duration <= self.timeframe_minutes.get(timeframe, 1):
                    severity = "low"
                elif gap_duration <= self.timeframe_minutes.get(timeframe, 1) * 10:
                    severity = "medium"
                elif gap_duration <= self.timeframe_minutes.get(timeframe, 1) * 100:
                    severity = "high"
                else:
                    severity = "critical"
                
                issue = DataIssue(
                    issue_type="gap",
                    severity=severity,
                    description=f"Data gap from {gap_start} to {gap_end} ({gap_duration:.1f} minutes)",
                    start_time=gap_start,
                    end_time=gap_end,
                    details={"gap_duration_minutes": gap_duration}
                )
                issues.append(issue)
        
        return issues
    
    def _check_for_duplicates(self, df: pd.DataFrame) -> List[DataIssue]:
        """Check for duplicate timestamps."""
        issues = []
        
        if df.empty:
            return issues
        
        # Find duplicate timestamps
        duplicates = df[df.duplicated(subset=['timestamp'], keep=False)]
        
        if not duplicates.empty:
            # Group by timestamp
            duplicate_groups = duplicates.groupby('timestamp')
            
            for timestamp, group in duplicate_groups:
                if len(group) > 1:
                    issue = DataIssue(
                        issue_type="duplicate",
                        severity="medium",
                        description=f"Duplicate data for timestamp {timestamp} ({len(group)} records)",
                        start_time=timestamp,
                        end_time=timestamp,
                        affected_rows=group.index.tolist(),
                        details={"duplicate_count": len(group)}
                    )
                    issues.append(issue)
        
        return issues
    
    def _check_for_invalid_data(self, df: pd.DataFrame) -> List[DataIssue]:
        """Check for invalid OHLCV data."""
        issues = []
        
        if df.empty:
            return issues
        
        # Check for invalid prices
        invalid_prices = df[
            (df['open'] <= 0) | (df['high'] <= 0) | (df['low'] <= 0) | (df['close'] <= 0) |
            (df['high'] < df['low']) |
            (df['open'] > df['high']) | (df['open'] < df['low']) |
            (df['close'] > df['high']) | (df['close'] < df['low'])
        ]
        
        if not invalid_prices.empty:
            issue = DataIssue(
                issue_type="invalid_price",
                severity="high",
                description=f"Found {len(invalid_prices)} candles with invalid OHLC data",
                affected_rows=invalid_prices.index.tolist(),
                details={
                    "invalid_count": len(invalid_prices),
                    "examples": invalid_prices[['timestamp', 'open', 'high', 'low', 'close']].head(5).to_dict('records')
                }
            )
            issues.append(issue)
        
        # Check for invalid volumes
        invalid_volumes = df[df['volume'] < 0]
        
        if not invalid_volumes.empty:
            issue = DataIssue(
                issue_type="invalid_volume",
                severity="medium",
                description=f"Found {len(invalid_volumes)} candles with negative volume",
                affected_rows=invalid_volumes.index.tolist(),
                details={
                    "invalid_count": len(invalid_volumes),
                    "examples": invalid_volumes[['timestamp', 'volume']].head(5).to_dict('records')
                }
            )
            issues.append(issue)
        
        # Check for extreme price movements (potential data errors)
        if len(df) > 1:
            # Calculate price changes
            df_copy = df.copy()
            df_copy['price_change'] = df_copy['close'].pct_change().abs()
            
            # Flag extreme changes (e.g., > 50% in one period)
            extreme_changes = df_copy[df_copy['price_change'] > 0.5]
            
            if not extreme_changes.empty:
                issue = DataIssue(
                    issue_type="extreme_price_change",
                    severity="medium",
                    description=f"Found {len(extreme_changes)} candles with extreme price changes (>50%)",
                    affected_rows=extreme_changes.index.tolist(),
                    details={
                        "extreme_count": len(extreme_changes),
                        "examples": extreme_changes[['timestamp', 'close', 'price_change']].head(5).to_dict('records')
                    }
                )
                issues.append(issue)
        
        return issues
    
    def _check_timestamp_errors(self, df: pd.DataFrame, timeframe: str) -> List[DataIssue]:
        """Check for timestamp alignment errors."""
        issues = []
        
        if df.empty:
            return issues
        
        # Check if timestamps align with expected intervals
        expected_interval = self.timeframe_minutes.get(timeframe, 1)
        
        for i in range(1, len(df)):
            current_ts = df.iloc[i]['timestamp']
            previous_ts = df.iloc[i-1]['timestamp']
            
            # Calculate time difference in minutes
            time_diff = (current_ts - previous_ts).total_seconds() / 60
            
            # Check if the difference is not a multiple of the expected interval
            if time_diff % expected_interval != 0:
                issue = DataIssue(
                    issue_type="timestamp_error",
                    severity="low",
                    description=f"Timestamp misalignment: {previous_ts} to {current_ts} ({time_diff:.1f} minutes, expected {expected_interval})",
                    start_time=previous_ts,
                    end_time=current_ts,
                    affected_rows=[i-1, i],
                    details={
                        "time_diff_minutes": time_diff,
                        "expected_interval": expected_interval
                    }
                )
                issues.append(issue)
        
        return issues
    
    def _generate_expected_timestamps(self, start_date: datetime, end_date: datetime, timeframe: str) -> List[datetime]:
        """Generate expected timestamps for the given date range and timeframe."""
        timestamps = []
        current = start_date
        
        interval_minutes = self.timeframe_minutes.get(timeframe, 1)
        
        while current <= end_date:
            timestamps.append(current)
            current += timedelta(minutes=interval_minutes)
        
        return timestamps
    
    def _group_consecutive_timestamps(self, timestamps: List[datetime]) -> List[Tuple[datetime, datetime]]:
        """Group consecutive timestamps into gaps."""
        if not timestamps:
            return []
        
        gaps = []
        timestamps.sort()
        
        gap_start = timestamps[0]
        gap_end = timestamps[0]
        
        for i in range(1, len(timestamps)):
            current = timestamps[i]
            expected = gap_end + timedelta(minutes=1)
            
            if current == expected:
                gap_end = current
            else:
                gaps.append((gap_start, gap_end))
                gap_start = current
                gap_end = current
        
        # Add the last gap
        gaps.append((gap_start, gap_end))
        
        return gaps
    
    def _calculate_expected_candles(self, start_date: datetime, end_date: datetime, timeframe: str) -> int:
        """Calculate expected number of candles for the given date range."""
        total_minutes = (end_date - start_date).total_seconds() / 60
        interval_minutes = self.timeframe_minutes.get(timeframe, 1)
        
        # Add 1 because we include both start and end dates
        return int(total_minutes / interval_minutes) + 1
    
    def _create_summary(self, issues: List[DataIssue], data_completeness: float, missing_candles: int) -> str:
        """Create a summary of the data quality report."""
        if not issues:
            return f"Data quality is excellent. Completeness: {data_completeness:.1f}%"
        
        critical_issues = len([i for i in issues if i.severity == "critical"])
        high_issues = len([i for i in issues if i.severity == "high"])
        medium_issues = len([i for i in issues if i.severity == "medium"])
        low_issues = len([i for i in issues if i.severity == "low"])
        
        summary_parts = [f"Data completeness: {data_completeness:.1f}%"]
        
        if missing_candles > 0:
            summary_parts.append(f"Missing candles: {missing_candles}")
        
        if critical_issues > 0:
            summary_parts.append(f"Critical issues: {critical_issues}")
        if high_issues > 0:
            summary_parts.append(f"High priority issues: {high_issues}")
        if medium_issues > 0:
            summary_parts.append(f"Medium priority issues: {medium_issues}")
        if low_issues > 0:
            summary_parts.append(f"Low priority issues: {low_issues}")
        
        return ". ".join(summary_parts) + "."
    
    def _create_empty_report(self, symbol: str, timeframe: str, 
                            start_date: Optional[datetime], end_date: Optional[datetime]) -> DataQualityReport:
        """Create a report for empty data."""
        now = datetime.now(timezone.utc)
        start = start_date or now
        end = end_date or now
        
        return DataQualityReport(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start,
            end_date=end,
            total_candles=0,
            expected_candles=0,
            missing_candles=0,
            duplicate_candles=0,
            invalid_candles=0,
            data_completeness=0.0,
            issues=[],
            summary="No data available for the specified date range."
        )
    
    def fix_common_issues(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Fix common data integrity issues."""
        if df.empty:
            return df
        
        df_fixed = df.copy()
        
        # Remove duplicates
        df_fixed = df_fixed.drop_duplicates(subset=['timestamp']).reset_index(drop=True)
        
        # Sort by timestamp
        df_fixed = df_fixed.sort_values('timestamp').reset_index(drop=True)
        
        # Fix invalid prices (set to previous valid price or remove)
        for col in ['open', 'high', 'low', 'close']:
            invalid_mask = df_fixed[col] <= 0
            if invalid_mask.any():
                # Forward fill invalid values
                df_fixed[col] = df_fixed[col].replace(0, pd.NA).fillna(method='ffill')
                
                # If still have invalid values, backward fill
                df_fixed[col] = df_fixed[col].fillna(method='bfill')
                
                # Remove rows that still have invalid values
                df_fixed = df_fixed[df_fixed[col].notna()].reset_index(drop=True)
        
        # Fix invalid volumes
        df_fixed.loc[df_fixed['volume'] < 0, 'volume'] = 0
        
        # Ensure OHLC relationships
        df_fixed['high'] = df_fixed[['open', 'high', 'close']].max(axis=1)
        df_fixed['low'] = df_fixed[['open', 'low', 'close']].min(axis=1)
        
        return df_fixed
