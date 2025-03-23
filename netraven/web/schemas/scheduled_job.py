"""
Pydantic schemas for scheduled jobs.

This module provides the Pydantic schemas for scheduled job creation, update,
and response objects.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

from netraven.web.constants import JobTypeEnum, ScheduleTypeEnum

class ScheduledJobBase(BaseModel):
    """Base model for scheduled jobs with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    device_id: str
    job_type: JobTypeEnum = JobTypeEnum.BACKUP
    schedule_type: ScheduleTypeEnum
    enabled: bool = True
    
    # Schedule fields
    schedule_time: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")  # HH:MM format
    schedule_day: Optional[str] = None  # Day of week/month for recurrence
    schedule_interval: Optional[int] = None  # Interval for recurring schedules
    
    job_data: Optional[Dict[str, Any]] = None

class ScheduledJobCreate(ScheduledJobBase):
    """Schema for creating a new scheduled job."""
    pass

class ScheduledJobUpdate(BaseModel):
    """Schema for updating an existing scheduled job."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    device_id: Optional[str] = None
    job_type: Optional[JobTypeEnum] = None
    schedule_type: Optional[ScheduleTypeEnum] = None
    enabled: Optional[bool] = None
    
    # Schedule fields
    schedule_time: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")  # HH:MM format
    schedule_day: Optional[str] = None  # Day of week/month for recurrence
    schedule_interval: Optional[int] = None  # Interval for recurring schedules
    
    job_data: Optional[Dict[str, Any]] = None

class ScheduledJobInDB(ScheduledJobBase):
    """Schema for a scheduled job as stored in the database."""
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

    class Config:
        """Pydantic config for the model."""
        from_attributes = True

class ScheduledJobWithDetails(ScheduledJobInDB):
    """Schema for a scheduled job with related details."""
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    username: Optional[str] = None  # Username of the creator

# Define an alias for backward compatibility with existing code
ScheduledJob = ScheduledJobInDB

class ScheduledJobList(BaseModel):
    """Schema for a list of scheduled jobs."""
    jobs: List[ScheduledJobWithDetails]
    total: int

class ScheduledJobToggle(BaseModel):
    """Schema for toggling a scheduled job's enabled status."""
    enabled: bool = Field(..., description="Whether the job should be enabled")

class ScheduledJobFilter(BaseModel):
    """Schema for filtering scheduled jobs."""
    device_id: Optional[str] = None
    schedule_type: Optional[ScheduleTypeEnum] = None
    job_type: Optional[JobTypeEnum] = None
    enabled: Optional[bool] = None
    created_by: Optional[str] = None 