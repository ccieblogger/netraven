"""
Backup schemas for the NetRaven web interface.

This module provides Pydantic models for backup-related API requests and responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class BackupBase(BaseModel):
    """Base backup schema with common attributes."""
    version: str = Field(..., min_length=1, max_length=20)
    status: str = Field(..., min_length=1, max_length=20)
    file_path: str = Field(..., min_length=1, max_length=512)
    file_size: int = Field(..., ge=0)
    comment: Optional[str] = None
    is_automatic: Optional[bool] = True

class BackupCreate(BackupBase):
    """Schema for creating a new backup."""
    device_id: str = Field(..., min_length=36, max_length=36)

class Backup(BackupBase):
    """Schema for backup information returned by API."""
    id: str
    device_id: str
    created_at: datetime
    content_hash: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class BackupWithDevice(Backup):
    """Schema for backup information with device details."""
    device_hostname: str
    device_ip: str

    model_config = ConfigDict(from_attributes=True)

class BackupContent(BaseModel):
    """Schema for backup content."""
    id: str
    device_id: str
    device_hostname: str
    content: str
    created_at: datetime

class BackupDiffRequest(BaseModel):
    """Schema for requesting a diff between two backups."""
    backup1_id: str = Field(..., min_length=36, max_length=36)
    backup2_id: str = Field(..., min_length=36, max_length=36)

class BackupDiffResponse(BaseModel):
    """Schema for the result of a diff operation."""
    backup1_id: str
    backup2_id: str
    backup1_created_at: datetime
    backup2_created_at: datetime
    backup1_device: str
    backup2_device: str
    differences: List[Dict[str, Any]] 