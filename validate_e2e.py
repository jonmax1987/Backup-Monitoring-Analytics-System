#!/usr/bin/env python3
"""
CORE-010 End-to-End Validation Script.

Validates full system flow: load sample JSON -> classify -> process ->
compare -> detect anomalies -> generate reports -> Integration Layer output.
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Sample backup data for validation
SAMPLE_JSON = """
[
  {
    "backup_id": "e2e-001",
    "start_time": "2024-01-01T10:00:00Z",
    "end_time": "2024-01-01T10:30:00Z",
    "status": "success",
    "source_system": "database-primary"
  },
  {
    "backup_id": "e2e-002",
    "start_time": "2024-01-01T14:00:00Z",
    "end_time": "2024-01-01T14:45:00Z",
    "status": "success",
    "source_system": "filesystem-storage"
  },
  {
    "backup_id": "e2e-003",
    "start_time": "2024-01-01T18:00:00Z",
    "end_time": "2024-01-01T18:10:00Z",
    "status": "failure",
    "source_system": "database-secondary"
  }
]
"""


def main():
    """Run end-to-end validation."""
    print("=" * 60)
    print("CORE-010 End-to-End Validation")
    print("=" * 60)

    try:
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
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 1

    try:
        # 1. Load
        print("\n[1/7] Loading JSON...")
        loader = JSONDataLoader()
        records = loader.load_from_string(SAMPLE_JSON)
        print(f"  ✓ Loaded {len(records)} records")

        # 2. Classify
        print("\n[2/7] Classifying...")
        classifier = BackupClassifier()
        classified = classifier.classify_batch(records)
        print(f"  ✓ Classified {len(classified)} records")

        # 3. Process
        print("\n[3/7] Computing aggregates...")
        engine = ProcessingEngine()
        daily = engine.compute_daily_aggregates(classified)
        weekly = engine.compute_weekly_aggregates(classified)
        monthly = engine.compute_monthly_aggregates(classified)
        print(f"  ✓ Daily: {len(daily)}, Weekly: {len(weekly)}, Monthly: {len(monthly)}")

        # 4. Compare
        print("\n[4/7] Historical comparison...")
        comparator = HistoricalComparator()
        comparisons = comparator.compare_multiple_periods(daily)
        print(f"  ✓ Comparisons: {len(comparisons)}")

        # 5. Anomaly detection
        print("\n[5/7] Anomaly detection...")
        detector = AnomalyDetector()
        anomalies = detector.detect_batch(daily)
        print(f"  ✓ Anomaly results: {len(anomalies)}")

        # 6. Reports
        print("\n[6/7] Generating reports...")
        out_dir = project_root / "reports" / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        reporter = ReportGenerator()
        reporter.output_directory = out_dir
        daily_files = reporter.generate_daily_report(daily, anomalies)
        for fmt, path in daily_files.items():
            print(f"  ✓ {fmt}: {path.name}")
        assert daily_files["json"].exists()
        with open(daily_files["json"], "r", encoding="utf-8") as f:
            report_data = json.load(f)
        assert report_data["report_type"] == "daily"
        assert "metrics" in report_data

        # 7. Integration Layer (dashboard output)
        print("\n[7/7] Integration Layer (dashboard output)...")
        provider = IntegrationDataProvider(
            backup_records=classified,
            daily_metrics=daily,
            weekly_metrics=weekly,
            monthly_metrics=monthly,
            comparisons=comparisons,
            anomalies=anomalies,
        )
        ui_adapter = StandardUIAdapter(provider)
        summary = ui_adapter.get_dashboard_summary()
        assert "total_backups" in summary
        assert "success_rate" in summary
        print(f"  ✓ Dashboard summary: {summary['total_backups']} backups, {summary['success_rate']:.1f}% success")

    except Exception as e:
        print(f"\n❌ E2E validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 60)
    print("✅ End-to-end validation passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
