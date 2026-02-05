"""Tests for historical comparison module."""

import pytest
from datetime import date, datetime, timedelta
import pytz

from backup_monitoring.processing.comparison import (
    HistoricalComparator,
    ComparisonError,
    PeriodComparison,
    MetricDelta,
)
from backup_monitoring.processing.models import (
    DailyMetrics,
    WeeklyMetrics,
    MonthlyMetrics,
    PeriodType,
    AggregatedMetrics,
)
from backup_monitoring.data_loader.models import BackupStatus


@pytest.fixture
def comparator():
    """Create a HistoricalComparator instance."""
    return HistoricalComparator()


@pytest.fixture
def sample_daily_metrics():
    """Create sample daily metrics for testing."""
    base_date = date(2024, 1, 2)
    
    current = DailyMetrics(
        period_start=base_date,
        period_end=base_date,
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=base_date,
        average_duration=1800.0,  # 30 minutes
        max_duration=3600.0,  # 1 hour
        min_duration=900.0,  # 15 minutes
        total_duration=7200.0,  # 2 hours total
        total_count=4,
        success_count=3,
        failure_count=1,
        partial_count=0,
    )
    
    previous = DailyMetrics(
        period_start=base_date - timedelta(days=1),
        period_end=base_date - timedelta(days=1),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=base_date - timedelta(days=1),
        average_duration=1500.0,  # 25 minutes
        max_duration=3000.0,  # 50 minutes
        min_duration=600.0,  # 10 minutes
        total_duration=4500.0,  # 1.25 hours total
        total_count=3,
        success_count=3,
        failure_count=0,
        partial_count=0,
    )
    
    return current, previous


def test_compare_daily_with_previous(comparator, sample_daily_metrics):
    """Test daily comparison with previous day."""
    current, previous = sample_daily_metrics
    
    comparison = comparator.compare_daily(current, previous)
    
    assert comparison.period_type == PeriodType.DAY
    assert comparison.backup_type == "database"
    assert comparison.has_previous_data is True
    assert comparison.current_metrics == current
    assert comparison.previous_metrics == previous
    
    # Check duration deltas
    assert "average_duration" in comparison.duration_deltas
    avg_delta = comparison.duration_deltas["average_duration"]
    assert avg_delta.absolute_delta == 300.0  # 1800 - 1500
    assert abs(avg_delta.percentage_delta - 20.0) < 0.1  # 20% increase
    
    # Check count deltas
    assert "total_count" in comparison.count_deltas
    count_delta = comparison.count_deltas["total_count"]
    assert count_delta.absolute_delta == 1.0  # 4 - 3
    assert abs(count_delta.percentage_delta - 33.33) < 0.1  # ~33% increase


def test_compare_daily_without_previous(comparator, sample_daily_metrics):
    """Test daily comparison without previous day data."""
    current, _ = sample_daily_metrics
    
    comparison = comparator.compare_daily(current, None)
    
    assert comparison.has_previous_data is False
    assert comparison.previous_metrics is None
    
    # Should compare to zero values
    avg_delta = comparison.duration_deltas["average_duration"]
    assert avg_delta.previous_value == 0.0
    assert avg_delta.absolute_delta == current.average_duration


def test_compare_weekly(comparator):
    """Test weekly comparison."""
    week1_start = date(2024, 1, 1)  # Monday
    week1_end = date(2024, 1, 7)  # Sunday
    
    week2_start = date(2024, 1, 8)  # Next Monday
    week2_end = date(2024, 1, 14)  # Next Sunday
    
    current = WeeklyMetrics(
        period_start=week2_start,
        period_end=week2_end,
        period_type=PeriodType.WEEK,
        backup_type="database",
        week_start=week2_start,
        week_end=week2_end,
        week_number=2,
        average_duration=2000.0,
        max_duration=4000.0,
        min_duration=1000.0,
        total_duration=10000.0,
        total_count=5,
        success_count=4,
        failure_count=1,
        partial_count=0,
    )
    
    previous = WeeklyMetrics(
        period_start=week1_start,
        period_end=week1_end,
        period_type=PeriodType.WEEK,
        backup_type="database",
        week_start=week1_start,
        week_end=week1_end,
        week_number=1,
        average_duration=1800.0,
        max_duration=3600.0,
        min_duration=900.0,
        total_duration=9000.0,
        total_count=5,
        success_count=5,
        failure_count=0,
        partial_count=0,
    )
    
    comparison = comparator.compare_weekly(current, previous)
    
    assert comparison.period_type == PeriodType.WEEK
    assert comparison.current_period_start == week2_start
    assert comparison.previous_period_start == week1_start
    
    # Check that failure count increased
    failure_delta = comparison.count_deltas["failure_count"]
    assert failure_delta.absolute_delta == 1.0


