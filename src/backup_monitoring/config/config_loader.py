"""Configuration loader for the backup monitoring system."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application configuration."""
    name: str
    version: str
    log_level: str = "INFO"
    log_file: str = "logs/backup_monitoring.log"


class DataLoaderConfig(BaseModel):
    """Data loader configuration."""
    json_schema_path: str = "config/json_schema.json"
    default_timezone: str = "UTC"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class ClassifierConfig(BaseModel):
    """Classifier configuration."""
    rules_file: str = "config/classification_rules.yaml"
    default_backup_type: str = "unknown"


class ProcessingConfig(BaseModel):
    """Processing engine configuration."""
    aggregation_periods: list[str] = Field(default_factory=lambda: ["day", "week", "month"])
    duration_unit: str = "seconds"


class AnomalyDetectionConfig(BaseModel):
    """Anomaly detection configuration."""
    enabled: bool = True
    threshold_multiplier: float = 2.0
    min_samples: int = 5
    lookback_periods: int = 7


class ReportingConfig(BaseModel):
    """Reporting configuration."""
    output_directory: str = "reports/output"
    formats: list[str] = Field(default_factory=lambda: ["json", "csv", "html"])
    date_format: str = "%Y-%m-%d"


class IntegrationConfig(BaseModel):
    """Integration layer configuration."""
    api_enabled: bool = False
    api_port: int = 8000
    prometheus_enabled: bool = False
    prometheus_port: int = 9090


class SystemConfig(BaseModel):
    """Main system configuration."""
    app: AppConfig
    data_loader: DataLoaderConfig
    classifier: ClassifierConfig
    processing: ProcessingConfig
    anomaly_detection: AnomalyDetectionConfig
    reporting: ReportingConfig
    integration: IntegrationConfig


class ConfigLoader:
    """Loads and validates configuration from YAML files."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to the configuration file. If None, uses default.
        """
        if config_path is None:
            # Default to config/config.yaml relative to project root
            project_root = self._find_project_root()
            config_path = project_root / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Optional[SystemConfig] = None
    
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        # Start from the directory containing this file
        current = Path(__file__).resolve().parent
        # Look for project root markers (pyproject.toml, README.md, etc.)
        while current.parent != current:
            if (current / "pyproject.toml").exists() or (current / "README.md").exists():
                return current
            current = current.parent
        # Fallback to current directory
        return Path.cwd()
    
    def load(self) -> SystemConfig:
        """
        Load configuration from file.
        
        Returns:
            SystemConfig: Validated configuration object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Validate and create config object
        self._config = SystemConfig(**config_data)
        return self._config
    
    def get_config(self) -> SystemConfig:
        """
        Get the loaded configuration.
        
        Returns:
            SystemConfig: The configuration object
            
        Raises:
            RuntimeError: If config hasn't been loaded yet
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load() first.")
        return self._config
    
    def reload(self) -> SystemConfig:
        """Reload configuration from file."""
        return self.load()


# Global config instance (lazy-loaded)
_global_config: Optional[SystemConfig] = None
_config_loader: Optional[ConfigLoader] = None


def get_config(config_path: Optional[str] = None) -> SystemConfig:
    """
    Get the global configuration instance.
    
    Args:
        config_path: Optional path to config file (only used on first call)
        
    Returns:
        SystemConfig: The configuration object
    """
    global _global_config, _config_loader
    
    if _global_config is None:
        _config_loader = ConfigLoader(config_path)
        _global_config = _config_loader.load()
    
    return _global_config
