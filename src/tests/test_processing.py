"""Tests for processing engine."""

import pytest
from datetime import date, datetime, timedelta
import pytz
import calendar

from backup_monitoring.processing.processor import ProcessingEngine, ProcessingError
from backup_monitoring.processing.models import (
    AggregatedMetrics,
    DailyMetrics,
    WeeklyMetrics,
    MonthlyMetrics,
    PeriodType,
)
from backup_monitoring.data_loader.models import BackupRecord, BackupStatus


@pytest.fixture
def sample_records():
    """Create sample backup records for testing."""
    base_date = datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC)
    
    return [
        # Day 1 - database backups
        BackupRecord(
            backup_id="backup-001",
            start_time=base_date,
            end_time=base_date + timedelta(minutes=30),
            status=BackupStatus.SUCCESS,
            backup_type="database",
            source_system="db-01"
        ),
        BackupRecord(
            backup_id="backup-002",
            start_time=base_date + timedelta(hours=1),
            end_time=base_date + timedelta(hours=1, minutes=45),
            status=BackupStatus.SUCCESS,
            backup_type="database",
            source_system="db-01"
        ),
        # Day 1 - filesystem backup
        BackupRecord(
            backup_id="backup-003",
            start_time=base_date + timedelta(hours=2),
            end_time=base_date + timedelta(hours=2, minutes=15),
            status=BackupStatus.SUCCESS,
            backup_type="filesystem",
            source_system="fs-01"
        ),
        # Day 2 - database backup
        BackupRecord(
            backup_id="backup-004",
            start_time=base_date + timedelta(days=1),
            end_time=base_date + timedelta(days=1, minutes=20),
            status=BackupStatus.FAILURE,
            backup_type="database",
            source_system="db-01"
        ),
    ]


@pytest.fixture
def processor():
    """Create a ProcessingEngine instance."""
    return ProcessingEngine()


def test_compute_daily_aggregates(processor, sample_records):
    """Test daily aggregate computation."""
    daily_metrics = processor.compute_daily_aggregates(sample_records)
    
    assert len(daily_metrics) > 0
    
    # Check that we have metrics for each day/type combination
    dates = {m.period_date for m in daily_metrics}
    assert date(2024, 1, 1) in dates
    assert date(2024, 1, 2) in dates
    
    # Check database metrics for day 1
    day1_db = next((m for m in daily_metrics if m.period_date == date(2024, 1, 1) and m.backup_type == "database"), None)
    assert day1_db is not None
    assert day1_db.total_count == 2
    assert day1_db.success_count == 2
    assert day1_db.failure_count == 0
    assert day1_db.average_duration > 0
    assert day1_db.max_duration >= day1_db.min_duration


def test_compute_daily_aggregates_specific_date(processor, sample_records):
    """Test daily aggregate computation for a specific date."""
    target_date = date(2024, 1, 1)
    daily_metrics = processor.compute_daily_aggregates(sample_records, target_date=target_date)
    
    # Should only have metrics for the target date
    assert all(m.period_date == target_date for m in daily_metrics)
    assert len(daily_metrics) == 2  # database and filesystem


def test_compute_daily_aggregates_empty_list(processor):
    """Test daily aggregate computation with empty list."""
    daily_metrics = processor.compute_daily_aggregates([])
    assert daily_metrics == []


def test_compute_daily_aggregates_single_record(processor):
    """Test daily aggregate computation with single record."""
    record = BackupRecord(
        backup_id="single",
        start_time=datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC),
        end_time=datetime(2024, 1, 1, 10, 30, 0, tzinfo=pytz.UTC),
        status=BackupStatus.SUCCESS,
        backup_type="database"
    )
    
    daily_metrics = processor.compute_daily_aggregates([record])
    assert len(daily_metrics) == 1
    assert daily_metrics[0].total_count == 1
    assert daily_metrics[0].average_duration == 1800.0  # 30 minutes
    assert daily_metrics[0].max_duration == 1800.0
    assert daily_metrics[0].min_duration == 1800.0


def test_compute_weekly_aggregates(processor, sample_records):
    """Test weekly aggregate computation."""
    weekly_metrics = processor.compute_weekly_aggregates(sample_records)
    
    assert len(weekly_metrics) > 0
    
    # Check that week_start is a Monday
    for metric in weekly_metrics:
        assert metric.week_start.weekday() == 0  # Monday is 0
        assert metric.week_end.weekday() == 6  # Sunday is 6
        assert metric.week_number > 0


