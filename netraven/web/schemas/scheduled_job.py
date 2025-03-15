"""
Scheduled job schemas for the NetRaven web interface.

This module provides Pydantic models for scheduled job-related API requests and responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class ScheduledJobBase(BaseModel):
    """Base scheduled job schema with common attributes."""
    name: str = Field(..., min_length=1, max_length=255)
    device_id: str = Field(..., min_length=36, max_length=36)
    schedule_type: str = Field(..., min_length=1, max_length=50)
    schedule_time: Optional[str] = Field(None, min_length=5, max_length=5)
    schedule_interval: Optional[int] = Field(None, gt=0)
    schedule_day: Optional[str] = Field(None, min_length=1, max_length=10)
    enabled: bool = True
    job_data: Optional[Dict[str, Any]] = None

class ScheduledJobCreate(ScheduledJobBase):
    """Schema for creating a new scheduled job."""
    pass

class ScheduledJobUpdate(BaseModel):
    """Schema for updating a scheduled job."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    schedule_type: Optional[str] = Field(None, min_length=1, max_length=50)
    schedule_time: Optional[str] = Field(None, min_length=5, max_length=5)
    schedule_interval: Optional[int] = Field(None, gt=0)
    schedule_day: Optional[str] = Field(None, min_length=1, max_length=10)
    enabled: Optional[bool] = None
    job_data: Optional[Dict[str, Any]] = None

class ScheduledJob(ScheduledJobBase):
    """Schema for scheduled job information returned by API."""
    id: str
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_by: str

    model_config = ConfigDict(from_attributes=True)

class ScheduledJobWithDevice(ScheduledJob):
    """Schema for scheduled job information with device details."""
    device_hostname: str
    device_ip: str
    device_type: str

    model_config = ConfigDict(from_attributes=True)

class ScheduledJobWithUser(ScheduledJob):
    """Schema for scheduled job information with user details."""
    username: str
    user_full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ScheduledJobComplete(ScheduledJobWithDevice, ScheduledJobWithUser):
    """Schema for complete scheduled job information with device and user details."""
    model_config = ConfigDict(from_attributes=True)

class ScheduledJobFilter(BaseModel):
    """Schema for filtering scheduled jobs."""
    device_id: Optional[str] = None
    schedule_type: Optional[str] = None
    enabled: Optional[bool] = None
    created_by: Optional[str] = None

class ScheduledJobToggle(BaseModel):
    """Schema for toggling a scheduled job."""
    enabled: bool = Field(...) 