def test_compare_monthly(comparator):
    """Test monthly comparison."""
    current = MonthlyMetrics(
        period_start=date(2024, 2, 1),
        period_end=date(2024, 2, 29),
        period_type=PeriodType.MONTH,
        backup_type="database",
        year=2024,
        month=2,
        average_duration=1900.0,
        max_duration=3800.0,
        min_duration=950.0,
        total_duration=19000.0,
        total_count=10,
        success_count=9,
        failure_count=1,
        partial_count=0,
    )
    
    previous = MonthlyMetrics(
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
        period_type=PeriodType.MONTH,
        backup_type="database",
        year=2024,
        month=1,
        average_duration=1700.0,
        max_duration=3400.0,
        min_duration=850.0,
        total_duration=17000.0,
        total_count=10,
        success_count=10,
        failure_count=0,
        partial_count=0,
    )
    
    comparison = comparator.compare_monthly(current, previous)
    
    assert comparison.period_type == PeriodType.MONTH
    assert comparison.current_metrics.year == 2024
    assert comparison.current_metrics.month == 2
    assert comparison.previous_metrics.year == 2024
    assert comparison.previous_metrics.month == 1


def test_compare_monthly_year_boundary(comparator):
    """Test monthly comparison across year boundary."""
    current = MonthlyMetrics(
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
        period_type=PeriodType.MONTH,
        backup_type="database",
        year=2024,
        month=1,
        average_duration=1800.0,
        max_duration=3600.0,
        min_duration=900.0,
        total_duration=18000.0,
        total_count=10,
        success_count=10,
        failure_count=0,
        partial_count=0,
    )
    
    # Compare without previous - should find December of previous year
    comparison = comparator.compare_monthly(current, None)
    
    assert comparison.has_previous_data is False
    assert comparison.previous_period_start.year == 2023
    assert comparison.previous_period_start.month == 12


def test_metric_delta_properties():
    """Test MetricDelta properties."""
    # Increase
    delta_increase = MetricDelta(
        metric_name="test",
        current_value=200.0,
        previous_value=100.0,
        absolute_delta=100.0,
        percentage_delta=100.0,
    )
    assert delta_increase.is_increase is True
    assert delta_increase.is_decrease is False
    assert delta_increase.is_unchanged is False
    
    # Decrease
    delta_decrease = MetricDelta(
        metric_name="test",
        current_value=50.0,
        previous_value=100.0,
        absolute_delta=-50.0,
        percentage_delta=-50.0,
    )
    assert delta_decrease.is_increase is False
    assert delta_decrease.is_decrease is True
    assert delta_decrease.is_unchanged is False
    
    # Unchanged
    delta_unchanged = MetricDelta(
        metric_name="test",
        current_value=100.0,
        previous_value=100.0,
        absolute_delta=0.0,
        percentage_delta=0.0,
    )
    assert delta_unchanged.is_increase is False
    assert delta_unchanged.is_decrease is False
    assert delta_unchanged.is_unchanged is True


def test_percentage_delta_zero_previous(comparator):
    """Test percentage delta calculation when previous value is zero."""
    current = DailyMetrics(
        period_start=date(2024, 1, 2),
        period_end=date(2024, 1, 2),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 2),
        average_duration=1800.0,
        max_duration=3600.0,
        min_duration=900.0,
        total_duration=1800.0,
        total_count=1,
        success_count=1,
        failure_count=0,
        partial_count=0,
    )
    
    previous = DailyMetrics(
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 1),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 1),
        average_duration=0.0,
        max_duration=0.0,
        min_duration=0.0,
        total_duration=0.0,
        total_count=0,
        success_count=0,
        failure_count=0,
        partial_count=0,
    )
    
    comparison = comparator.compare_daily(current, previous)
    
    # When previous is zero and current is positive, percentage should be 100%
    avg_delta = comparison.duration_deltas["average_duration"]
    assert avg_delta.percentage_delta == 100.0


def test_percentage_delta_both_zero(comparator):
    """Test percentage delta when both values are zero."""
    current = DailyMetrics(
        period_start=date(2024, 1, 2),
        period_end=date(2024, 1, 2),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 2),
        average_duration=0.0,
        max_duration=0.0,
        min_duration=0.0,
        total_duration=0.0,
        total_count=0,
        success_count=0,
        failure_count=0,
        partial_count=0,
    )
    
    previous = DailyMetrics(
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 1),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 1),
        average_duration=0.0,
        max_duration=0.0,
        min_duration=0.0,
        total_duration=0.0,
        total_count=0,
        success_count=0,
        failure_count=0,
        partial_count=0,
    )
    
    comparison = comparator.compare_daily(current, previous)
    
    avg_delta = comparison.duration_deltas["average_duration"]
    assert avg_delta.percentage_delta == 0.0
    assert avg_delta.is_unchanged is True


