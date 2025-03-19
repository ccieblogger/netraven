"""
Tag schemas for the NetRaven web interface.

This module provides Pydantic models for tag-related API requests and responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class TagBase(BaseModel):
    """Base tag schema with common attributes."""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code (e.g., #FF5733)")

class TagCreate(TagBase):
    """Schema for creating a new tag."""
    pass

class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code (e.g., #FF5733)")

class Tag(TagBase):
    """Schema for tag information returned by API."""
    id: str
    created_at: datetime
    updated_at: datetime
    device_count: Optional[int] = 0  # Number of devices with this tag

    model_config = ConfigDict(from_attributes=True)

class TagWithDevices(Tag):
    """Schema for tag information with device details."""
    devices: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)

# Tag assignment schemas
class TagAssignment(BaseModel):
    """Schema for assigning tags to devices."""
    device_ids: List[str] = Field(..., min_length=1)
    tag_ids: List[str] = Field(..., min_length=1)

class TagRemoval(BaseModel):
    """Schema for removing tags from devices."""
    device_ids: List[str] = Field(..., min_length=1)
    tag_ids: List[str] = Field(..., min_length=1) 