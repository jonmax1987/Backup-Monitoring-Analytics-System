"""Tests for JSON data loader."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
import pytz

from backup_monitoring.data_loader.json_loader import (
    JSONDataLoader,
    JSONLoadError,
    SchemaValidationError,
    TimestampNormalizationError,
)
from backup_monitoring.data_loader.models import BackupRecord, BackupStatus


@pytest.fixture
def sample_backup_data():
    """Sample valid backup data."""
    return [
        {
            "backup_id": "backup-001",
            "start_time": "2024-01-01T10:00:00Z",
            "end_time": "2024-01-01T10:30:00Z",
            "status": "success",
            "source_system": "database-01",
            "backup_type": "database",
            "metadata": {"size": "10GB", "compression": "gzip"}
        },
        {
            "backup_id": "backup-002",
            "start_time": "2024-01-01T11:00:00Z",
            "end_time": "2024-01-01T11:15:00Z",
            "status": "success",
            "source_system": "filesystem-01"
        }
    ]


@pytest.fixture
def temp_json_file(sample_backup_data):
    """Create a temporary JSON file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_backup_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def loader():
    """Create a JSONDataLoader instance."""
    return JSONDataLoader()


def test_load_valid_json_file(loader, temp_json_file, sample_backup_data):
    """Test loading a valid JSON file."""
    records = loader.load_from_file(temp_json_file)
    
    assert len(records) == 2
    assert isinstance(records[0], BackupRecord)
    assert records[0].backup_id == "backup-001"
    assert records[0].status == BackupStatus.SUCCESS
    assert records[0].source_system == "database-01"
    assert records[0].backup_type == "database"
    assert records[0].duration == 1800.0  # 30 minutes in seconds


def test_load_from_string(loader, sample_backup_data):
    """Test loading from JSON string."""
    json_string = json.dumps(sample_backup_data)
    records = loader.load_from_string(json_string)
    
    assert len(records) == 2
    assert isinstance(records[0], BackupRecord)


def test_timestamp_normalization_iso_format(loader):
    """Test timestamp normalization with ISO format."""
    data = [{
        "backup_id": "test-001",
        "start_time": "2024-01-01T10:00:00Z",
        "end_time": "2024-01-01T10:30:00Z",
        "status": "success"
    }]
    
    records = loader.load_from_string(json.dumps(data))
    assert records[0].start_time.tzinfo is not None
    assert records[0].end_time.tzinfo is not None


def test_timestamp_normalization_without_timezone(loader):
    """Test timestamp normalization without timezone (assumes UTC)."""
    data = [{
        "backup_id": "test-001",
        "start_time": "2024-01-01T10:00:00",
        "end_time": "2024-01-01T10:30:00",
        "status": "success"
    }]
    
    records = loader.load_from_string(json.dumps(data))
    assert records[0].start_time.tzinfo is not None
    assert records[0].start_time.tzinfo == pytz.UTC


def test_timestamp_normalization_custom_format(loader):
    """Test timestamp normalization with custom format."""
    data = [{
        "backup_id": "test-001",
        "start_time": "2024-01-01 10:00:00",
        "end_time": "2024-01-01 10:30:00",
        "status": "success"
    }]
    
    records = loader.load_from_string(json.dumps(data))
    assert records[0].start_time.year == 2024
    assert records[0].start_time.hour == 10


def test_invalid_timestamp(loader):
    """Test handling of invalid timestamp format."""
    data = [{
        "backup_id": "test-001",
        "start_time": "invalid-timestamp",
        "end_time": "2024-01-01T10:30:00Z",
        "status": "success"
    }]
    
    with pytest.raises(TimestampNormalizationError):
        loader.load_from_string(json.dumps(data))


def test_schema_validation_missing_required_field(loader):
    """Test schema validation catches missing required fields."""
    invalid_data = [{
        "backup_id": "test-001",
        # Missing start_time, end_time, status
    }]
    
    with pytest.raises(SchemaValidationError):
        loader.load_from_string(json.dumps(invalid_data))


