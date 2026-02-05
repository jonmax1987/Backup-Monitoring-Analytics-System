# Backup Monitoring & Analytics System

A modular system for monitoring, analyzing, and reporting on backup operations.

## Overview

This system ingests backup metadata from JSON sources, classifies backup types, computes durations and aggregates, detects anomalies, and generates reports and dashboards.

## Architecture

The system follows a modular architecture with clear separation of concerns:

- **Data Loader**: Reads and validates JSON backup metadata
- **Backup Classifier**: Classifies backup types
- **Processing Engine**: Computes durations, aggregates, and period averages
- **Anomaly Detection**: Rule-based anomaly detection
- **Report Generator**: Generates reports in JSON, CSV, and HTML formats
- **Integration Layer**: Decouples core logic from UI and monitoring systems

## Project Structure

```
backup_monitoring/
├── src/
│   ├── backup_monitoring/
│   │   ├── __init__.py
│   │   ├── config/
│   │   ├── data_loader/
│   │   ├── classifier/
│   │   ├── processing/
│   │   ├── anomaly_detection/
│   │   ├── reporting/
│   │   └── integration/
│   └── tests/
├── config/
├── docs/
└── ui/
```

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Configure: Edit `config/config.yaml`
3. Run tests: `pytest`
4. Run the system: `python -m backup_monitoring`

## Documentation

- [Formal Specification](backup_monitoring_system_אפיון_פורמלי.md)
- [Status](status.md)
- [Architectural Decisions](decisions.md)
- [Changelog](changelog.md)
