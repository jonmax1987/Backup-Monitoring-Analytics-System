"""Tests for integration layer."""

import pytest
from datetime import date, datetime, timedelta
import pytz

from backup_monitoring.integration.adapters import DataAdapter, UIAdapter, MonitoringAdapter
from backup_monitoring.integration.data_provider import (
    IntegrationDataProvider,
    StandardDataAdapter,
    StandardUIAdapter,
    StandardMonitoringAdapter,
)
from backup_monitoring.integration.mocks import (
    MockDataProvider,
    MockUIAdapter,
    MockMonitoringAdapter,
)
from backup_monitoring.data_loader.models import BackupRecord, BackupStatus
from backup_monitoring.processing.models import DailyMetrics, PeriodType
from backup_monitoring.anomaly_detection.models import AnomalyDetectionResult


@pytest.fixture
def sample_backup_records():
    """Create sample backup records."""
    base_date = datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC)
    return [
        BackupRecord(
            backup_id=f"backup-{i:03d}",
            start_time=base_date + timedelta(days=i),
            end_time=base_date + timedelta(days=i, minutes=30),
            status=BackupStatus.SUCCESS,
            backup_type="database" if i % 2 == 0 else "filesystem",
            source_system=f"system-{i % 3}",
        )
        for i in range(10)
    ]


@pytest.fixture
def sample_daily_metrics():
    """Create sample daily metrics."""
    return [
        DailyMetrics(
            period_start=date(2024, 1, i + 1),
            period_end=date(2024, 1, i + 1),
            period_type=PeriodType.DAY,
            backup_type="database",
            period_date=date(2024, 1, i + 1),
            average_duration=1800.0,
            max_duration=3600.0,
            min_duration=900.0,
            total_duration=1800.0,
            total_count=5,
            success_count=5,
            failure_count=0,
            partial_count=0,
        )
        for i in range(5)
    ]


def test_integration_data_provider(sample_backup_records, sample_daily_metrics):
    """Test IntegrationDataProvider."""
    provider = IntegrationDataProvider(
        backup_records=sample_backup_records,
        daily_metrics=sample_daily_metrics,
    )
    
    assert len(provider.backup_records) == 10
    assert len(provider.daily_metrics) == 5


def test_standard_data_adapter_get_backup_records(sample_backup_records):
    """Test StandardDataAdapter.get_backup_records."""
    provider = IntegrationDataProvider(backup_records=sample_backup_records)
    adapter = StandardDataAdapter(provider)
    
    # Get all records
    records = adapter.get_backup_records()
    assert len(records) == 10
    
    # Filter by backup type
    db_records = adapter.get_backup_records(backup_type="database")
    assert len(db_records) == 5
    
    # Filter by date range
    start_date = date(2024, 1, 3)
    end_date = date(2024, 1, 7)
    filtered = adapter.get_backup_records(start_date=start_date, end_date=end_date)
    assert len(filtered) == 5


def test_standard_data_adapter_get_daily_metrics(sample_daily_metrics):
    """Test StandardDataAdapter.get_daily_metrics."""
    provider = IntegrationDataProvider(daily_metrics=sample_daily_metrics)
    adapter = StandardDataAdapter(provider)
    
    # Get all metrics
    metrics = adapter.get_daily_metrics()
    assert len(metrics) == 5
    
    # Filter by date range
    start_date = date(2024, 1, 2)
    end_date = date(2024, 1, 4)
    filtered = adapter.get_daily_metrics(start_date=start_date, end_date=end_date)
    assert len(filtered) == 3


def test_standard_ui_adapter_get_dashboard_summary(sample_backup_records, sample_daily_metrics):
    """Test StandardUIAdapter.get_dashboard_summary."""
    provider = IntegrationDataProvider(
        backup_records=sample_backup_records,
        daily_metrics=sample_daily_metrics,
    )
    adapter = StandardUIAdapter(provider)
    
    summary = adapter.get_dashboard_summary()
    
    assert "total_backups" in summary
    assert "total_success" in summary
    assert "total_failure" in summary
    assert "success_rate" in summary
    assert "backup_types" in summary
    assert "date_range" in summary


def test_standard_ui_adapter_get_backup_types(sample_backup_records):
    """Test StandardUIAdapter.get_backup_types."""
    provider = IntegrationDataProvider(backup_records=sample_backup_records)
    adapter = StandardUIAdapter(provider)
    
    types = adapter.get_backup_types()
    
    assert "database" in types
    assert "filesystem" in types


def test_standard_ui_adapter_get_date_range(sample_backup_records):
    """Test StandardUIAdapter.get_date_range."""
    provider = IntegrationDataProvider(backup_records=sample_backup_records)
    adapter = StandardUIAdapter(provider)
    
    date_range = adapter.get_date_range()
    
    assert "start" in date_range
    assert "end" in date_range
    assert isinstance(date_range["start"], date)
    assert isinstance(date_range["end"], date)


