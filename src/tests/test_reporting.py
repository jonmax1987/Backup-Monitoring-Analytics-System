"""Tests for report generator."""

import pytest
import json
import csv
from pathlib import Path
from datetime import date, datetime, timedelta
import pytz

from backup_monitoring.reporting.generator import ReportGenerator, ReportGenerationError
from backup_monitoring.processing.models import (
    DailyMetrics,
    WeeklyMetrics,
    MonthlyMetrics,
    PeriodType,
)
from backup_monitoring.processing.comparison import PeriodComparison, MetricDelta
from backup_monitoring.anomaly_detection.models import (
    AnomalyDetectionResult,
    Anomaly,
    AnomalyType,
    AnomalySeverity,
)


@pytest.fixture
def generator(tmp_path):
    """Create a ReportGenerator instance with temporary output directory."""
    # Override output directory for testing
    gen = ReportGenerator()
    gen.output_directory = tmp_path
    return gen


@pytest.fixture
def sample_daily_metrics():
    """Create sample daily metrics for testing."""
    base_date = date(2024, 1, 1)
    
    return [
        DailyMetrics(
            period_start=base_date + timedelta(days=i),
            period_end=base_date + timedelta(days=i),
            period_type=PeriodType.DAY,
            backup_type="database",
            period_date=base_date + timedelta(days=i),
            average_duration=1800.0,
            max_duration=3600.0,
            min_duration=900.0,
            total_duration=1800.0,
            total_count=5,
            success_count=5,
            failure_count=0,
            partial_count=0,
        )
        for i in range(3)
    ]


@pytest.fixture
def sample_anomalies(sample_daily_metrics):
    """Create sample anomaly detection results."""
    from backup_monitoring.anomaly_detection.models import AnomalyDetectionResult
    
    return [
        AnomalyDetectionResult(
            has_anomaly=True,
            anomalies=[
                Anomaly(
                    anomaly_type=AnomalyType.DURATION_HIGH,
                    severity=AnomalySeverity.HIGH,
                    metric_name="average_duration",
                    current_value=5000.0,
                    expected_value=1800.0,
                    threshold_value=3600.0,
                    deviation_percentage=177.78,
                    period_start=m.period_start,
                    period_end=m.period_end,
                    backup_type=m.backup_type,
                    period_type=m.period_type.value,
                )
            ],
            metrics=sample_daily_metrics[0],
            historical_average=1800.0,
            samples_used=7,
        )
    ]