def test_compute_weekly_aggregates_specific_week(processor, sample_records):
    """Test weekly aggregate computation for a specific week."""
    # Get the week start for Jan 1, 2024 (which is a Monday)
    week_start = date(2024, 1, 1)
    weekly_metrics = processor.compute_weekly_aggregates(sample_records, week_start=week_start)
    
    assert all(m.week_start == week_start for m in weekly_metrics)


def test_compute_weekly_aggregates_empty_list(processor):
    """Test weekly aggregate computation with empty list."""
    weekly_metrics = processor.compute_weekly_aggregates([])
    assert weekly_metrics == []


def test_compute_monthly_aggregates(processor, sample_records):
    """Test monthly aggregate computation."""
    monthly_metrics = processor.compute_monthly_aggregates(sample_records)
    
    assert len(monthly_metrics) > 0
    
    # Check that we have metrics for January 2024
    jan_metrics = [m for m in monthly_metrics if m.year == 2024 and m.month == 1]
    assert len(jan_metrics) > 0
    
    for metric in jan_metrics:
        assert metric.year == 2024
        assert metric.month == 1
        assert 1 <= metric.month <= 12


def test_compute_monthly_aggregates_specific_month(processor, sample_records):
    """Test monthly aggregate computation for a specific month."""
    monthly_metrics = processor.compute_monthly_aggregates(sample_records, year=2024, month=1)
    
    assert all(m.year == 2024 and m.month == 1 for m in monthly_metrics)


def test_compute_monthly_aggregates_empty_list(processor):
    """Test monthly aggregate computation with empty list."""
    monthly_metrics = processor.compute_monthly_aggregates([])
    assert monthly_metrics == []


def test_status_counting(processor):
    """Test that status counting works correctly."""
    base_date = datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC)
    
    records = [
        BackupRecord(
            backup_id=f"backup-{i}",
            start_time=base_date + timedelta(hours=i),
            end_time=base_date + timedelta(hours=i, minutes=30),
            status=status,
            backup_type="database"
        )
        for i, status in enumerate([
            BackupStatus.SUCCESS,
            BackupStatus.SUCCESS,
            BackupStatus.FAILURE,
            BackupStatus.PARTIAL,
        ])
    ]
    
    daily_metrics = processor.compute_daily_aggregates(records)
    assert len(daily_metrics) == 1
    
    metrics = daily_metrics[0]
    assert metrics.total_count == 4
    assert metrics.success_count == 2
    assert metrics.failure_count == 1
    assert metrics.partial_count == 1
    assert metrics.success_rate == 50.0
    assert metrics.failure_rate == 25.0


def test_duration_calculations(processor):
    """Test that duration calculations are correct."""
    base_date = datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC)
    
    records = [
        BackupRecord(
            backup_id="backup-001",
            start_time=base_date,
            end_time=base_date + timedelta(minutes=10),  # 10 minutes
            status=BackupStatus.SUCCESS,
            backup_type="database"
        ),
        BackupRecord(
            backup_id="backup-002",
            start_time=base_date + timedelta(hours=1),
            end_time=base_date + timedelta(hours=1, minutes=30),  # 30 minutes
            status=BackupStatus.SUCCESS,
            backup_type="database"
        ),
        BackupRecord(
            backup_id="backup-003",
            start_time=base_date + timedelta(hours=2),
            end_time=base_date + timedelta(hours=2, minutes=5),  # 5 minutes
            status=BackupStatus.SUCCESS,
            backup_type="database"
        ),
    ]
    
    daily_metrics = processor.compute_daily_aggregates(records)
    metrics = daily_metrics[0]
    
    # Average: (10 + 30 + 5) / 3 = 15 minutes = 900 seconds
    assert abs(metrics.average_duration - 900.0) < 0.01
    assert metrics.max_duration == 1800.0  # 30 minutes
    assert metrics.min_duration == 300.0  # 5 minutes
    assert metrics.total_duration == 2700.0  # 45 minutes total


