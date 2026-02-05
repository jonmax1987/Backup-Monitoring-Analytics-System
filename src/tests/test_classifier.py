"""Tests for backup classifier."""

import pytest
import tempfile
import yaml
from pathlib import Path
from datetime import datetime
import pytz

from backup_monitoring.classifier.classifier import BackupClassifier, ClassificationError
from backup_monitoring.classifier.rules import (
    ClassificationRule,
    ClassificationRules,
    Condition,
    Operator,
    RuleEvaluator,
)
from backup_monitoring.data_loader.models import BackupRecord, BackupStatus


@pytest.fixture
def sample_rules():
    """Sample classification rules for testing."""
    return [
        ClassificationRule(
            name="database_backup",
            conditions=[
                Condition(
                    field="source_system",
                    operator=Operator.CONTAINS,
                    value="database",
                    case_sensitive=False
                )
            ],
            backup_type="database"
        ),
        ClassificationRule(
            name="filesystem_backup",
            conditions=[
                Condition(
                    field="source_system",
                    operator=Operator.CONTAINS,
                    value="filesystem",
                    case_sensitive=False
                )
            ],
            backup_type="filesystem"
        ),
        ClassificationRule(
            name="default",
            conditions=[],
            backup_type="unknown"
        )
    ]


@pytest.fixture
def temp_rules_file(sample_rules):
    """Create a temporary rules YAML file."""
    rules_data = {"rules": [rule.model_dump() for rule in sample_rules]}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(rules_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def sample_backup_record():
    """Create a sample backup record."""
    return BackupRecord(
        backup_id="test-001",
        start_time=datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC),
        end_time=datetime(2024, 1, 1, 10, 30, 0, tzinfo=pytz.UTC),
        status=BackupStatus.SUCCESS,
        source_system="database-primary",
        metadata={"key": "value"}
    )


def test_classifier_loads_rules(temp_rules_file):
    """Test that classifier loads rules from file."""
    classifier = BackupClassifier()
    # Override rules path for testing
    classifier.rules_path = Path(temp_rules_file)
    classifier._rules = None  # Force reload
    
    rules = classifier._load_rules()
    assert len(rules) == 3
    assert rules[0].name == "database_backup"
    assert rules[0].backup_type == "database"


def test_classifier_classifies_database_backup(sample_backup_record, temp_rules_file):
    """Test classification of database backup."""
    classifier = BackupClassifier()
    classifier.rules_path = Path(temp_rules_file)
    classifier._rules = None
    
    classified = classifier.classify(sample_backup_record)
    assert classified.backup_type == "database"


def test_classifier_classifies_filesystem_backup(temp_rules_file):
    """Test classification of filesystem backup."""
    record = BackupRecord(
        backup_id="test-002",
        start_time=datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC),
        end_time=datetime(2024, 1, 1, 10, 30, 0, tzinfo=pytz.UTC),
        status=BackupStatus.SUCCESS,
        source_system="filesystem-storage"
    )
    
    classifier = BackupClassifier()
    classifier.rules_path = Path(temp_rules_file)
    classifier._rules = None
    
    classified = classifier.classify(record)
    assert classified.backup_type == "filesystem"


def test_classifier_uses_default_for_unknown(temp_rules_file):
    """Test that classifier uses default type for unknown backups."""
    record = BackupRecord(
        backup_id="test-003",
        start_time=datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC),
        end_time=datetime(2024, 1, 1, 10, 30, 0, tzinfo=pytz.UTC),
        status=BackupStatus.SUCCESS,
        source_system="unknown-system"
    )
    
    classifier = BackupClassifier()
    classifier.rules_path = Path(temp_rules_file)
    classifier._rules = None
    
    classified = classifier.classify(record)
    assert classified.backup_type == "unknown"


def test_classifier_preserves_existing_type(sample_backup_record, temp_rules_file):
    """Test that classifier preserves existing backup_type."""
    record = BackupRecord(
        backup_id="test-004",
        start_time=datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC),
        end_time=datetime(2024, 1, 1, 10, 30, 0, tzinfo=pytz.UTC),
        status=BackupStatus.SUCCESS,
        source_system="database-primary",
        backup_type="custom_type"  # Already set
    )
    
    classifier = BackupClassifier()
    classifier.rules_path = Path(temp_rules_file)
    classifier._rules = None
    
    classified = classifier.classify(record)
    assert classified.backup_type == "custom_type"  # Should be preserved


def test_classifier_batch_classification(temp_rules_file):
    """Test batch classification of multiple records."""
    records = [
        BackupRecord(
            backup_id=f"test-{i}",
            start_time=datetime(2024, 1, 1, 10, 0, 0, tzinfo=pytz.UTC),
            end_time=datetime(2024, 1, 1, 10, 30, 0, tzinfo=pytz.UTC),
            status=BackupStatus.SUCCESS,
            source_system=["database-primary", "filesystem-storage", "unknown"][i]
        )
        for i in range(3)
    ]
    
    classifier = BackupClassifier()
    classifier.rules_path = Path(temp_rules_file)
    classifier._rules = None
    
    classified = classifier.classify_batch(records)
    assert len(classified) == 3
    assert classified[0].backup_type == "database"
    assert classified[1].backup_type == "filesystem"
    assert classified[2].backup_type == "unknown"


