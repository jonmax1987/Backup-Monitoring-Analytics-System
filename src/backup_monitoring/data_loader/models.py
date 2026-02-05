"""Data models for backup records."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
from enum import Enum


class BackupStatus(str, Enum):
    """Backup execution status."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class BackupRecord(BaseModel):
    """Normalized backup record model."""

    model_config = ConfigDict(use_enum_values=True)

    backup_id: str = Field(..., description="Unique identifier for the backup")
    start_time: datetime = Field(..., description="Backup start timestamp")
    end_time: datetime = Field(..., description="Backup end timestamp")
    status: BackupStatus = Field(..., description="Backup execution status")
    backup_type: Optional[str] = Field(None, description="Type of backup (classified)")
    source_system: Optional[str] = Field(None, description="Source system identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @model_validator(mode='after')
    def validate_end_after_start(self):
        """Validate that end_time is after start_time."""
        if self.end_time < self.start_time:
            raise ValueError("end_time must be after start_time")
        return self

    @property
    def duration(self) -> float:
        """Calculate backup duration in seconds."""
        delta = self.end_time - self.start_time
        return delta.total_seconds()
