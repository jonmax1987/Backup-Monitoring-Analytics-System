"""Historical comparison module for comparing metrics across periods."""

from typing import List, Optional, Dict, Tuple
from datetime import date, timedelta
from pydantic import BaseModel, Field

from backup_monitoring.processing.models import (
    AggregatedMetrics,
    DailyMetrics,
    WeeklyMetrics,
    MonthlyMetrics,
    PeriodType,
)


class ComparisonError(Exception):
    """Exception raised when comparison fails."""
    pass


class MetricDelta(BaseModel):
    """Represents the change in a metric between two periods."""
    
    metric_name: str = Field(..., description="Name of the metric")
    current_value: float = Field(..., description="Value in current period")
    previous_value: float = Field(..., description="Value in previous period")
    absolute_delta: float = Field(..., description="Absolute change (current - previous)")
    percentage_delta: float = Field(..., description="Percentage change")
    
    @property
    def is_increase(self) -> bool:
        """Whether the metric increased."""
        return self.absolute_delta > 0
    
    @property
    def is_decrease(self) -> bool:
        """Whether the metric decreased."""
        return self.absolute_delta < 0
    
    @property
    def is_unchanged(self) -> bool:
        """Whether the metric remained unchanged."""
        return abs(self.absolute_delta) < 0.0001  # Floating point tolerance


class PeriodComparison(BaseModel):
    """Comparison between two periods."""
    
    period_type: PeriodType = Field(..., description="Type of period being compared")
    backup_type: str = Field(..., description="Backup type being compared")
    
    # Period identifiers
    current_period_start: date = Field(..., description="Start date of current period")
    current_period_end: date = Field(..., description="End date of current period")
    previous_period_start: date = Field(..., description="Start date of previous period")
    previous_period_end: date = Field(..., description="End date of previous period")
    
    # Current period metrics
    current_metrics: AggregatedMetrics = Field(..., description="Metrics for current period")
    
    # Previous period metrics
    previous_metrics: Optional[AggregatedMetrics] = Field(None, description="Metrics for previous period")
    
    # Deltas
    duration_deltas: Dict[str, MetricDelta] = Field(default_factory=dict, description="Duration metric deltas")
    count_deltas: Dict[str, MetricDelta] = Field(default_factory=dict, description="Count metric deltas")
    rate_deltas: Dict[str, MetricDelta] = Field(default_factory=dict, description="Rate metric deltas")
    
    # Summary
    has_previous_data: bool = Field(..., description="Whether previous period data exists")
    
    @property
    def all_deltas(self) -> Dict[str, MetricDelta]:
        """Get all deltas combined."""
        return {**self.duration_deltas, **self.count_deltas, **self.rate_deltas}


