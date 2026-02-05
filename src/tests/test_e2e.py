"""End-to-end tests for full system flow."""

import pytest
import json
import tempfile
from pathlib import Path
import sys

# Ensure src is on path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from backup_monitoring.data_loader import JSONDataLoader
from backup_monitoring.classifier import BackupClassifier
from backup_monitoring.processing import ProcessingEngine, HistoricalComparator
from backup_monitoring.anomaly_detection import AnomalyDetector
from backup_monitoring.reporting import ReportGenerator
from backup_monitoring.integration import (
    IntegrationDataProvider,
    StandardUIAdapter,
    StandardMonitoringAdapter,
)


# Sample JSON backup data for E2E tests
SAMPLE_BACKUP_JSON = """
[
  {
    "backup_id": "e2e-backup-001",
    "start_time": "2024-01-01T10:00:00Z",
    "end_time": "2024-01-01T10:30:00Z",
    "status": "success",
    "source_system": "database-primary",
    "metadata": {}
  },
  {
    "backup_id": "e2e-backup-002",
    "start_time": "2024-01-01T14:00:00Z",
    "end_time": "2024-01-01T14:45:00Z",
    "status": "success",
    "source_system": "filesystem-storage",
    "metadata": {}
  },
  {
    "backup_id": "e2e-backup-003",
    "start_time": "2024-01-01T18:00:00Z",
    "end_time": "2024-01-01T18:10:00Z",
    "status": "failure",
    "source_system": "database-secondary",
    "metadata": {}
  },
  {
    "backup_id": "e2e-backup-004",
    "start_time": "2024-01-02T10:00:00Z",
    "end_time": "2024-01-02T10:25:00Z",
    "status": "success",
    "source_system": "database-primary",
    "metadata": {}
  },
  {
    "backup_id": "e2e-backup-005",
    "start_time": "2024-01-02T14:00:00Z",
    "end_time": "2024-01-02T14:30:00Z",
    "status": "success",
    "source_system": "database-primary",
    "metadata": {}
  }
]
"""


@pytest.fixture
def sample_json_file(tmp_path):
    """Create a temporary JSON file with sample backup data."""
    json_path = tmp_path / "sample_backups.json"
    json_path.write_text(SAMPLE_BACKUP_JSON, encoding="utf-8")
    return str(json_path)


@pytest.fixture
def output_dir(tmp_path):
    """Temporary directory for report output."""
    return tmp_path


def test_e2e_full_pipeline(sample_json_file, output_dir):
    """End-to-end: Load JSON -> Classify -> Process -> Compare -> Detect -> Report."""
    # 1. Load data
    loader = JSONDataLoader()
    records = loader.load_from_file(sample_json_file)
    assert len(records) == 5

    # 2. Classify
    classifier = BackupClassifier()
    classified = classifier.classify_batch(records)
    assert len(classified) == 5
    backup_types = {r.backup_type for r in classified}
    assert "database" in backup_types or "filesystem" in backup_types or "unknown" in backup_types

    # 3. Compute aggregates
    engine = ProcessingEngine()
    daily_metrics = engine.compute_daily_aggregates(classified)
    weekly_metrics = engine.compute_weekly_aggregates(classified)
    monthly_metrics = engine.compute_monthly_aggregates(classified)
    assert len(daily_metrics) >= 1
    assert len(weekly_metrics) >= 1
    assert len(monthly_metrics) >= 1

    # 4. Historical comparison
    comparator = HistoricalComparator()
    daily_comparisons = comparator.compare_multiple_periods(daily_metrics)
    assert isinstance(daily_comparisons, list)

    # 5. Anomaly detection
    detector = AnomalyDetector()
    daily_anomalies = detector.detect_batch(daily_metrics)
    assert len(daily_anomalies) == len(daily_metrics)

    # 6. Generate reports
    reporter = ReportGenerator()
    reporter.output_directory = output_dir
    daily_files = reporter.generate_daily_report(daily_metrics, daily_anomalies)
    assert "json" in daily_files
    assert "csv" in daily_files
    assert "html" in daily_files
    assert daily_files["json"].exists()
    assert daily_files["csv"].exists()
    assert daily_files["html"].exists()

    # Validate report content
    with open(daily_files["json"], "r", encoding="utf-8") as f:
        report_data = json.load(f)
    assert report_data["report_type"] == "daily"
    assert "metrics" in report_data
    assert "summary" in report_data
    assert len(report_data["metrics"]) >= 1


