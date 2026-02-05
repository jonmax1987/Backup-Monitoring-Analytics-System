# Changelog

All notable changes to this project will be documented here.

The format follows Keep a Changelog principles.

---

## [Unreleased]

### Added
- Initial project specification
- Phase 1 task list
- Project skeleton with modular directory structure (CORE-001)
- Configuration system with YAML-based config loader (CORE-001)
- Configuration validation using Pydantic models (CORE-001)
- Project setup files (pyproject.toml, setup.py, requirements.txt) (CORE-001)
- Test infrastructure with pytest (CORE-001)
- Validation script for setup verification (CORE-001)
- Configuration files (config.yaml, classification_rules.yaml, json_schema.json) (CORE-001)
- JSON Data Loader with schema validation (CORE-002)
- BackupRecord data model with Pydantic validation (CORE-002)
- Timestamp normalization supporting multiple formats (CORE-002)
- Comprehensive unit tests for JSON loader (CORE-002)
- Sample backup data file for testing (CORE-002)
- Backup Classification Layer with rule-based system (CORE-003)
- ClassificationRule and Condition models with multiple operators (CORE-003)
- RuleEvaluator for evaluating classification rules (CORE-003)
- Support for nested field access (dot notation) (CORE-003)
- Operators: equals, contains, starts_with, ends_with, regex, in, not_equals, not_contains (CORE-003)
- Case-sensitive and case-insensitive string matching (CORE-003)
- Batch classification support (CORE-003)
- Comprehensive unit tests for classifier (CORE-003)
- Enhanced classification_rules.yaml with more examples (CORE-003)
- Processing Engine for computing aggregates and metrics (CORE-004)
- AggregatedMetrics model with duration and count metrics (CORE-004)
- DailyMetrics, WeeklyMetrics, MonthlyMetrics models (CORE-004)
- Daily aggregation by date and backup type (CORE-004)
- Weekly aggregation with week start/end calculation (CORE-004)
- Monthly aggregation with proper month boundary handling (CORE-004)
- Duration calculations (average, min, max, total) (CORE-004)
- Status counting (success, failure, partial) with rate calculations (CORE-004)
- Support for filtering by specific date/week/month (CORE-004)
- compute_all_aggregates method for batch processing (CORE-004)
- Comprehensive unit tests for processing engine (CORE-004)
- Historical Comparison Module for period-to-period comparisons (CORE-005)
- PeriodComparison model with delta calculations (CORE-005)
- MetricDelta model for tracking changes in metrics (CORE-005)
- Daily comparison (day vs day) (CORE-005)
- Weekly comparison (week vs week) (CORE-005)
- Monthly comparison (month vs month) with year boundary handling (CORE-005)
- Absolute and percentage delta calculations (CORE-005)
- Support for comparing multiple consecutive periods (CORE-005)
- Handling of missing previous period data (CORE-005)
- Zero value handling in percentage calculations (CORE-005)
- Comprehensive unit tests for comparison module (CORE-005)
- Anomaly Detection Engine with rule-based threshold detection (CORE-006)
- Anomaly and AnomalyDetectionResult models (CORE-006)
- AnomalyType enum (duration_high/low, count_high/low, failure_rate_high, success_rate_low) (CORE-006)
- AnomalySeverity levels (low, medium, high, critical) (CORE-006)
- Duration anomaly detection (average and max duration) (CORE-006)
- Count anomaly detection (total count high/low) (CORE-006)
- Rate anomaly detection (failure rate high, success rate low) (CORE-006)
- Configurable threshold multiplier and minimum samples (CORE-006)
- Lookback period limiting for historical comparison (CORE-006)
- Severity calculation based on deviation percentage and standard deviation (CORE-006)
- Batch anomaly detection for multiple metrics (CORE-006)
- Filtering by backup type and period type (CORE-006)
- Comprehensive unit tests for anomaly detection (CORE-006)
- Report Generator with multi-format support (CORE-007)
- JSON report generation (machine-readable format) (CORE-007)
- CSV report generation (analysis-friendly format) (CORE-007)
- HTML report generation (human-readable, presentation-ready) (CORE-007)
- Daily report generation per backup type (CORE-007)
- Period-based report generation (week/month) (CORE-007)
- Historical comparison report generation (CORE-007)
- Report summary calculation with statistics (CORE-007)
- Support for including anomaly data in reports (CORE-007)
- Support for including comparison data in reports (CORE-007)
- Timestamped report filenames (CORE-007)
- Configurable output directory and formats (CORE-007)
- Comprehensive unit tests for report generator (CORE-007)
- Integration Layer with adapter interfaces (CORE-008)
- DataAdapter base interface for data access (CORE-008)
- UIAdapter interface for UI integration (CORE-008)
- MonitoringAdapter interface for Prometheus/Grafana integration (CORE-008)
- IntegrationDataProvider for managing processed data (CORE-008)
- StandardDataAdapter implementation with filtering (CORE-008)
- StandardUIAdapter with dashboard summary methods (CORE-008)
- StandardMonitoringAdapter with Prometheus format export (CORE-008)
- Mock adapters for testing (MockUIAdapter, MockMonitoringAdapter) (CORE-008)
- Support for filtering by date range, backup type, period type (CORE-008)
- Decoupled architecture - no coupling to core logic (CORE-008)
- Comprehensive unit tests for integration layer (CORE-008)

### Changed
- Added jsonschema and pytz to requirements.txt (CORE-002)
- Updated classification_rules.yaml with expanded rule examples (CORE-003)

### Fixed
- —

---

## Instructions for Cursor Agents
- Add entries under [Unreleased]
- Move to versioned section only after release