def test_compare_multiple_periods(comparator):
    """Test comparing multiple consecutive periods."""
    dates = [date(2024, 1, i) for i in range(1, 4)]
    
    metrics_list = [
        DailyMetrics(
            period_start=d,
            period_end=d,
            period_type=PeriodType.DAY,
            backup_type="database",
            period_date=d,
            average_duration=1000.0 * (i + 1),  # Increasing
            max_duration=2000.0 * (i + 1),
            min_duration=500.0 * (i + 1),
            total_duration=1000.0 * (i + 1),
            total_count=i + 1,
            success_count=i + 1,
            failure_count=0,
            partial_count=0,
        )
        for i, d in enumerate(dates)
    ]
    
    comparisons = comparator.compare_multiple_periods(metrics_list)
    
    # Should have 2 comparisons (day 2 vs day 1, day 3 vs day 2)
    assert len(comparisons) == 2
    
    # First comparison: day 2 vs day 1
    assert comparisons[0].current_period_start == dates[1]
    assert comparisons[0].previous_period_start == dates[0]
    
    # Second comparison: day 3 vs day 2
    assert comparisons[1].current_period_start == dates[2]
    assert comparisons[1].previous_period_start == dates[1]


def test_compare_multiple_periods_single(comparator):
    """Test comparing multiple periods with only one period."""
    metrics_list = [
        DailyMetrics(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 1),
            period_type=PeriodType.DAY,
            backup_type="database",
            period_date=date(2024, 1, 1),
            average_duration=1800.0,
            max_duration=3600.0,
            min_duration=900.0,
            total_duration=1800.0,
            total_count=1,
            success_count=1,
            failure_count=0,
            partial_count=0,
        )
    ]
    
    comparisons = comparator.compare_multiple_periods(metrics_list)
    
    assert len(comparisons) == 1
    assert comparisons[0].has_previous_data is False


def test_compare_multiple_periods_empty(comparator):
    """Test comparing multiple periods with empty list."""
    comparisons = comparator.compare_multiple_periods([])
    assert comparisons == []


def test_compare_multiple_periods_different_backup_types(comparator):
    """Test that different backup types are not compared."""
    metrics_list = [
        DailyMetrics(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 1),
            period_type=PeriodType.DAY,
            backup_type="database",
            period_date=date(2024, 1, 1),
            average_duration=1800.0,
            max_duration=3600.0,
            min_duration=900.0,
            total_duration=1800.0,
            total_count=1,
            success_count=1,
            failure_count=0,
            partial_count=0,
        ),
        DailyMetrics(
            period_start=date(2024, 1, 2),
            period_end=date(2024, 1, 2),
            period_type=PeriodType.DAY,
            backup_type="filesystem",  # Different backup type
            period_date=date(2024, 1, 2),
            average_duration=1800.0,
            max_duration=3600.0,
            min_duration=900.0,
            total_duration=1800.0,
            total_count=1,
            success_count=1,
            failure_count=0,
            partial_count=0,
        ),
    ]
    
    comparisons = comparator.compare_multiple_periods(metrics_list)
    
    # Should skip comparison due to different backup types
    assert len(comparisons) == 0


def test_rate_deltas(comparator, sample_daily_metrics):
    """Test that rate deltas are calculated correctly."""
    current, previous = sample_daily_metrics
    
    comparison = comparator.compare_daily(current, previous)
    
    assert "success_rate" in comparison.rate_deltas
    assert "failure_rate" in comparison.rate_deltas
    
    # Current: 3/4 = 75%, Previous: 3/3 = 100%
    success_rate_delta = comparison.rate_deltas["success_rate"]
    assert success_rate_delta.current_value == 75.0
    assert success_rate_delta.previous_value == 100.0
    assert success_rate_delta.absolute_delta == -25.0  # Decreased


def test_all_deltas_property(comparator, sample_daily_metrics):
    """Test that all_deltas property combines all delta types."""
    current, previous = sample_daily_metrics
    
    comparison = comparator.compare_daily(current, previous)
    
    all_deltas = comparison.all_deltas
    
    # Should contain duration, count, and rate deltas
    assert "average_duration" in all_deltas
    assert "total_count" in all_deltas
    assert "success_rate" in all_deltas
    
    assert len(all_deltas) == len(comparison.duration_deltas) + \
           len(comparison.count_deltas) + \
           len(comparison.rate_deltas)
