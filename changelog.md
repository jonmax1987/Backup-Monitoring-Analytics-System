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

### Changed
- Added jsonschema and pytz to requirements.txt (CORE-002)
- Updated classification_rules.yaml with expanded rule examples (CORE-003)

### Fixed
- —

---

## Instructions for Cursor Agents
- Add entries under [Unreleased]
- Move to versioned section only after release

