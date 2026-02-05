"""Data models for processed metrics."""

from datetime import date, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PeriodType(str, Enum):
    """Types of aggregation periods."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class AggregatedMetrics(BaseModel):
    """Aggregated metrics for a specific period and backup type."""
    
    period_start: date = Field(..., description="Start date of the aggregation period")
    period_end: date = Field(..., description="End date of the aggregation period")
    period_type: PeriodType = Field(..., description="Type of period (day/week/month)")
    backup_type: str = Field(..., description="Type of backup")
    
    # Duration metrics
    average_duration: float = Field(..., description="Average backup duration in seconds")
    max_duration: float = Field(..., description="Maximum backup duration in seconds")
    min_duration: float = Field(..., description="Minimum backup duration in seconds")
    total_duration: float = Field(..., description="Total duration of all backups in seconds")
    
    # Count metrics
    total_count: int = Field(..., description="Total number of backups")
    success_count: int = Field(..., description="Number of successful backups")
    failure_count: int = Field(..., description="Number of failed backups")
    partial_count: int = Field(..., description="Number of partial backups")
    
    # Additional metadata
    anomaly_flag: bool = Field(False, description="Whether anomalies were detected")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100.0
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as a percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.failure_count / self.total_count) * 100.0


class DailyMetrics(AggregatedMetrics):
    """Daily aggregated metrics."""
    period_type: PeriodType = Field(default=PeriodType.DAY, description="Period type is day")
    period_date: date = Field(..., description="Date of the aggregation")


class WeeklyMetrics(AggregatedMetrics):
    """Weekly aggregated metrics."""
    period_type: PeriodType = Field(default=PeriodType.WEEK, description="Period type is week")
    week_start: date = Field(..., description="Start date of the week")
    week_end: date = Field(..., description="End date of the week")
    week_number: int = Field(..., description="Week number in the year")


class MonthlyMetrics(AggregatedMetrics):
    """Monthly aggregated metrics."""
    period_type: PeriodType = Field(default=PeriodType.MONTH, description="Period type is month")
    year: int = Field(..., description="Year")
    month: int = Field(..., description="Month (1-12)")
