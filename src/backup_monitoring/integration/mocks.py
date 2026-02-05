"""Mock adapters for testing."""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
import pytz

from backup_monitoring.integration.adapters import UIAdapter, MonitoringAdapter
from backup_monitoring.integration.data_provider import IntegrationDataProvider, StandardUIAdapter, StandardMonitoringAdapter
from backup_monitoring.data_loader.models import BackupRecord, BackupStatus
from backup_monitoring.processing.models import DailyMetrics, WeeklyMetrics, MonthlyMetrics, PeriodType
from backup_monitoring.anomaly_detection.models import AnomalyDetectionResult


class MockDataProvider(IntegrationDataProvider):
    """Mock data provider with sample data for testing."""
    
    def __init__(self):
        """Initialize with mock data."""
        # Create sample backup records
        base_date = datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC)
        backup_records = [
            BackupRecord(
                backup_id=f"backup-{i:03d}",
                start_time=base_date + timedelta(days=i, hours=i % 24),
                end_time=base_date + timedelta(days=i, hours=i % 24, minutes=30),
                status=BackupStatus.SUCCESS if i % 10 != 0 else BackupStatus.FAILURE,
                backup_type="database" if i % 2 == 0 else "filesystem",
                source_system=f"system-{(i % 3) + 1}",
            )
            for i in range(30)
        ]
        
        # Create sample daily metrics
        daily_metrics = [
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
                success_count=5 if i % 10 != 0 else 4,
                failure_count=0 if i % 10 != 0 else 1,
                partial_count=0,
            )
            for i in range(7)
        ]
        
        # Create sample weekly metrics
        weekly_metrics = [
            WeeklyMetrics(
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 7),
                period_type=PeriodType.WEEK,
                backup_type="database",
                week_start=date(2024, 1, 1),
                week_end=date(2024, 1, 7),
                week_number=1,
                average_duration=1800.0,
                max_duration=3600.0,
                min_duration=900.0,
                total_duration=12600.0,
                total_count=35,
                success_count=34,
                failure_count=1,
                partial_count=0,
            )
        ]
        
        # Create sample monthly metrics
        monthly_metrics = [
            MonthlyMetrics(
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                period_type=PeriodType.MONTH,
                backup_type="database",
                year=2024,
                month=1,
                average_duration=1800.0,
                max_duration=3600.0,
                min_duration=900.0,
                total_duration=54000.0,
                total_count=150,
                success_count=145,
                failure_count=5,
                partial_count=0,
            )
        ]
        
        # Create sample anomalies
        anomalies = [
            AnomalyDetectionResult(
                has_anomaly=True,
                anomalies=[],
                metrics=daily_metrics[0],
                historical_average=1800.0,
                samples_used=7,
            )
        ]
        
        super().__init__(
            backup_records=backup_records,
            daily_metrics=daily_metrics,
            weekly_metrics=weekly_metrics,
            monthly_metrics=monthly_metrics,
            anomalies=anomalies,
        )


class MockUIAdapter(StandardUIAdapter):
    """Mock UI adapter for testing."""
    
    def __init__(self):
        """Initialize with mock data provider."""
        super().__init__(MockDataProvider())


class MockMonitoringAdapter(StandardMonitoringAdapter):
    """Mock monitoring adapter for testing."""
    
    def __init__(self):
        """Initialize with mock data provider."""
        super().__init__(MockDataProvider())
