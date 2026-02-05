"""
Phase 1 Execution Script
Runs the full backup monitoring pipeline: load, classify, process, compare, detect, and report.
"""

import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from backup_monitoring.data_loader import JSONDataLoader
from backup_monitoring.classifier import BackupClassifier
from backup_monitoring.processing import ProcessingEngine, HistoricalComparator
from backup_monitoring.anomaly_detection import AnomalyDetector
from backup_monitoring.reporting import ReportGenerator
import glob
import os
from pathlib import Path


def main():
    """Execute Phase 1: Full pipeline execution."""
    print("=" * 80)
    print("Backup Monitoring & Analytics System - Phase 1 Execution")
    print("=" * 80)
    
    # Ensure output directory exists
    output_dir = Path("reporting/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n✓ Output directory ready: {output_dir}")
    
    # 1. Load all JSON files from data/
    print("\n[1/6] Loading data files...")
    data_files = glob.glob(os.path.join("data", "*.json"))
    if not data_files:
        print("⚠ Warning: No JSON files found in data/ directory")
        print("  Please add backup data JSON files to the data/ directory")
        return
    
    print(f"  Found {len(data_files)} JSON file(s)")
    loader = JSONDataLoader()
    all_records = []
    for f in data_files:
        print(f"  Loading: {f}")
        try:
            records = loader.load_from_file(f)
            all_records.extend(records)
            print(f"    ✓ Loaded {len(records)} records")
        except Exception as e:
            print(f"    ✗ Error loading {f}: {e}")
            continue
    
    if not all_records:
        print("✗ Error: No records loaded. Cannot proceed.")
        return
    
    print(f"\n✓ Total records loaded: {len(all_records)}")
    
    # 2. Classify backups
    print("\n[2/6] Classifying backups...")
    classifier = BackupClassifier()
    try:
        all_records = classifier.classify_batch(all_records)
        print(f"✓ Classified {len(all_records)} records")
    except Exception as e:
        print(f"✗ Error during classification: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Compute aggregates
    print("\n[3/6] Computing aggregates...")
    engine = ProcessingEngine()
    try:
        daily_metrics = engine.compute_daily_aggregates(all_records)
        print(f"  ✓ Daily metrics: {len(daily_metrics)} periods")
        
        weekly_metrics = engine.compute_weekly_aggregates(all_records)
        print(f"  ✓ Weekly metrics: {len(weekly_metrics)} periods")
        
        monthly_metrics = engine.compute_monthly_aggregates(all_records)
        print(f"  ✓ Monthly metrics: {len(monthly_metrics)} periods")
    except Exception as e:
        print(f"✗ Error during aggregation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Historical comparison
    print("\n[4/6] Performing historical comparison...")
    comparator = HistoricalComparator()
    try:
        daily_comparison = comparator.compare_multiple_periods(daily_metrics)
        print(f"  ✓ Daily comparisons: {len(daily_comparison)} periods")
        
        weekly_comparison = comparator.compare_multiple_periods(weekly_metrics)
        print(f"  ✓ Weekly comparisons: {len(weekly_comparison)} periods")
        
        monthly_comparison = comparator.compare_multiple_periods(monthly_metrics)
        print(f"  ✓ Monthly comparisons: {len(monthly_comparison)} periods")
    except Exception as e:
        print(f"✗ Error during comparison: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. Detect anomalies
    print("\n[5/6] Detecting anomalies...")
    detector = AnomalyDetector()
    try:
        daily_anomalies = detector.detect_batch(daily_metrics)
        print(f"  ✓ Daily anomalies detected: {len(daily_anomalies)}")
        
        weekly_anomalies = detector.detect_batch(weekly_metrics)
        print(f"  ✓ Weekly anomalies detected: {len(weekly_anomalies)}")
        
        monthly_anomalies = detector.detect_batch(monthly_metrics)
        print(f"  ✓ Monthly anomalies detected: {len(monthly_anomalies)}")
    except Exception as e:
        print(f"✗ Error during anomaly detection: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. Generate reports
    print("\n[6/6] Generating reports...")
    reporter = ReportGenerator()
    try:
        daily_files = reporter.generate_daily_report(daily_metrics, daily_anomalies)
        print(f"  ✓ Daily reports generated: {list(daily_files.keys())}")
        
        weekly_files = reporter.generate_period_report(weekly_metrics, "weekly", weekly_comparison, weekly_anomalies)
        print(f"  ✓ Weekly reports generated: {list(weekly_files.keys())}")
        
        monthly_files = reporter.generate_period_report(monthly_metrics, "monthly", monthly_comparison, monthly_anomalies)
        print(f"  ✓ Monthly reports generated: {list(monthly_files.keys())}")
    except Exception as e:
        print(f"✗ Error during report generation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("Phase 1 Execution Complete!")
    print("=" * 80)
    print(f"\nOutput files are available in: {output_dir.absolute()}")
    print("\nGenerated files:")
    for file_path in sorted(output_dir.glob("**/*")):
        if file_path.is_file():
            print(f"  - {file_path.relative_to(output_dir)}")


if __name__ == "__main__":
    main()