def test_generate_daily_report_json(generator, sample_daily_metrics):
    """Test JSON daily report generation."""
    output_files = generator.generate_daily_report(sample_daily_metrics, formats=["json"])
    
    assert "json" in output_files
    assert output_files["json"].exists()
    
    # Validate JSON content
    with open(output_files["json"], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["report_type"] == "daily"
    assert "generated_at" in data
    assert len(data["metrics"]) == 3
    assert "summary" in data


def test_generate_daily_report_csv(generator, sample_daily_metrics):
    """Test CSV daily report generation."""
    output_files = generator.generate_daily_report(sample_daily_metrics, formats=["csv"])
    
    assert "csv" in output_files
    assert output_files["csv"].exists()
    
    # Validate CSV content
    with open(output_files["csv"], 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    assert len(rows) > 0
    assert "Report Type" in rows[0][0] or "Metrics" in str(rows)


def test_generate_daily_report_html(generator, sample_daily_metrics):
    """Test HTML daily report generation."""
    output_files = generator.generate_daily_report(sample_daily_metrics, formats=["html"])
    
    assert "html" in output_files
    assert output_files["html"].exists()
    
    # Validate HTML content
    with open(output_files["html"], 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "<html" in content
    assert "Backup Monitoring Report" in content
    assert "Metrics" in content


def test_generate_daily_report_all_formats(generator, sample_daily_metrics):
    """Test generating daily report in all formats."""
    output_files = generator.generate_daily_report(sample_daily_metrics)
    
    assert "json" in output_files
    assert "csv" in output_files
    assert "html" in output_files
    
    for filepath in output_files.values():
        assert filepath.exists()


def test_generate_daily_report_with_anomalies(generator, sample_daily_metrics, sample_anomalies):
    """Test daily report generation with anomalies."""
    output_files = generator.generate_daily_report(sample_daily_metrics, anomalies=sample_anomalies)
    
    # Check JSON for anomalies
    with open(output_files["json"], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert "anomalies" in data
    assert len(data["anomalies"]) == 1
    assert data["anomalies"][0]["has_anomaly"] is True


def test_generate_period_report_weekly(generator):
    """Test weekly period report generation."""
    metrics = [
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
            total_duration=18000.0,
            total_count=10,
            success_count=10,
            failure_count=0,
            partial_count=0,
        )
    ]
    
    output_files = generator.generate_period_report(metrics, "week", formats=["json"])
    
    assert "json" in output_files
    
    with open(output_files["json"], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["report_type"] == "week"
    assert len(data["metrics"]) == 1


def test_generate_period_report_monthly(generator):
    """Test monthly period report generation."""
    metrics = [
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
            total_count=30,
            success_count=30,
            failure_count=0,
            partial_count=0,
        )
    ]
    
    output_files = generator.generate_period_report(metrics, "month", formats=["json"])
    
    assert "json" in output_files
    
    with open(output_files["json"], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["report_type"] == "month"
    assert data["metrics"][0]["year"] == 2024
    assert data["metrics"][0]["month"] == 1


def test_generate_comparison_report(generator):
    """Test comparison report generation."""
    comparisons = [
        PeriodComparison(
            period_type=PeriodType.DAY,
            backup_type="database",
            current_period_start=date(2024, 1, 2),
            current_period_end=date(2024, 1, 2),
            previous_period_start=date(2024, 1, 1),
            previous_period_end=date(2024, 1, 1),
            current_metrics=DailyMetrics(
                period_start=date(2024, 1, 2),
                period_end=date(2024, 1, 2),
                period_type=PeriodType.DAY,
                backup_type="database",
                period_date=date(2024, 1, 2),
                average_duration=2000.0,
                max_duration=4000.0,
                min_duration=1000.0,
                total_duration=2000.0,
                total_count=5,
                success_count=5,
                failure_count=0,
                partial_count=0,
            ),
            previous_metrics=DailyMetrics(
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 1),
                period_type=PeriodType.DAY,
                backup_type="database",
                period_date=date(2024, 1, 1),
                average_duration=1800.0,
                max_duration=3600.0,
                min_duration=900.0,
                total_duration=1800.0,
                total_count=5,
                success_count=5,
                failure_count=0,
                partial_count=0,
            ),
            duration_deltas={
                "average_duration": MetricDelta(
                    metric_name="average_duration",
                    current_value=2000.0,
                    previous_value=1800.0,
                    absolute_delta=200.0,
                    percentage_delta=11.11,
                )
            },
            count_deltas={},
            rate_deltas={},
            has_previous_data=True,
        )
    ]
    
    output_files = generator.generate_comparison_report(comparisons, formats=["json"])
    
    assert "json" in output_files
    
    with open(output_files["json"], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["report_type"] == "comparison"
    assert len(data["comparisons"]) == 1
    assert "deltas" in data["comparisons"][0]


def test_report_summary_calculation(generator, sample_daily_metrics):
    """Test that summary is calculated correctly."""
    output_files = generator.generate_daily_report(sample_daily_metrics, formats=["json"])
    
    with open(output_files["json"], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summary = data["summary"]
    assert summary["total_periods"] == 3
    assert summary["total_backups"] == 15  # 5 * 3
    assert summary["total_success"] == 15
    assert summary["total_failure"] == 0
    assert "backup_types" in summary


def test_json_report_structure(generator, sample_daily_metrics):
    """Test JSON report structure and content."""
    output_files = generator.generate_daily_report(sample_daily_metrics, formats=["json"])
    
    with open(output_files["json"], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validate structure
    assert "report_type" in data
    assert "generated_at" in data
    assert "metrics" in data
    assert "summary" in data
    
    # Validate metric structure
    if data["metrics"]:
        metric = data["metrics"][0]
        assert "period_start" in metric
        assert "backup_type" in metric
        assert "average_duration" in metric
        assert "total_count" in metric


def test_csv_report_structure(generator, sample_daily_metrics):
    """Test CSV report structure."""
    output_files = generator.generate_daily_report(sample_daily_metrics, formats=["csv"])
    
    with open(output_files["csv"], 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Should contain report type and metrics
    assert "Report Type" in content or "Metrics" in content


def test_html_report_structure(generator, sample_daily_metrics):
    """Test HTML report structure."""
    output_files = generator.generate_daily_report(sample_daily_metrics, formats=["html"])
    
    with open(output_files["html"], 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Should contain HTML structure
    assert "<!DOCTYPE html>" in content
    assert "<html" in content
    assert "<head>" in content
    assert "<body>" in content
    assert "</html>" in content
    
    # Should contain report content
    assert "Backup Monitoring Report" in content
    assert "Summary" in content
    assert "Metrics" in content


def test_html_report_with_anomalies(generator, sample_daily_metrics, sample_anomalies):
    """Test HTML report includes anomalies section."""
    output_files = generator.generate_daily_report(
        sample_daily_metrics,
        anomalies=sample_anomalies,
        formats=["html"]
    )
    
    with open(output_files["html"], 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "Anomalies" in content


def test_empty_metrics_report(generator):
    """Test report generation with empty metrics."""
    output_files = generator.generate_daily_report([], formats=["json"])
    
    with open(output_files["json"], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["report_type"] == "daily"
    assert len(data["metrics"]) == 0
    assert data["summary"] == {}


def test_report_timestamp_formatting(generator, sample_daily_metrics):
    """Test that report filenames include timestamps."""
    output_files = generator.generate_daily_report(sample_daily_metrics, formats=["json"])
    
    filename = output_files["json"].name
    # Should contain timestamp pattern YYYYMMDD_HHMMSS
    assert "_" in filename
    parts = filename.split("_")
    assert len(parts) >= 3  # daily_report_TIMESTAMP.json


def test_multiple_backup_types_in_report(generator):
    """Test report with multiple backup types."""
    metrics = [
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
            total_count=5,
            success_count=5,
            failure_count=0,
            partial_count=0,
        ),
        DailyMetrics(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 1),
            period_type=PeriodType.DAY,
            backup_type="filesystem",
            period_date=date(2024, 1, 1),
            average_duration=1200.0,
            max_duration=2400.0,
            min_duration=600.0,
            total_duration=1200.0,
            total_count=3,
            success_count=3,
            failure_count=0,
            partial_count=0,
        ),
    ]
    
    output_files = generator.generate_daily_report(metrics, formats=["json"])
    
    with open(output_files["json"], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summary = data["summary"]
    assert len(summary["backup_types"]) == 2
    assert "database" in summary["backup_types"]
    assert "filesystem" in summary["backup_types"]