def test_e2e_integration_layer_output(sample_json_file, output_dir):
    """End-to-end: Full pipeline and validate Integration Layer produces dashboard-ready data."""
    loader = JSONDataLoader()
    records = loader.load_from_file(sample_json_file)
    classifier = BackupClassifier()
    classified = classifier.classify_batch(records)
    engine = ProcessingEngine()
    daily_metrics = engine.compute_daily_aggregates(classified)
    weekly_metrics = engine.compute_weekly_aggregates(classified)
    monthly_metrics = engine.compute_monthly_aggregates(classified)
    comparator = HistoricalComparator()
    daily_comparisons = comparator.compare_multiple_periods(daily_metrics)
    detector = AnomalyDetector()
    daily_anomalies = detector.detect_batch(daily_metrics)

    # Populate Integration Layer
    provider = IntegrationDataProvider(
        backup_records=classified,
        daily_metrics=daily_metrics,
        weekly_metrics=weekly_metrics,
        monthly_metrics=monthly_metrics,
        comparisons=daily_comparisons,
        anomalies=daily_anomalies,
    )
    ui_adapter = StandardUIAdapter(provider)
    monitoring_adapter = StandardMonitoringAdapter(provider)

    # Dashboard summary (UI consumes only via adapter)
    summary = ui_adapter.get_dashboard_summary()
    assert "total_backups" in summary
    assert "success_rate" in summary
    assert "backup_types" in summary
    assert "date_range" in summary
    assert summary["total_backups"] >= 5

    # Metrics for dashboard
    metrics = ui_adapter.get_daily_metrics()
    assert len(metrics) >= 1

    # Monitoring export (Prometheus-style)
    prometheus_output = monitoring_adapter.export_prometheus_format()
    assert "backup_total" in prometheus_output or "backup_success" in prometheus_output


def test_e2e_report_formats_valid(sample_json_file, output_dir):
    """End-to-end: Validate all report formats (JSON, CSV, HTML) are valid."""
    loader = JSONDataLoader()
    records = loader.load_from_file(sample_json_file)
    classified = BackupClassifier().classify_batch(records)
    daily_metrics = ProcessingEngine().compute_daily_aggregates(classified)
    daily_anomalies = AnomalyDetector().detect_batch(daily_metrics)

    reporter = ReportGenerator()
    reporter.output_directory = output_dir
    daily_files = reporter.generate_daily_report(daily_metrics, daily_anomalies)

    # JSON: valid and parseable
    with open(daily_files["json"], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "report_type" in data
    assert "generated_at" in data

    # CSV: has content and header-like structure
    csv_content = daily_files["csv"].read_text(encoding="utf-8")
    assert "Report Type" in csv_content or "Metrics" in csv_content
    assert len(csv_content) > 50

    # HTML: has structure
    html_content = daily_files["html"].read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html_content
    assert "Backup Monitoring" in html_content


def test_e2e_deterministic_output(sample_json_file, output_dir):
    """End-to-end: Same input produces same report structure (deterministic)."""
    loader = JSONDataLoader()
    records1 = loader.load_from_file(sample_json_file)
    records2 = loader.load_from_file(sample_json_file)
    assert len(records1) == len(records2)

    def run_pipeline(recs):
        classified = BackupClassifier().classify_batch(recs)
        daily = ProcessingEngine().compute_daily_aggregates(classified)
        return len(daily), sum(m.total_count for m in daily)

    count1, total1 = run_pipeline(records1)
    count2, total2 = run_pipeline(records2)
    assert count1 == count2
    assert total1 == total2
