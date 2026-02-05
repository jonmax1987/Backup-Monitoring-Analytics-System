"""Processing engine for computing aggregates and metrics."""

from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
import calendar

from backup_monitoring.config.config_loader import get_config
from backup_monitoring.data_loader.models import BackupRecord, BackupStatus
from backup_monitoring.processing.models import (
    AggregatedMetrics,
    DailyMetrics,
    WeeklyMetrics,
    MonthlyMetrics,
    PeriodType,
)


class ProcessingError(Exception):
    """Exception raised when processing fails."""
    pass


class ProcessingEngine:
    """Processes backup records to compute aggregates and metrics."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the processing engine.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = get_config(config_path)
        self.aggregation_periods = self.config.processing.aggregation_periods
        self.duration_unit = self.config.processing.duration_unit
    
    def compute_daily_aggregates(
        self,
        records: List[BackupRecord],
        target_date: Optional[date] = None
    ) -> List[DailyMetrics]:
        """
        Compute daily aggregates for backup records.
        
        Args:
            records: List of BackupRecord objects
            target_date: Optional specific date to aggregate. If None, aggregates all dates.
            
        Returns:
            List of DailyMetrics objects, one per day and backup type combination
        """
        if not records:
            return []
        
        # Group records by date and backup type
        daily_data: Dict[tuple[date, str], List[BackupRecord]] = defaultdict(list)
        
        for record in records:
            record_date = record.start_time.date()
            
            # Filter by target_date if specified
            if target_date is not None and record_date != target_date:
                continue
            
            backup_type = record.backup_type or "unknown"
            daily_data[(record_date, backup_type)].append(record)
        
        # Compute metrics for each day/type combination
        daily_metrics = []
        
        for (record_date, backup_type), day_records in daily_data.items():
            metrics = self._compute_metrics_for_records(
                day_records,
                record_date,
                record_date,
                PeriodType.DAY,
                backup_type
            )
            
            daily_metric = DailyMetrics(
                **metrics.model_dump(),
                period_date=record_date
            )
            daily_metrics.append(daily_metric)
        
        return sorted(daily_metrics, key=lambda x: (x.period_date, x.backup_type))
    
    def compute_weekly_aggregates(
        self,
        records: List[BackupRecord],
        week_start: Optional[date] = None
    ) -> List[WeeklyMetrics]:
        """
        Compute weekly aggregates for backup records.
        
        Args:
            records: List of BackupRecord objects
            week_start: Optional specific week start date (Monday). If None, aggregates all weeks.
            
        Returns:
            List of WeeklyMetrics objects, one per week and backup type combination
        """
        if not records:
            return []
        
        # Group records by week and backup type
        weekly_data: Dict[tuple[date, str], List[BackupRecord]] = defaultdict(list)
        
        for record in records:
            record_date = record.start_time.date()
            week_start_date = self._get_week_start(record_date)
            
            # Filter by week_start if specified
            if week_start is not None and week_start_date != week_start:
                continue
            
            backup_type = record.backup_type or "unknown"
            weekly_data[(week_start_date, backup_type)].append(record)
        
        # Compute metrics for each week/type combination
        weekly_metrics = []
        
        for (week_start_date, backup_type), week_records in weekly_data.items():
            week_end_date = week_start_date + timedelta(days=6)
            
            metrics = self._compute_metrics_for_records(
                week_records,
                week_start_date,
                week_end_date,
                PeriodType.WEEK,
                backup_type
            )
            
            # Calculate week number
            week_number = week_start_date.isocalendar()[1]
            
            weekly_metric = WeeklyMetrics(
                **metrics.model_dump(),
                week_start=week_start_date,
                week_end=week_end_date,
                week_number=week_number
            )
            weekly_metrics.append(weekly_metric)
        
        return sorted(weekly_metrics, key=lambda x: (x.week_start, x.backup_type))
    
    def compute_monthly_aggregates(
        self,
        records: List[BackupRecord],
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> List[MonthlyMetrics]:
        """
        Compute monthly aggregates for backup records.
        
        Args:
            records: List of BackupRecord objects
            year: Optional specific year. If None, aggregates all years.
            month: Optional specific month (1-12). If None, aggregates all months.
            
        Returns:
            List of MonthlyMetrics objects, one per month and backup type combination
        """
        if not records:
            return []
        
        # Group records by month and backup type
        monthly_data: Dict[tuple[int, int, str], List[BackupRecord]] = defaultdict(list)
        
        for record in records:
            record_date = record.start_time.date()
            record_year = record_date.year
            record_month = record_date.month
            
            # Filter by year/month if specified
            if year is not None and record_year != year:
                continue
            if month is not None and record_month != month:
                continue
            
            backup_type = record.backup_type or "unknown"
            monthly_data[(record_year, record_month, backup_type)].append(record)
        
        # Compute metrics for each month/type combination
        monthly_metrics = []
        
        for (record_year, record_month, backup_type), month_records in monthly_data.items():
            month_start = date(record_year, record_month, 1)
            # Get last day of month
            last_day = calendar.monthrange(record_year, record_month)[1]
            month_end = date(record_year, record_month, last_day)
            
            metrics = self._compute_metrics_for_records(
                month_records,
                month_start,
                month_end,
                PeriodType.MONTH,
                backup_type
            )
            
            monthly_metric = MonthlyMetrics(
                **metrics.model_dump(),
                year=record_year,
                month=record_month
            )
            monthly_metrics.append(monthly_metric)
        
        return sorted(monthly_metrics, key=lambda x: (x.year, x.month, x.backup_type))
    
    def _compute_metrics_for_records(
        self,
        records: List[BackupRecord],
        period_start: date,
        period_end: date,
        period_type: PeriodType,
        backup_type: str
    ) -> AggregatedMetrics:
        """
        Compute aggregated metrics for a list of records.
        
        Args:
            records: List of BackupRecord objects
            period_start: Start date of the period
            period_end: End date of the period
            period_type: Type of period
            backup_type: Type of backup
            
        Returns:
            AggregatedMetrics object
        """
        if not records:
            # Return zero metrics
            return AggregatedMetrics(
                period_start=period_start,
                period_end=period_end,
                period_type=period_type,
                backup_type=backup_type,
                average_duration=0.0,
                max_duration=0.0,
                min_duration=0.0,
                total_duration=0.0,
                total_count=0,
                success_count=0,
                failure_count=0,
                partial_count=0,
            )
        
        durations = [record.duration for record in records]
        total_duration = sum(durations)
        average_duration = total_duration / len(durations) if durations else 0.0
        max_duration = max(durations) if durations else 0.0
        min_duration = min(durations) if durations else 0.0
        
        # Count by status
        success_count = sum(1 for r in records if r.status == BackupStatus.SUCCESS)
        failure_count = sum(1 for r in records if r.status == BackupStatus.FAILURE)
        partial_count = sum(1 for r in records if r.status == BackupStatus.PARTIAL)
        
        return AggregatedMetrics(
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            backup_type=backup_type,
            average_duration=average_duration,
            max_duration=max_duration,
            min_duration=min_duration,
            total_duration=total_duration,
            total_count=len(records),
            success_count=success_count,
            failure_count=failure_count,
            partial_count=partial_count,
        )
    
    def _get_week_start(self, target_date: date) -> date:
        """
        Get the Monday (week start) for a given date.
        
        Args:
            target_date: Target date
            
        Returns:
            Monday date of the week containing target_date
        """
        # Monday is 0 in isoweekday()
        days_since_monday = (target_date.isoweekday() - 1) % 7
        return target_date - timedelta(days=days_since_monday)
    
    def compute_all_aggregates(
        self,
        records: List[BackupRecord]
    ) -> Dict[str, List[AggregatedMetrics]]:
        """
        Compute all types of aggregates for backup records.
        
        Args:
            records: List of BackupRecord objects
            
        Returns:
            Dictionary with keys 'daily', 'weekly', 'monthly' containing lists of metrics
        """
        result = {}
        
        if PeriodType.DAY.value in self.aggregation_periods:
            result['daily'] = self.compute_daily_aggregates(records)
        
        if PeriodType.WEEK.value in self.aggregation_periods:
            result['weekly'] = self.compute_weekly_aggregates(records)
        
        if PeriodType.MONTH.value in self.aggregation_periods:
            result['monthly'] = self.compute_monthly_aggregates(records)
        
        return result