def test_rule_evaluator_equals_operator():
    """Test rule evaluator with equals operator."""
    rule = ClassificationRule(
        name="test",
        conditions=[
            Condition(field="source_system", operator=Operator.EQUALS, value="test-system")
        ],
        backup_type="test_type"
    )
    
    evaluator = RuleEvaluator([rule])
    record = {"source_system": "test-system"}
    assert evaluator.classify(record) == "test_type"
    
    record2 = {"source_system": "other-system"}
    assert evaluator.classify(record2) is None


def test_rule_evaluator_contains_operator():
    """Test rule evaluator with contains operator."""
    rule = ClassificationRule(
        name="test",
        conditions=[
            Condition(field="source_system", operator=Operator.CONTAINS, value="db", case_sensitive=False)
        ],
        backup_type="database"
    )
    
    evaluator = RuleEvaluator([rule])
    record = {"source_system": "my-database-server"}
    assert evaluator.classify(record) == "database"
    
    record2 = {"source_system": "DB-SERVER"}  # Case insensitive
    assert evaluator.classify(record2) == "database"


def test_rule_evaluator_starts_with_operator():
    """Test rule evaluator with starts_with operator."""
    rule = ClassificationRule(
        name="test",
        conditions=[
            Condition(field="backup_id", operator=Operator.STARTS_WITH, value="backup-")
        ],
        backup_type="backup"
    )
    
    evaluator = RuleEvaluator([rule])
    record = {"backup_id": "backup-001"}
    assert evaluator.classify(record) == "backup"
    
    record2 = {"backup_id": "snapshot-001"}
    assert evaluator.classify(record2) is None


def test_rule_evaluator_in_operator():
    """Test rule evaluator with in operator."""
    rule = ClassificationRule(
        name="test",
        conditions=[
            Condition(field="status", operator=Operator.IN, value=["success", "partial"])
        ],
        backup_type="successful"
    )
    
    evaluator = RuleEvaluator([rule])
    record = {"status": "success"}
    assert evaluator.classify(record) == "successful"
    
    record2 = {"status": "failure"}
    assert evaluator.classify(record2) is None


def test_rule_evaluator_nested_field():
    """Test rule evaluator with nested field access."""
    rule = ClassificationRule(
        name="test",
        conditions=[
            Condition(field="metadata.type", operator=Operator.EQUALS, value="full")
        ],
        backup_type="full_backup"
    )
    
    evaluator = RuleEvaluator([rule])
    record = {"metadata": {"type": "full"}}
    assert evaluator.classify(record) == "full_backup"
    
    record2 = {"metadata": {"type": "incremental"}}
    assert evaluator.classify(record2) is None


def test_rule_evaluator_multiple_conditions():
    """Test rule evaluator with multiple conditions (AND logic)."""
    rule = ClassificationRule(
        name="test",
        conditions=[
            Condition(field="source_system", operator=Operator.CONTAINS, value="database"),
            Condition(field="status", operator=Operator.EQUALS, value="success")
        ],
        backup_type="successful_database"
    )
    
    evaluator = RuleEvaluator([rule])
    record = {"source_system": "database-primary", "status": "success"}
    assert evaluator.classify(record) == "successful_database"
    
    record2 = {"source_system": "database-primary", "status": "failure"}
    assert evaluator.classify(record2) is None  # Second condition fails


def test_rule_evaluator_regex_operator():
    """Test rule evaluator with regex operator."""
    rule = ClassificationRule(
        name="test",
        conditions=[
            Condition(field="backup_id", operator=Operator.REGEX, value=r"backup-\d{4}")
        ],
        backup_type="numbered_backup"
    )
    
    evaluator = RuleEvaluator([rule])
    record = {"backup_id": "backup-2024"}
    assert evaluator.classify(record) == "numbered_backup"
    
    record2 = {"backup_id": "backup-abc"}
    assert evaluator.classify(record2) is None


def test_rule_evaluator_case_sensitive():
    """Test rule evaluator with case-sensitive comparison."""
    rule = ClassificationRule(
        name="test",
        conditions=[
            Condition(field="source_system", operator=Operator.CONTAINS, value="DB", case_sensitive=True)
        ],
        backup_type="database"
    )
    
    evaluator = RuleEvaluator([rule])
    record = {"source_system": "my-DB-server"}
    assert evaluator.classify(record) == "database"
    
    record2 = {"source_system": "my-db-server"}  # Lowercase
    assert evaluator.classify(record2) is None


def test_rule_evaluator_missing_field():
    """Test rule evaluator with missing field."""
    rule = ClassificationRule(
        name="test",
        conditions=[
            Condition(field="nonexistent_field", operator=Operator.EQUALS, value="value")
        ],
        backup_type="test_type"
    )
    
    evaluator = RuleEvaluator([rule])
    record = {"other_field": "value"}
    assert evaluator.classify(record) is None


def test_classifier_reload_rules(temp_rules_file):
    """Test that classifier can reload rules."""
    classifier = BackupClassifier()
    classifier.rules_path = Path(temp_rules_file)
    
    # Load rules
    rules1 = classifier._load_rules()
    assert len(rules1) == 3
    
    # Reload
    classifier.reload_rules()
    rules2 = classifier._load_rules()
    assert len(rules2) == 3
    assert classifier._evaluator is None  # Should be reset


def test_classifier_missing_rules_file():
    """Test error handling for missing rules file."""
    classifier = BackupClassifier()
    classifier.rules_path = Path("/nonexistent/rules.yaml")
    
    with pytest.raises(FileNotFoundError):
        classifier._load_rules()
