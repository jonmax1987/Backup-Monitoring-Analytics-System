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

### Changed
- Added jsonschema and pytz to requirements.txt (CORE-002)
- Updated classification_rules.yaml with expanded rule examples (CORE-003)

### Fixed
- —

---

## Instructions for Cursor Agents
- Add entries under [Unreleased]
- Move to versioned section only after release