def test_standard_monitoring_adapter_get_metrics(sample_daily_metrics):
    """Test StandardMonitoringAdapter.get_metrics."""
    provider = IntegrationDataProvider(daily_metrics=sample_daily_metrics)
    adapter = StandardMonitoringAdapter(provider)
    
    metrics = adapter.get_metrics()
    
    assert "backup_total" in metrics
    assert "backup_success" in metrics
    assert "backup_failure" in metrics
    assert "backup_success_rate" in metrics
    assert "backup_avg_duration_seconds" in metrics
    assert isinstance(metrics["backup_total"], float)


def test_standard_monitoring_adapter_get_metric_labels(sample_daily_metrics):
    """Test StandardMonitoringAdapter.get_metric_labels."""
    provider = IntegrationDataProvider(daily_metrics=sample_daily_metrics)
    adapter = StandardMonitoringAdapter(provider)
    
    labeled = adapter.get_metric_labels()
    
    assert len(labeled) > 0
    for metric_name, data in labeled.items():
        assert "value" in data
        assert "labels" in data
        assert "system" in data["labels"]


def test_standard_monitoring_adapter_export_prometheus_format(sample_daily_metrics):
    """Test StandardMonitoringAdapter.export_prometheus_format."""
    provider = IntegrationDataProvider(daily_metrics=sample_daily_metrics)
    adapter = StandardMonitoringAdapter(provider)
    
    prometheus_format = adapter.export_prometheus_format()
    
    assert isinstance(prometheus_format, str)
    assert "# HELP" in prometheus_format
    assert "# TYPE" in prometheus_format
    assert "backup_total" in prometheus_format or "backup_success" in prometheus_format


def test_mock_data_provider():
    """Test MockDataProvider."""
    provider = MockDataProvider()
    
    assert len(provider.backup_records) > 0
    assert len(provider.daily_metrics) > 0
    assert len(provider.weekly_metrics) > 0
    assert len(provider.monthly_metrics) > 0


def test_mock_ui_adapter():
    """Test MockUIAdapter."""
    adapter = MockUIAdapter()
    
    summary = adapter.get_dashboard_summary()
    assert "total_backups" in summary
    
    types = adapter.get_backup_types()
    assert len(types) > 0
    
    date_range = adapter.get_date_range()
    assert "start" in date_range


def test_mock_monitoring_adapter():
    """Test MockMonitoringAdapter."""
    adapter = MockMonitoringAdapter()
    
    metrics = adapter.get_metrics()
    assert len(metrics) > 0
    
    prometheus_format = adapter.export_prometheus_format()
    assert len(prometheus_format) > 0


def test_data_provider_update_data(sample_backup_records):
    """Test updating data in provider."""
    provider = IntegrationDataProvider()
    
    provider.update_data(backup_records=sample_backup_records)
    assert len(provider.backup_records) == 10
    
    # Update with new data
    new_records = sample_backup_records[:5]
    provider.update_data(backup_records=new_records)
    assert len(provider.backup_records) == 5


def test_adapter_filtering_combinations(sample_backup_records, sample_daily_metrics):
    """Test adapter filtering with multiple criteria."""
    provider = IntegrationDataProvider(
        backup_records=sample_backup_records,
        daily_metrics=sample_daily_metrics,
    )
    adapter = StandardDataAdapter(provider)
    
    # Filter by date and backup type
    records = adapter.get_backup_records(
        start_date=date(2024, 1, 3),
        end_date=date(2024, 1, 7),
        backup_type="database"
    )
    assert len(records) > 0
    assert all(r.backup_type == "database" for r in records)


def test_ui_adapter_inheritance():
    """Test that UIAdapter inherits from DataAdapter."""
    adapter = MockUIAdapter()
    
    # Should have DataAdapter methods
    records = adapter.get_backup_records()
    assert isinstance(records, list)
    
    metrics = adapter.get_daily_metrics()
    assert isinstance(metrics, list)
    
    # Should have UIAdapter methods
    summary = adapter.get_dashboard_summary()
    assert isinstance(summary, dict)


def test_empty_data_provider():
    """Test adapters with empty data provider."""
    provider = IntegrationDataProvider()
    adapter = StandardDataAdapter(provider)
    
    records = adapter.get_backup_records()
    assert records == []
    
    metrics = adapter.get_daily_metrics()
    assert metrics == []
    
    ui_adapter = StandardUIAdapter(provider)
    summary = ui_adapter.get_dashboard_summary()
    assert summary["total_backups"] == 0
