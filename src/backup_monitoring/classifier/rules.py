"""Classification rules models and evaluation."""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class Operator(str, Enum):
    """Supported comparison operators for classification rules."""
    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    IN = "in"
    NOT_EQUALS = "not_equals"
    NOT_CONTAINS = "not_contains"


class Condition(BaseModel):
    """A single condition in a classification rule."""
    field: str = Field(..., description="Field name to check (supports dot notation for nested fields)")
    operator: Operator = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Value to compare against")
    case_sensitive: bool = Field(True, description="Whether string comparison is case-sensitive")


class ClassificationRule(BaseModel):
    """A classification rule with conditions and resulting backup type."""
    name: str = Field(..., description="Rule name/identifier")
    conditions: List[Condition] = Field(default_factory=list, description="List of conditions (all must match)")
    backup_type: str = Field(..., description="Backup type to assign if rule matches")


class ClassificationRules(BaseModel):
    """Collection of classification rules."""
    rules: List[ClassificationRule] = Field(default_factory=list, description="List of classification rules")


class RuleEvaluator:
    """Evaluates classification rules against backup records."""
    
    def __init__(self, rules: List[ClassificationRule]):
        """
        Initialize the rule evaluator.
        
        Args:
            rules: List of classification rules to evaluate
        """
        self.rules = rules
    
    def _get_field_value(self, record: Dict[str, Any], field: str) -> Any:
        """
        Get field value from record, supporting dot notation for nested fields.
        
        Args:
            record: Backup record dictionary
            field: Field name (supports dot notation like "metadata.key")
            
        Returns:
            Field value or None if not found
        """
        parts = field.split('.')
        value = record
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
            
            if value is None:
                return None
        
        return value
    
    def _evaluate_condition(self, condition: Condition, record: Dict[str, Any]) -> bool:
        """
        Evaluate a single condition against a record.
        
        Args:
            condition: Condition to evaluate
            record: Backup record dictionary
            
        Returns:
            True if condition matches, False otherwise
        """
        field_value = self._get_field_value(record, condition.field)
        
        if field_value is None:
            return False
        
        # Convert to string for string operations if needed
        if condition.operator in [Operator.CONTAINS, Operator.STARTS_WITH, Operator.ENDS_WITH]:
            field_value = str(field_value)
            compare_value = str(condition.value)
            
            if not condition.case_sensitive:
                field_value = field_value.lower()
                compare_value = compare_value.lower()
        
        # Evaluate based on operator
        if condition.operator == Operator.EQUALS:
            return field_value == condition.value
        
        elif condition.operator == Operator.NOT_EQUALS:
            return field_value != condition.value
        
        elif condition.operator == Operator.CONTAINS:
            return compare_value in field_value
        
        elif condition.operator == Operator.NOT_CONTAINS:
            return compare_value not in field_value
        
        elif condition.operator == Operator.STARTS_WITH:
            return field_value.startswith(compare_value)
        
        elif condition.operator == Operator.ENDS_WITH:
            return field_value.endswith(compare_value)
        
        elif condition.operator == Operator.IN:
            if isinstance(condition.value, list):
                return field_value in condition.value
            return False
        
        elif condition.operator == Operator.REGEX:
            import re
            flags = 0 if condition.case_sensitive else re.IGNORECASE
            pattern = str(condition.value)
            return bool(re.search(pattern, str(field_value), flags))
        
        return False
    
    def classify(self, record: Dict[str, Any]) -> Optional[str]:
        """
        Classify a backup record using the rules.
        
        Rules are evaluated in order, and the first matching rule's backup_type is returned.
        
        Args:
            record: Backup record dictionary (can be BackupRecord model_dict or plain dict)
            
        Returns:
            Backup type string, or None if no rule matches
        """
        # Convert Pydantic model to dict if needed
        if hasattr(record, 'model_dump'):
            record_dict = record.model_dump()
        elif hasattr(record, 'dict'):
            record_dict = record.dict()
        else:
            record_dict = record
        
        # Evaluate rules in order
        for rule in self.rules:
            # All conditions must match (AND logic)
            if all(self._evaluate_condition(condition, record_dict) for condition in rule.conditions):
                return rule.backup_type
        
        return None
