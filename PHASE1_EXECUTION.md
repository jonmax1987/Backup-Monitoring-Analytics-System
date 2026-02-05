# Phase 1 Execution Guide

This document provides instructions for running Phase 1 of the Backup Monitoring & Analytics System.

## Prerequisites

1. **Python 3.9+** installed and available in PATH
2. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install the package in development mode:
   ```bash
   pip install -e .
   ```

## Data Files

Place your backup metadata JSON files in the `data/` directory. The script will automatically load all `.json` files from this directory.

### Sample Data

A sample file (`sample_backup_data.json`) has been provided in the `data/` directory for testing.

## Running Phase 1

### Option 1: Using Python directly

From the project root directory:

```bash
python run_phase1.py
```

### Option 2: Using the batch file (Windows)

Double-click `run_phase1.bat` or run from command prompt:

```cmd
run_phase1.bat
```

### Option 3: Manual execution

If you encounter path issues, you can run it with explicit PYTHONPATH:

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="$PWD\src"
python run_phase1.py
```

**Windows (CMD):**
```cmd
set PYTHONPATH=%CD%\src
python run_phase1.py
```

**Linux/Mac:**
```bash
export PYTHONPATH="$PWD/src"
python run_phase1.py
```

## What Phase 1 Does

The script executes the following 6 steps:

1. **Load Data**: Loads all JSON files from `data/` directory
2. **Classify Backups**: Classifies backup records by type
3. **Compute Aggregates**: Calculates daily, weekly, and monthly metrics
4. **Historical Comparison**: Compares periods to identify trends
5. **Detect Anomalies**: Identifies anomalies in backup patterns
6. **Generate Reports**: Creates JSON, CSV, and HTML reports

## Output

All output files are saved to `reporting/output/` directory:

- **Daily reports**: `daily_report.json`, `daily_report.csv`, `daily_report.html`
- **Weekly reports**: `weekly_report.json`, `weekly_report.csv`, `weekly_report.html`
- **Monthly reports**: `monthly_report.json`, `monthly_report.csv`, `monthly_report.html`

## Troubleshooting

### Import Errors

If you get import errors, ensure:
1. The `src/` directory is in your PYTHONPATH
2. All dependencies are installed (`pip install -r requirements.txt`)
3. You're running from the project root directory

### No Data Files Found

If you see "No JSON files found in data/ directory":
1. Ensure JSON files exist in the `data/` directory
2. Check file permissions
3. Verify file extensions are `.json` (lowercase)

### Schema Validation Errors

If you get schema validation errors:
1. Check that your JSON files match the schema in `config/json_schema.json`
2. Ensure required fields are present: `backup_id`, `start_time`, `end_time`, `status`
3. Verify timestamps are in ISO 8601 format

### Configuration Errors

If you get configuration errors:
1. Verify `config/config.yaml` exists and is valid
2. Check that `config/json_schema.json` exists
3. Ensure all required configuration paths are correct

## Testing

Before running Phase 1, you can verify the setup by running tests:

```bash
pytest
```

Or run specific test modules:

```bash
pytest tests/test_json_loader.py
pytest tests/test_classifier.py
pytest tests/test_processing.py
pytest tests/test_comparison.py
pytest tests/test_anomaly_detection.py
pytest tests/test_reporting.py
```

## Next Steps

After Phase 1 completes successfully:

1. Review the generated reports in `reporting/output/`
2. Check for any anomalies detected
3. Verify data accuracy
4. Proceed to Phase 2 (if applicable)

## Support

For issues or questions:
1. Check the error messages - they include detailed information
2. Review the traceback output for debugging
3. Verify all prerequisites are met
4. Check the project documentation in `README.md`