def test_multiple_backup_types(processor):
    """Test aggregation with multiple backup types."""
    base_date = datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC)
    
    records = [
        BackupRecord(
            backup_id="db-001",
            start_time=base_date,
            end_time=base_date + timedelta(minutes=30),
            status=BackupStatus.SUCCESS,
            backup_type="database"
        ),
        BackupRecord(
            backup_id="fs-001",
            start_time=base_date + timedelta(hours=1),
            end_time=base_date + timedelta(hours=1, minutes=15),
            status=BackupStatus.SUCCESS,
            backup_type="filesystem"
        ),
    ]
    
    daily_metrics = processor.compute_daily_aggregates(records)
    
    # Should have separate metrics for each backup type
    assert len(daily_metrics) == 2
    
    db_metrics = next(m for m in daily_metrics if m.backup_type == "database")
    fs_metrics = next(m for m in daily_metrics if m.backup_type == "filesystem")
    
    assert db_metrics.total_count == 1
    assert fs_metrics.total_count == 1


def test_unknown_backup_type(processor):
    """Test aggregation with unknown/null backup type."""
    base_date = datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC)
    
    records = [
        BackupRecord(
            backup_id="unknown-001",
            start_time=base_date,
            end_time=base_date + timedelta(minutes=30),
            status=BackupStatus.SUCCESS,
            backup_type=None  # No backup type
        ),
    ]
    
    daily_metrics = processor.compute_daily_aggregates(records)
    assert len(daily_metrics) == 1
    assert daily_metrics[0].backup_type == "unknown"


def test_compute_all_aggregates(processor, sample_records):
    """Test computing all types of aggregates."""
    result = processor.compute_all_aggregates(sample_records)
    
    assert 'daily' in result
    assert 'weekly' in result
    assert 'monthly' in result
    
    assert len(result['daily']) > 0
    assert len(result['weekly']) > 0
    assert len(result['monthly']) > 0


def test_week_start_calculation(processor):
    """Test that week start calculation is correct."""
    # Monday
    monday = date(2024, 1, 1)
    assert processor._get_week_start(monday) == monday
    
    # Tuesday
    tuesday = date(2024, 1, 2)
    assert processor._get_week_start(tuesday) == monday
    
    # Sunday
    sunday = date(2024, 1, 7)
    assert processor._get_week_start(sunday) == monday


def test_month_end_calculation(processor):
    """Test that month end calculation handles different month lengths."""
    # Create records for different months to test month end calculation
    jan_record = BackupRecord(
        backup_id="jan-001",
        start_time=datetime(2024, 1, 15, 10, 0, 0, tzinfo=pytz.UTC),
        end_time=datetime(2024, 1, 15, 10, 30, 0, tzinfo=pytz.UTC),
        status=BackupStatus.SUCCESS,
        backup_type="database"
    )
    
    feb_record = BackupRecord(
        backup_id="feb-001",
        start_time=datetime(2024, 2, 15, 10, 0, 0, tzinfo=pytz.UTC),
        end_time=datetime(2024, 2, 15, 10, 30, 0, tzinfo=pytz.UTC),
        status=BackupStatus.SUCCESS,
        backup_type="database"
    )
    
    apr_record = BackupRecord(
        backup_id="apr-001",
        start_time=datetime(2024, 4, 15, 10, 0, 0, tzinfo=pytz.UTC),
        end_time=datetime(2024, 4, 15, 10, 30, 0, tzinfo=pytz.UTC),
        status=BackupStatus.SUCCESS,
        backup_type="database"
    )
    
    # January has 31 days
    jan_metrics = processor.compute_monthly_aggregates([jan_record], year=2024, month=1)
    assert len(jan_metrics) > 0
    assert jan_metrics[0].period_end.day == 31
    
    # February 2024 has 29 days (leap year)
    feb_metrics = processor.compute_monthly_aggregates([feb_record], year=2024, month=2)
    assert len(feb_metrics) > 0
    assert feb_metrics[0].period_end.day == 29
    
    # April has 30 days
    apr_metrics = processor.compute_monthly_aggregates([apr_record], year=2024, month=4)
    assert len(apr_metrics) > 0
    assert apr_metrics[0].period_end.day == 30


def test_metrics_properties(processor, sample_records):
    """Test that computed metrics have correct properties."""
    daily_metrics = processor.compute_daily_aggregates(sample_records)
    
    for metric in daily_metrics:
        assert metric.period_start <= metric.period_end
        assert metric.total_count > 0
        assert metric.total_count == metric.success_count + metric.failure_count + metric.partial_count
        assert metric.average_duration >= 0
        assert metric.max_duration >= metric.min_duration
        assert 0 <= metric.success_rate <= 100
        assert 0 <= metric.failure_rate <= 100
