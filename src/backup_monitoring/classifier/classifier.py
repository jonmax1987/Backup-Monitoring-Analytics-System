"""Backup classification module."""

import yaml
from pathlib import Path
from typing import Optional, List
from backup_monitoring.config.config_loader import get_config
from backup_monitoring.classifier.rules import (
    ClassificationRule,
    ClassificationRules,
    RuleEvaluator,
)
from backup_monitoring.data_loader.models import BackupRecord


class ClassificationError(Exception):
    """Exception raised when classification fails."""
    pass


class BackupClassifier:
    """Classifies backup records into logical backup types."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the backup classifier.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = get_config(config_path)
        self.rules_path = Path(self.config.classifier.rules_file)
        self.default_backup_type = self.config.classifier.default_backup_type
        self._rules: Optional[List[ClassificationRule]] = None
        self._evaluator: Optional[RuleEvaluator] = None
    
    def _load_rules(self) -> List[ClassificationRule]:
        """Load classification rules from YAML file."""
        if self._rules is None:
            rules_path = Path(self.rules_path)
            
            # If path is relative, try relative to project root
            if not rules_path.is_absolute():
                project_root = self._find_project_root()
                full_rules_path = project_root / rules_path
                if full_rules_path.exists():
                    rules_path = full_rules_path
                elif not rules_path.exists():
                    raise FileNotFoundError(f"Classification rules file not found: {self.rules_path}")
            
            if not rules_path.exists():
                raise FileNotFoundError(f"Classification rules file not found: {rules_path}")
            
            try:
                with open(rules_path, 'r', encoding='utf-8') as f:
                    rules_data = yaml.safe_load(f)
                
                rules_collection = ClassificationRules(**rules_data)
                self._rules = rules_collection.rules
            except Exception as e:
                raise ClassificationError(f"Failed to load classification rules: {e}") from e
        
        return self._rules
    
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        current = Path(__file__).resolve().parent
        while current.parent != current:
            if (current / "pyproject.toml").exists() or (current / "README.md").exists():
                return current
            current = current.parent
        return Path.cwd()
    
    def _get_evaluator(self) -> RuleEvaluator:
        """Get or create the rule evaluator."""
        if self._evaluator is None:
            rules = self._load_rules()
            self._evaluator = RuleEvaluator(rules)
        return self._evaluator
    
    def classify(self, record: BackupRecord) -> BackupRecord:
        """
        Classify a backup record.
        
        If the record already has a backup_type, it is preserved unless it's None.
        Otherwise, classification rules are applied.
        
        Args:
            record: BackupRecord to classify
            
        Returns:
            BackupRecord with backup_type set
        """
        # If backup_type is already set and not None, keep it
        if record.backup_type is not None and record.backup_type != self.default_backup_type:
            return record
        
        # Apply classification rules
        evaluator = self._get_evaluator()
        backup_type = evaluator.classify(record)
        
        # Use default if no rule matched
        if backup_type is None:
            backup_type = self.default_backup_type
        
        # Create a new record with the classified type
        record_dict = record.model_dump()
        record_dict['backup_type'] = backup_type
        
        return BackupRecord(**record_dict)
    
    def classify_batch(self, records: List[BackupRecord]) -> List[BackupRecord]:
        """
        Classify a batch of backup records.
        
        Args:
            records: List of BackupRecord objects to classify
            
        Returns:
            List of classified BackupRecord objects
        """
        evaluator = self._get_evaluator()
        classified = []
        
        for record in records:
            classified_record = self.classify(record)
            classified.append(classified_record)
        
        return classified
    
    def reload_rules(self) -> None:
        """Reload classification rules from file."""
        self._rules = None
        self._evaluator = None