def test_schema_validation_invalid_status(loader):
    """Test schema validation catches invalid status values."""
    invalid_data = [{
        "backup_id": "test-001",
        "start_time": "2024-01-01T10:00:00Z",
        "end_time": "2024-01-01T10:30:00Z",
        "status": "invalid_status"
    }]
    
    # Schema validation should pass, but normalization should fail
    with pytest.raises(JSONLoadError):
        loader.load_from_string(json.dumps(invalid_data))


def test_end_time_before_start_time(loader):
    """Test validation that end_time must be after start_time."""
    invalid_data = [{
        "backup_id": "test-001",
        "start_time": "2024-01-01T10:30:00Z",
        "end_time": "2024-01-01T10:00:00Z",  # Before start_time
        "status": "success"
    }]
    
    with pytest.raises(JSONLoadError):
        loader.load_from_string(json.dumps(invalid_data))


def test_missing_file(loader):
    """Test error handling for missing file."""
    with pytest.raises(JSONLoadError) as exc_info:
        loader.load_from_file("/nonexistent/file.json")
    
    assert "not found" in str(exc_info.value).lower()


def test_invalid_json_file(loader):
    """Test error handling for invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content {")
        temp_path = f.name
    
    try:
        with pytest.raises(JSONLoadError):
            loader.load_from_file(temp_path)
    finally:
        Path(temp_path).unlink()


def test_optional_fields(loader):
    """Test that optional fields are handled correctly."""
    minimal_data = [{
        "backup_id": "test-001",
        "start_time": "2024-01-01T10:00:00Z",
        "end_time": "2024-01-01T10:30:00Z",
        "status": "success"
    }]
    
    records = loader.load_from_string(json.dumps(minimal_data))
    assert records[0].backup_type is None
    assert records[0].source_system is None
    assert records[0].metadata == {}


def test_metadata_preservation(loader):
    """Test that metadata is preserved."""
    data = [{
        "backup_id": "test-001",
        "start_time": "2024-01-01T10:00:00Z",
        "end_time": "2024-01-01T10:30:00Z",
        "status": "success",
        "metadata": {
            "custom_field": "value",
            "nested": {"key": "value"}
        }
    }]
    
    records = loader.load_from_string(json.dumps(data))
    assert records[0].metadata["custom_field"] == "value"
    assert records[0].metadata["nested"]["key"] == "value"


def test_duration_calculation(loader):
    """Test that duration is calculated correctly."""
    data = [{
        "backup_id": "test-001",
        "start_time": "2024-01-01T10:00:00Z",
        "end_time": "2024-01-01T10:05:30Z",  # 5 minutes 30 seconds
        "status": "success"
    }]
    
    records = loader.load_from_string(json.dumps(data))
    assert records[0].duration == 330.0  # 5*60 + 30 seconds


def test_multiple_status_values(loader):
    """Test all valid status values."""
    statuses = ["success", "failure", "partial"]
    
    for status in statuses:
        data = [{
            "backup_id": f"test-{status}",
            "start_time": "2024-01-01T10:00:00Z",
            "end_time": "2024-01-01T10:30:00Z",
            "status": status
        }]
        
        records = loader.load_from_string(json.dumps(data))
        assert records[0].status == BackupStatus(status)


def test_empty_array(loader):
    """Test loading empty array."""
    records = loader.load_from_string("[]")
    assert len(records) == 0


def test_partial_failure_handling(loader):
    """Test that partial failures are reported correctly."""
    data = [
        {
            "backup_id": "valid-001",
            "start_time": "2024-01-01T10:00:00Z",
            "end_time": "2024-01-01T10:30:00Z",
            "status": "success"
        },
        {
            "backup_id": "invalid-001",
            "start_time": "invalid",
            "end_time": "2024-01-01T10:30:00Z",
            "status": "success"
        }
    ]
    
    with pytest.raises(JSONLoadError) as exc_info:
        loader.load_from_string(json.dumps(data))
    
    assert "Failed to normalize" in str(exc_info.value)
    assert "invalid-001" in str(exc_info.value)
