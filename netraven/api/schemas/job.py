from datetime import datetime
from typing import Optional, List, Literal
from pydantic import Field, field_validator, model_validator
import re
from croniter import croniter

from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from .tag import Tag # Import Tag schema for relationships

# Define valid schedule types
ScheduleTypes = Literal["interval", "cron", "onetime"]

# --- Job Schemas ---

class JobBase(BaseSchema):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        pattern=r"^[\w\-\s]+$",
        example="Backup Core Routers Daily",
        description="Job name. Can contain letters, numbers, underscores, hyphens, and spaces."
    )
    description: Optional[str] = Field(
        None, 
        max_length=1000,
        example="Daily backup of all core routers at 2am",
        description="Optional job description"
    )
    is_enabled: bool = Field(
        True,
        description="Whether the job is enabled and should be scheduled",
        example=True
    )
    # Schedule fields based on DB model
    schedule_type: Optional[ScheduleTypes] = Field(
        None, 
        description="Type of schedule: 'interval' (seconds between runs), 'cron' (cron expression), or 'onetime' (run once at a specific time)",
        example="interval"
    )
    interval_seconds: Optional[int] = Field(
        None, 
        ge=60,  # Minimum 1 minute
        le=31536000,  # Maximum 1 year
        example=86400,
        description="Seconds between job runs. Required when schedule_type is 'interval'. Minimum 60 seconds."
    )
    cron_string: Optional[str] = Field(
        None, 
        min_length=9,  # At minimum "* * * * *"
        max_length=100,
        example="0 2 * * *",
        description="Cron expression (e.g., '0 2 * * *' for daily at 2am). Required when schedule_type is 'cron'."
    )
    scheduled_for: Optional[datetime] = Field(
        None,
        description="Datetime when the job should run. Required when schedule_type is 'onetime'.",
        example="2025-06-01T02:00:00Z"
    )
    
    @model_validator(mode='after')
    def validate_schedule_fields(self):
        """Validate schedule fields based on schedule_type"""
        if self.schedule_type == "interval" and not self.interval_seconds:
            raise ValueError("interval_seconds is required when schedule_type is 'interval'")
        
        if self.schedule_type == "cron" and not self.cron_string:
            raise ValueError("cron_string is required when schedule_type is 'cron'")
            
        if self.schedule_type == "onetime" and not self.scheduled_for:
            raise ValueError("scheduled_for is required when schedule_type is 'onetime'")
            
        # Validate cron string if provided
        if self.cron_string:
            try:
                croniter(self.cron_string)
            except ValueError as e:
                raise ValueError(f"Invalid cron expression: {e}")
                
        return self

class JobCreate(JobBase):
    tags: Optional[List[int]] = Field(
        None,
        description="List of tag IDs to associate with the job. Devices with these tags will be targeted by the job.",
        example=[1, 2]
    )

class JobUpdate(BaseSchema):
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        pattern=r"^[\w\-\s]+$",
        example="Backup Core Routers Daily",
        description="Job name"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        example="Daily backup of all core routers at 2am",
        description="Job description"
    )
    is_enabled: Optional[bool] = Field(
        None,
        description="Whether the job is enabled and should be scheduled",
        example=True
    )
    schedule_type: Optional[ScheduleTypes] = Field(
        None,
        description="Type of schedule: 'interval', 'cron', or 'onetime'",
        example="interval"
    )
    interval_seconds: Optional[int] = Field(
        None,
        ge=60,
        le=31536000,
        example=86400,
        description="Seconds between job runs"
    )
    cron_string: Optional[str] = Field(
        None,
        min_length=9,
        max_length=100,
        example="0 2 * * *",
        description="Cron expression"
    )
    scheduled_for: Optional[datetime] = Field(
        None,
        description="Datetime when the job should run",
        example="2025-06-01T02:00:00Z"
    )
    tags: Optional[List[int]] = Field(
        None,
        description="List of tag IDs to associate with the job",
        example=[1, 2]
    )
    
    @model_validator(mode='after')
    def validate_schedule_fields(self):
        """Validate that the appropriate schedule fields are provided based on schedule_type"""
        # Skip validation if schedule_type not provided in update
        if self.schedule_type is None:
            return self
            
        # Only validate if schedule fields are being updated
        if self.schedule_type == "interval" and self.interval_seconds is not None and self.interval_seconds < 60:
            raise ValueError("interval_seconds must be at least 60 seconds (1 minute)")
            
        # Validate cron string if provided
        if self.cron_string is not None:
            try:
                croniter(self.cron_string)
            except ValueError as e:
                raise ValueError(f"Invalid cron expression: {e}")
                
        return self

# Response model
class Job(JobBase, BaseSchemaWithId):
    status: str = Field(
        ...,
        description="Current job status (e.g., 'pending', 'running', 'completed', 'failed')",
        example="completed"
    )
    started_at: Optional[datetime] = Field(
        None,
        description="Timestamp when the job started running",
        example="2025-04-09T02:00:00Z"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when the job completed running",
        example="2025-04-09T02:01:35Z"
    )
    tags: List[Tag] = Field(
        default=[],
        description="List of tags associated with the job"
    )

# Paginated response model
PaginatedJobResponse = create_paginated_response(Job)
