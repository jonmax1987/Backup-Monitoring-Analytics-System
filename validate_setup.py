#!/usr/bin/env python3
"""Validation script for CORE-001 - Project Skeleton & Configuration.

This script validates that:
1. Project structure is correct
2. Configuration can be loaded from file
3. All required modules are importable
"""

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def validate_project_structure():
    """Validate that all required directories and files exist."""
    print("Validating project structure...")
    
    required_paths = [
        "src/backup_monitoring/__init__.py",
        "src/backup_monitoring/config/config_loader.py",
        "src/backup_monitoring/data_loader/__init__.py",
        "src/backup_monitoring/classifier/__init__.py",
        "src/backup_monitoring/processing/__init__.py",
        "src/backup_monitoring/anomaly_detection/__init__.py",
        "src/backup_monitoring/reporting/__init__.py",
        "src/backup_monitoring/integration/__init__.py",
        "src/tests/__init__.py",
        "config/config.yaml",
        "config/classification_rules.yaml",
        "config/json_schema.json",
        "pyproject.toml",
        "requirements.txt",
        "README.md",
    ]
    
    missing = []
    for path in required_paths:
        full_path = project_root / path
        if not full_path.exists():
            missing.append(path)
    
    if missing:
        print(f"❌ Missing files/directories: {', '.join(missing)}")
        return False
    
    print("✅ Project structure is valid")
    return True


def validate_config_loading():
    """Validate that configuration can be loaded from file."""
    print("\nValidating configuration loading...")
    
    try:
        from backup_monitoring.config.config_loader import ConfigLoader, SystemConfig
        
        config_path = project_root / "config" / "config.yaml"
        loader = ConfigLoader(str(config_path))
        config = loader.load()
        
        # Validate config structure
        assert isinstance(config, SystemConfig), "Config should be SystemConfig instance"
        assert config.app.name, "App name should be set"
        assert config.app.version, "App version should be set"
        assert config.data_loader.json_schema_path, "Data loader schema path should be set"
        assert config.classifier.rules_file, "Classifier rules file should be set"
        assert config.processing.aggregation_periods, "Processing periods should be set"
        assert config.anomaly_detection.enabled is not None, "Anomaly detection enabled should be set"
        assert config.reporting.formats, "Reporting formats should be set"
        assert config.integration.api_port > 0, "Integration API port should be set"
        
        print("✅ Configuration loaded successfully")
        print(f"   App: {config.app.name} v{config.app.version}")
        print(f"   Log level: {config.app.log_level}")
        print(f"   Aggregation periods: {', '.join(config.processing.aggregation_periods)}")
        print(f"   Report formats: {', '.join(config.reporting.formats)}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_imports():
    """Validate that all modules can be imported."""
    print("\nValidating module imports...")
    
    modules = [
        "backup_monitoring",
        "backup_monitoring.config",
        "backup_monitoring.config.config_loader",
        "backup_monitoring.data_loader",
        "backup_monitoring.classifier",
        "backup_monitoring.processing",
        "backup_monitoring.anomaly_detection",
        "backup_monitoring.reporting",
        "backup_monitoring.integration",
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")
            failed.append(module)
    
    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        return False
    
    print("✅ All modules importable")
    return True


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("CORE-001 Validation: Project Skeleton & Configuration")
    print("=" * 60)
    
    results = [
        validate_project_structure(),
        validate_config_loading(),
        validate_imports(),
    ]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All validations passed!")
        print("CORE-001 is complete and ready for next task.")
        return 0
    else:
        print("❌ Some validations failed. Please fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
