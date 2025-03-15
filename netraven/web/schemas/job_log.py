"""
Job log schemas for the NetRaven web interface.

This module provides Pydantic models for job log-related API requests and responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class JobLogEntryBase(BaseModel):
    """Base job log entry schema with common attributes."""
    timestamp: datetime = Field(...)
    level: str = Field(..., min_length=1, max_length=20)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    message: str = Field(...)
    details: Optional[Dict[str, Any]] = None

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
    status: str = Field(..., min_length=1, max_length=20)
    start_time: datetime = Field(...)
    end_time: Optional[datetime] = None
    result_message: Optional[str] = None
    job_data: Optional[Dict[str, Any]] = None
    retention_days: Optional[int] = Field(None, ge=1, le=3650)  # Max 10 years

class JobLogCreate(JobLogBase):
    """Schema for creating a new job log."""
    device_id: Optional[str] = Field(None, min_length=36, max_length=36)
    created_by: str = Field(..., min_length=1, max_length=36)

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
    device_id: Optional[str] = None
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

    model_config = ConfigDict(from_attributes=True)

class JobLogWithUser(JobLog):
    """Schema for job log information with user details."""
    username: str
    user_full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class JobLogComplete(JobLogWithDevice, JobLogWithUser):
    """Schema for complete job log information with device and user details."""
    entries: List[JobLogEntry] = []

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
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by: Optional[str] = None
    session_id: Optional[str] = None 