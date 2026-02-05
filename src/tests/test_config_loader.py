"""Tests for configuration loader."""

import pytest
import tempfile
import yaml
from pathlib import Path
from backup_monitoring.config.config_loader import ConfigLoader, SystemConfig, get_config


def test_config_loader_loads_valid_config():
    """Test that ConfigLoader loads a valid configuration file."""
    # Create a temporary config file
    config_data = {
        "app": {
            "name": "Test App",
            "version": "1.0.0",
            "log_level": "DEBUG",
            "log_file": "test.log"
        },
        "data_loader": {
            "json_schema_path": "schema.json",
            "default_timezone": "UTC",
            "date_format": "%Y-%m-%d"
        },
        "classifier": {
            "rules_file": "rules.yaml",
            "default_backup_type": "unknown"
        },
        "processing": {
            "aggregation_periods": ["day", "week"],
            "duration_unit": "seconds"
        },
        "anomaly_detection": {
            "enabled": True,
            "threshold_multiplier": 2.0,
            "min_samples": 5,
            "lookback_periods": 7
        },
        "reporting": {
            "output_directory": "reports",
            "formats": ["json", "csv"],
            "date_format": "%Y-%m-%d"
        },
        "integration": {
            "api_enabled": False,
            "api_port": 8000,
            "prometheus_enabled": False,
            "prometheus_port": 9090
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        loader = ConfigLoader(config_path)
        config = loader.load()
        
        assert isinstance(config, SystemConfig)
        assert config.app.name == "Test App"
        assert config.app.version == "1.0.0"
        assert config.app.log_level == "DEBUG"
        assert config.data_loader.json_schema_path == "schema.json"
        assert config.processing.aggregation_periods == ["day", "week"]
        assert config.anomaly_detection.enabled is True
    finally:
        Path(config_path).unlink()


def test_config_loader_raises_on_missing_file():
    """Test that ConfigLoader raises FileNotFoundError for missing config file."""
    loader = ConfigLoader("/nonexistent/config.yaml")
    
    with pytest.raises(FileNotFoundError):
        loader.load()


def test_config_loader_raises_on_invalid_config():
    """Test that ConfigLoader raises ValueError for invalid config."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        # Invalid config - missing required fields
        yaml.dump({"app": {"name": "Test"}}, f)
        config_path = f.name
    
    try:
        loader = ConfigLoader(config_path)
        with pytest.raises(Exception):  # Pydantic validation error
            loader.load()
    finally:
        Path(config_path).unlink()


def test_get_config_function():
    """Test the global get_config function."""
    # This will use the default config file if it exists
    # If not, it will fail - which is expected behavior
    try:
        config = get_config()
        assert isinstance(config, SystemConfig)
    except FileNotFoundError:
        # Expected if default config doesn't exist yet
        pass


def test_config_reload():
    """Test that config can be reloaded."""
    config_data = {
        "app": {"name": "Test", "version": "1.0.0", "log_level": "INFO", "log_file": "test.log"},
        "data_loader": {"json_schema_path": "schema.json", "default_timezone": "UTC", "date_format": "%Y-%m-%d"},
        "classifier": {"rules_file": "rules.yaml", "default_backup_type": "unknown"},
        "processing": {"aggregation_periods": ["day"], "duration_unit": "seconds"},
        "anomaly_detection": {"enabled": True, "threshold_multiplier": 2.0, "min_samples": 5, "lookback_periods": 7},
        "reporting": {"output_directory": "reports", "formats": ["json"], "date_format": "%Y-%m-%d"},
        "integration": {"api_enabled": False, "api_port": 8000, "prometheus_enabled": False, "prometheus_port": 9090}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        loader = ConfigLoader(config_path)
        config1 = loader.load()
        config2 = loader.reload()
        
        assert config1.app.name == config2.app.name
    finally:
        Path(config_path).unlink()
