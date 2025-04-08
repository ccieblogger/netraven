from datetime import datetime
from typing import Optional, List
from pydantic import Field

from .base import BaseSchema, BaseSchemaWithId
from .tag import Tag # Import Tag schema for relationships

# --- Job Schemas ---

class JobBase(BaseSchema):
    name: str = Field(..., example="Backup Core Routers Daily")
    description: Optional[str] = None
    is_enabled: Optional[bool] = True
    # Schedule fields based on DB model
    schedule_type: Optional[str] = Field(default=None, example="interval") # 'interval', 'cron', 'onetime'
    interval_seconds: Optional[int] = Field(default=None, example=86400)
    cron_string: Optional[str] = Field(default=None, example="0 2 * * *") # Run daily at 2am
    scheduled_for: Optional[datetime] = None # For onetime runs

class JobCreate(JobBase):
    tags: Optional[List[int]] = None # Associate tags by ID

class JobUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    schedule_type: Optional[str] = None
    interval_seconds: Optional[int] = None
    cron_string: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    tags: Optional[List[int]] = None # Update tags by ID

# Response model
class Job(JobBase, BaseSchemaWithId):
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: List[Tag] = []
