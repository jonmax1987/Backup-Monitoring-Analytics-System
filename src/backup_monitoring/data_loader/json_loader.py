"""JSON data loader for backup metadata."""

import json
import jsonschema
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import pytz

from backup_monitoring.config.config_loader import get_config
from backup_monitoring.data_loader.models import BackupRecord, BackupStatus


class JSONLoadError(Exception):
    """Exception raised when JSON loading fails."""
    pass


class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass


class TimestampNormalizationError(Exception):
    """Exception raised when timestamp normalization fails."""
    pass


class JSONDataLoader:
    """Loads and validates backup metadata from JSON files."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the JSON data loader.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = get_config(config_path)
        self.schema_path = Path(self.config.data_loader.json_schema_path)
        self.default_timezone = pytz.timezone(self.config.data_loader.default_timezone)
        self.date_format = self.config.data_loader.date_format
        self._schema: Optional[Dict[str, Any]] = None
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema from file."""
        if self._schema is None:
            schema_path = Path(self.schema_path)
            
            # If path is relative, try relative to project root
            if not schema_path.is_absolute():
                project_root = self._find_project_root()
                full_schema_path = project_root / schema_path
                if full_schema_path.exists():
                    schema_path = full_schema_path
                elif not schema_path.exists():
                    raise FileNotFoundError(f"JSON schema not found: {self.schema_path}")
            
            if not schema_path.exists():
                raise FileNotFoundError(f"JSON schema not found: {schema_path}")
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                self._schema = json.load(f)
        
        return self._schema
    
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        # Start from the directory containing this file
        current = Path(__file__).resolve().parent
        # Go up to find project root (look for pyproject.toml or README.md)
        while current.parent != current:
            if (current / "pyproject.toml").exists() or (current / "README.md").exists():
                return current
            current = current.parent
        # Fallback to current directory
        return Path.cwd()
    
    def _normalize_timestamp(self, timestamp_str: str) -> datetime:
        """
        Normalize timestamp string to datetime object.
        
        Args:
            timestamp_str: Timestamp string in various formats
            
        Returns:
            datetime: Normalized datetime object
            
        Raises:
            TimestampNormalizationError: If timestamp cannot be parsed
        """
        # Try ISO format first (most common)
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            # If timezone-naive, assume UTC
            if dt.tzinfo is None:
                dt = self.default_timezone.localize(dt)
            return dt
        except ValueError:
            pass
        
        # Try custom format from config
        try:
            dt = datetime.strptime(timestamp_str, self.date_format)
            # Assume UTC if timezone-naive
            if dt.tzinfo is None:
                dt = self.default_timezone.localize(dt)
            return dt
        except ValueError:
            pass
        
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S.%f",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                if dt.tzinfo is None:
                    dt = self.default_timezone.localize(dt)
                return dt
            except ValueError:
                continue
        
        raise TimestampNormalizationError(
            f"Unable to parse timestamp: {timestamp_str}"
        )
    
    def _normalize_record(self, raw_record: Dict[str, Any]) -> BackupRecord:
        """
        Normalize a raw backup record to BackupRecord model.
        
        Args:
            raw_record: Raw backup record dictionary
            
        Returns:
            BackupRecord: Normalized backup record
            
        Raises:
            TimestampNormalizationError: If timestamps cannot be normalized
            ValueError: If record data is invalid
        """
        # Normalize timestamps
        start_time = self._normalize_timestamp(raw_record['start_time'])
        end_time = self._normalize_timestamp(raw_record['end_time'])
        
        # Normalize status
        status_str = raw_record['status'].lower()
        try:
            status = BackupStatus(status_str)
        except ValueError:
            raise ValueError(f"Invalid status value: {raw_record['status']}")
        
        # Build normalized record
        normalized = BackupRecord(
            backup_id=str(raw_record['backup_id']),
            start_time=start_time,
            end_time=end_time,
            status=status,
            backup_type=raw_record.get('backup_type'),
            source_system=raw_record.get('source_system'),
            metadata=raw_record.get('metadata', {})
        )
        
        return normalized
    
    def validate_schema(self, data: List[Dict[str, Any]]) -> None:
        """
        Validate data against JSON schema.
        
        Args:
            data: List of backup records to validate
            
        Raises:
            SchemaValidationError: If validation fails
        """
        schema = self._load_schema()
        
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            raise SchemaValidationError(f"Schema validation failed: {e.message}") from e
        except jsonschema.SchemaError as e:
            raise SchemaValidationError(f"Invalid schema: {e.message}") from e
    
    def load_from_file(self, file_path: str) -> List[BackupRecord]:
        """
        Load backup records from a JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List[BackupRecord]: List of normalized backup records
            
        Raises:
            JSONLoadError: If file cannot be read or parsed
            SchemaValidationError: If data doesn't match schema
            TimestampNormalizationError: If timestamps cannot be normalized
        """
        path = Path(file_path)
        
        if not path.exists():
            raise JSONLoadError(f"File not found: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise JSONLoadError(f"Invalid JSON in file {file_path}: {e}") from e
        except Exception as e:
            raise JSONLoadError(f"Error reading file {file_path}: {e}") from e
        
        # Validate schema
        try:
            self.validate_schema(data)
        except SchemaValidationError as e:
            raise SchemaValidationError(f"Schema validation failed for {file_path}: {e}") from e
        
        # Normalize records
        normalized_records = []
        errors = []
        
        for idx, raw_record in enumerate(data):
            try:
                normalized = self._normalize_record(raw_record)
                normalized_records.append(normalized)
            except Exception as e:
                errors.append(f"Record {idx} (backup_id: {raw_record.get('backup_id', 'unknown')}): {e}")
        
        if errors:
            error_msg = f"Failed to normalize {len(errors)} record(s):\n" + "\n".join(errors)
            raise JSONLoadError(error_msg)
        
        return normalized_records
    
    def load_from_string(self, json_string: str) -> List[BackupRecord]:
        """
        Load backup records from a JSON string.
        
        Args:
            json_string: JSON string containing backup records
            
        Returns:
            List[BackupRecord]: List of normalized backup records
            
        Raises:
            JSONLoadError: If string cannot be parsed
            SchemaValidationError: If data doesn't match schema
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise JSONLoadError(f"Invalid JSON string: {e}") from e
        
        # Validate schema
        try:
            self.validate_schema(data)
        except SchemaValidationError as e:
            raise SchemaValidationError(f"Schema validation failed: {e}") from e
        
        # Normalize records
        normalized_records = []
        errors = []
        
        for idx, raw_record in enumerate(data):
            try:
                normalized = self._normalize_record(raw_record)
                normalized_records.append(normalized)
            except Exception as e:
                errors.append(f"Record {idx} (backup_id: {raw_record.get('backup_id', 'unknown')}): {e}")
        
        if errors:
            error_msg = f"Failed to normalize {len(errors)} record(s):\n" + "\n".join(errors)
            raise JSONLoadError(error_msg)
        
        return normalized_records
