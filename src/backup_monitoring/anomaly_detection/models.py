"""Data models for anomaly detection."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import date

from backup_monitoring.processing.models import AggregatedMetrics


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""
    DURATION_HIGH = "duration_high"
    DURATION_LOW = "duration_low"
    COUNT_HIGH = "count_high"
    COUNT_LOW = "count_low"
    FAILURE_RATE_HIGH = "failure_rate_high"
    SUCCESS_RATE_LOW = "success_rate_low"


class AnomalySeverity(str, Enum):
    """Severity levels for anomalies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Anomaly(BaseModel):
    """Represents a detected anomaly."""
    
    anomaly_type: AnomalyType = Field(..., description="Type of anomaly")
    severity: AnomalySeverity = Field(..., description="Severity level")
    metric_name: str = Field(..., description="Name of the metric that triggered the anomaly")
    current_value: float = Field(..., description="Current metric value")
    expected_value: float = Field(..., description="Expected/average metric value")
    threshold_value: float = Field(..., description="Threshold value that was breached")
    deviation_percentage: float = Field(..., description="Percentage deviation from expected")
    
    # Context
    period_start: date = Field(..., description="Start date of the period with anomaly")
    period_end: date = Field(..., description="End date of the period with anomaly")
    backup_type: str = Field(..., description="Backup type affected")
    period_type: str = Field(..., description="Type of period (day/week/month)")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    
    @property
    def is_critical(self) -> bool:
        """Whether this is a critical anomaly."""
        return self.severity == AnomalySeverity.CRITICAL


class AnomalyDetectionResult(BaseModel):
    """Result of anomaly detection for a metric."""
    
    has_anomaly: bool = Field(..., description="Whether an anomaly was detected")
    anomalies: List[Anomaly] = Field(default_factory=list, description="List of detected anomalies")
    metrics: AggregatedMetrics = Field(..., description="Metrics that were analyzed")
    historical_average: Optional[float] = Field(None, description="Historical average used for comparison")
    samples_used: int = Field(0, description="Number of historical samples used")
    
    @property
    def critical_anomalies(self) -> List[Anomaly]:
        """Get only critical anomalies."""
        return [a for a in self.anomalies if a.is_critical]
    
    @property
    def anomaly_count(self) -> int:
        """Get total number of anomalies."""
        return len(self.anomalies)