class HistoricalComparator:
    """Compares aggregated metrics across periods."""
    
    def compare_daily(
        self,
        current: DailyMetrics,
        previous: Optional[DailyMetrics] = None
    ) -> PeriodComparison:
        """
        Compare daily metrics between two days.
        
        Args:
            current: Current day metrics
            previous: Previous day metrics (typically the day before)
            
        Returns:
            PeriodComparison object
        """
        if previous is None:
            # Find previous day
            previous_date = current.period_date - timedelta(days=1)
            previous = DailyMetrics(
                period_start=previous_date,
                period_end=previous_date,
                period_type=PeriodType.DAY,
                backup_type=current.backup_type,
                period_date=previous_date,
                average_duration=0.0,
                max_duration=0.0,
                min_duration=0.0,
                total_duration=0.0,
                total_count=0,
                success_count=0,
                failure_count=0,
                partial_count=0,
            )
        
        return self._compare_metrics(current, previous, PeriodType.DAY)
    
    def compare_weekly(
        self,
        current: WeeklyMetrics,
        previous: Optional[WeeklyMetrics] = None
    ) -> PeriodComparison:
        """
        Compare weekly metrics between two weeks.
        
        Args:
            current: Current week metrics
            previous: Previous week metrics (typically the week before)
            
        Returns:
            PeriodComparison object
        """
        if previous is None:
            # Find previous week
            previous_week_start = current.week_start - timedelta(weeks=1)
            previous_week_end = previous_week_start + timedelta(days=6)
            previous = WeeklyMetrics(
                period_start=previous_week_start,
                period_end=previous_week_end,
                period_type=PeriodType.WEEK,
                backup_type=current.backup_type,
                week_start=previous_week_start,
                week_end=previous_week_end,
                week_number=(previous_week_start.isocalendar()[1]),
                average_duration=0.0,
                max_duration=0.0,
                min_duration=0.0,
                total_duration=0.0,
                total_count=0,
                success_count=0,
                failure_count=0,
                partial_count=0,
            )
        
        return self._compare_metrics(current, previous, PeriodType.WEEK)
    
    def compare_monthly(
        self,
        current: MonthlyMetrics,
        previous: Optional[MonthlyMetrics] = None
    ) -> PeriodComparison:
        """
        Compare monthly metrics between two months.
        
        Args:
            current: Current month metrics
            previous: Previous month metrics (typically the month before)
            
        Returns:
            PeriodComparison object
        """
        if previous is None:
            # Find previous month
            if current.month == 1:
                previous_year = current.year - 1
                previous_month = 12
            else:
                previous_year = current.year
                previous_month = current.month - 1
            
            previous_month_start = date(previous_year, previous_month, 1)
            import calendar
            last_day = calendar.monthrange(previous_year, previous_month)[1]
            previous_month_end = date(previous_year, previous_month, last_day)
            
            previous = MonthlyMetrics(
                period_start=previous_month_start,
                period_end=previous_month_end,
                period_type=PeriodType.MONTH,
                backup_type=current.backup_type,
                year=previous_year,
                month=previous_month,
                average_duration=0.0,
                max_duration=0.0,
                min_duration=0.0,
                total_duration=0.0,
                total_count=0,
                success_count=0,
                failure_count=0,
                partial_count=0,
            )
        
        return self._compare_metrics(current, previous, PeriodType.MONTH)
    
    def compare_periods(
        self,
        current: AggregatedMetrics,
        previous: Optional[AggregatedMetrics] = None
    ) -> PeriodComparison:
        """
        Compare two periods of the same type.
        
        Args:
            current: Current period metrics
            previous: Previous period metrics
            
        Returns:
            PeriodComparison object
        """
        return self._compare_metrics(current, previous, current.period_type)
    
    def _compare_metrics(
        self,
        current: AggregatedMetrics,
        previous: Optional[AggregatedMetrics],
        period_type: PeriodType
    ) -> PeriodComparison:
        """
        Internal method to compare metrics.
        
        Args:
            current: Current period metrics
            previous: Previous period metrics (None if no previous data)
            period_type: Type of period
            
        Returns:
            PeriodComparison object
        """
        has_previous = previous is not None
        
        if previous is None:
            # Create zero metrics for comparison
            previous = AggregatedMetrics(
                period_start=current.period_start,
                period_end=current.period_end,
                period_type=period_type,
                backup_type=current.backup_type,
                average_duration=0.0,
                max_duration=0.0,
                min_duration=0.0,
                total_duration=0.0,
                total_count=0,
                success_count=0,
                failure_count=0,
                partial_count=0,
            )
        
        # Calculate duration deltas
        duration_deltas = {
            "average_duration": self._calculate_delta(
                "average_duration",
                current.average_duration,
                previous.average_duration
            ),
            "max_duration": self._calculate_delta(
                "max_duration",
                current.max_duration,
                previous.max_duration
            ),
            "min_duration": self._calculate_delta(
                "min_duration",
                current.min_duration,
                previous.min_duration
            ),
            "total_duration": self._calculate_delta(
                "total_duration",
                current.total_duration,
                previous.total_duration
            ),
        }
        
        # Calculate count deltas
        count_deltas = {
            "total_count": self._calculate_delta(
                "total_count",
                float(current.total_count),
                float(previous.total_count)
            ),
            "success_count": self._calculate_delta(
                "success_count",
                float(current.success_count),
                float(previous.success_count)
            ),
            "failure_count": self._calculate_delta(
                "failure_count",
                float(current.failure_count),
                float(previous.failure_count)
            ),
            "partial_count": self._calculate_delta(
                "partial_count",
                float(current.partial_count),
                float(previous.partial_count)
            ),
        }
        
        # Calculate rate deltas
        rate_deltas = {
            "success_rate": self._calculate_delta(
                "success_rate",
                current.success_rate,
                previous.success_rate
            ),
            "failure_rate": self._calculate_delta(
                "failure_rate",
                current.failure_rate,
                previous.failure_rate
            ),
        }
        
        return PeriodComparison(
            period_type=period_type,
            backup_type=current.backup_type,
            current_period_start=current.period_start,
            current_period_end=current.period_end,
            previous_period_start=previous.period_start,
            previous_period_end=previous.period_end,
            current_metrics=current,
            previous_metrics=previous if has_previous else None,
            duration_deltas=duration_deltas,
            count_deltas=count_deltas,
            rate_deltas=rate_deltas,
            has_previous_data=has_previous,
        )
    
    def _calculate_delta(
        self,
        metric_name: str,
        current_value: float,
        previous_value: float
    ) -> MetricDelta:
        """
        Calculate delta between two values.
        
        Args:
            metric_name: Name of the metric
            current_value: Current period value
            previous_value: Previous period value
            
        Returns:
            MetricDelta object
        """
        absolute_delta = current_value - previous_value
        
        # Calculate percentage delta
        if previous_value == 0:
            if current_value == 0:
                percentage_delta = 0.0
            else:
                # Can't divide by zero, use a large percentage or indicate new
                percentage_delta = 100.0 if current_value > 0 else -100.0
        else:
            percentage_delta = (absolute_delta / previous_value) * 100.0
        
        return MetricDelta(
            metric_name=metric_name,
            current_value=current_value,
            previous_value=previous_value,
            absolute_delta=absolute_delta,
            percentage_delta=percentage_delta,
        )
    
    def compare_multiple_periods(
        self,
        metrics_list: List[AggregatedMetrics],
        period_type: Optional[PeriodType] = None
    ) -> List[PeriodComparison]:
        """
        Compare multiple consecutive periods.
        
        Args:
            metrics_list: List of metrics ordered by period (oldest to newest)
            period_type: Optional period type (auto-detected if not provided)
            
        Returns:
            List of PeriodComparison objects comparing each period to the previous one
        """
        if not metrics_list:
            return []
        
        if len(metrics_list) == 1:
            # Only one period, compare to empty previous period
            period_type = period_type or metrics_list[0].period_type
            return [self._compare_metrics(metrics_list[0], None, period_type)]
        
        comparisons = []
        
        for i in range(1, len(metrics_list)):
            current = metrics_list[i]
            previous = metrics_list[i - 1]
            
            # Ensure same backup type
            if current.backup_type != previous.backup_type:
                continue
            
            comparison = self._compare_metrics(
                current,
                previous,
                period_type or current.period_type
            )
            comparisons.append(comparison)
        
        return comparisons
