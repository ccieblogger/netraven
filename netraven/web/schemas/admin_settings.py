"""
Pydantic schemas for admin settings.

These schemas define the data validation and serialization for admin settings
used in the API endpoints and frontend components.
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID


class AdminSettingBase(BaseModel):
    """Base class for admin setting schemas."""
    key: str = Field(..., description="Unique identifier for the setting")
    value: Optional[Any] = Field(None, description="Value of the setting")
    value_type: str = Field(..., description="Type of value (string, number, boolean, json)")
    category: str = Field(..., description="Category of setting (security, system, notification)")
    description: Optional[str] = Field(None, description="Description of the setting")
    is_required: bool = Field(False, description="Whether the setting is required")
    is_sensitive: bool = Field(False, description="Whether the setting contains sensitive data")
    display_order: int = Field(0, description="Display order in the UI")


class AdminSettingCreate(AdminSettingBase):
    """Schema for creating a new admin setting."""
    pass


class AdminSettingUpdate(BaseModel):
    """Schema for updating an existing admin setting."""
    value: Optional[Any] = Field(None, description="Value of the setting")
    description: Optional[str] = Field(None, description="Description of the setting")
    is_required: Optional[bool] = Field(None, description="Whether the setting is required")
    is_sensitive: Optional[bool] = Field(None, description="Whether the setting contains sensitive data")
    display_order: Optional[int] = Field(None, description="Display order in the UI")


class AdminSettingOut(AdminSettingBase):
    """Schema for returning an admin setting."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class AdminSettingsByCategoryOut(BaseModel):
    """Schema for returning admin settings grouped by category."""
    security: List[AdminSettingOut] = Field([], description="Security settings")
    system: List[AdminSettingOut] = Field([], description="System settings")
    notification: List[AdminSettingOut] = Field([], description="Notification settings")
    
    class Config:
        orm_mode = True


class AdminSettingValueUpdate(BaseModel):
    """Schema for updating just the value of an admin setting."""
    value: Any = Field(..., description="New value for the setting")


class AdminSettingSearch(BaseModel):
    """Schema for searching admin settings."""
    category: Optional[str] = Field(None, description="Filter by category")
    key_contains: Optional[str] = Field(None, description="Filter by key containing this string")
    page: int = Field(1, description="Page number")
    page_size: int = Field(50, description="Number of items per page")


class AdminSettingListOut(BaseModel):
    """Schema for returning a paginated list of admin settings."""
    items: List[AdminSettingOut]
    total: int
    page: int
    page_size: int
    pages: int
    
    class Config:
        orm_mode = True 