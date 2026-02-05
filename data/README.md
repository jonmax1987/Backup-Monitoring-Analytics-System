# Data Directory

This directory is for storing input JSON backup metadata files.

## Usage

Place your backup metadata JSON files in this directory. The JSON Data Loader can read files from any location, but this directory provides a convenient standard location.

## File Format

Files should follow the JSON schema defined in `config/json_schema.json`. Each file should contain an array of backup records with the following required fields:

- `backup_id` (string): Unique identifier
- `start_time` (string): ISO 8601 timestamp
- `end_time` (string): ISO 8601 timestamp  
- `status` (string): "success", "failure", or "partial"

Optional fields:
- `backup_type` (string): Will be classified if missing
- `source_system` (string): Source system identifier
- `metadata` (object): Additional metadata

## Example

See `examples/sample_backup_data.json` for a sample file format.

## Loading Data

You can load data from any file path using the JSONDataLoader:

```python
from backup_monitoring.data_loader import JSONDataLoader

loader = JSONDataLoader()
records = loader.load_from_file("data/your_backup_file.json")
```
