"""
Job log schemas for the NetRaven web interface.

This module provides Pydantic models for job log-related API requests and responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    """Job status enum."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class JobLogEntryBase(BaseModel):
    """Base job log entry schema with common attributes."""
    timestamp: datetime = Field(...)
    level: str = Field(..., min_length=1, max_length=50)
    category: Optional[str] = None
    message: str = Field(..., min_length=1)
    details: Optional[Dict[str, Any]] = None
    
    # New fields for enhanced session logging
    session_log_path: Optional[str] = None
    session_log_content: Optional[str] = None
    credential_username: Optional[str] = None

class JobLogEntryCreate(JobLogEntryBase):
    """Schema for creating a new job log entry."""
    job_log_id: str = Field(..., min_length=36, max_length=36)

class JobLogEntry(JobLogEntryBase):
    """Schema for job log entry information returned by API."""
    id: str
    job_log_id: str

    model_config = ConfigDict(from_attributes=True)

class JobLogBase(BaseModel):
    """Base job log schema with common attributes."""
    session_id: str = Field(..., min_length=36, max_length=36)
    job_type: str = Field(..., min_length=1, max_length=50)
    status: str = Field(..., min_length=1, max_length=50)
    start_time: datetime = Field(...)
    end_time: Optional[datetime] = None
    result_code: Optional[int] = None
    result_message: Optional[str] = None
    device_id: Optional[str] = None
    job_data: Optional[Dict[str, Any]] = None
    retention_days: Optional[int] = Field(default=30, ge=1, le=365)

class JobLogCreate(JobLogBase):
    """Schema for creating a new job log."""
    id: Optional[str] = None
    session_id: Optional[str] = None
    created_by: Optional[str] = None

class JobLogUpdate(BaseModel):
    """Schema for updating a job log."""
    status: Optional[str] = Field(None, min_length=1, max_length=20)
    end_time: Optional[datetime] = None
    result_message: Optional[str] = None
    job_data: Optional[Dict[str, Any]] = None
    retention_days: Optional[int] = Field(None, ge=1, le=3650)  # Max 10 years

class JobLog(JobLogBase):
    """Schema for job log information returned by API."""
    id: str
    session_id: str
    created_by: str

    model_config = ConfigDict(from_attributes=True)

class JobLogWithEntries(JobLog):
    """Schema for job log information with entries."""
    entries: List[JobLogEntry] = []

    model_config = ConfigDict(from_attributes=True)

class JobLogWithDevice(JobLog):
    """Schema for job log information with device details."""
    device_hostname: Optional[str] = None
    device_ip: Optional[str] = None
    device_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class JobLogWithUser(JobLog):
    """
    Schema for job log information with user details.
    
    Simplified to include only the username field for consistency and to avoid
    attribute access issues with non-existent fields.
    """
    username: str

    model_config = ConfigDict(from_attributes=True)

class JobLogComplete(JobLogWithDevice, JobLogWithUser, JobLogWithEntries):
    """Schema for complete job log information with device, user, and entries."""
    model_config = ConfigDict(from_attributes=True)

class RetentionPolicyUpdate(BaseModel):
    """Schema for updating retention policy."""
    default_retention_days: int = Field(..., ge=1, le=3650)  # Max 10 years
    apply_to_existing: bool = Field(False)

class JobLogFilter(BaseModel):
    """Schema for filtering job logs."""
    device_id: Optional[str] = None
    job_type: Optional[str] = None
    status: Optional[str] = None
    created_by: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None 