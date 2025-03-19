"""
User schemas for the NetRaven web interface.

This module provides Pydantic models for user-related API requests and responses.
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional, Annotated, Dict, Any, List
from datetime import datetime
import re

# Custom email validator that allows .local domains
class LocalEmailStr(str):
    """Custom email type that allows .local domains."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError('string required')
        
        # Simple regex for email validation that allows .local domains
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-.]+)*$'
        if not re.match(pattern, v):
            raise ValueError('invalid email format')
        
        return v

class NotificationPreferences(BaseModel):
    """User notification preferences."""
    email_notifications: bool = True
    email_on_job_completion: bool = True
    email_on_job_failure: bool = True
    notification_frequency: str = "immediate"  # immediate, hourly, daily

class UserBase(BaseModel):
    """Base user schema with common attributes."""
    username: str = Field(..., min_length=3, max_length=64)
    email: Annotated[str, LocalEmailStr]  # Use our custom validator
    full_name: Optional[str] = Field(None, max_length=120)
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False
    notification_preferences: Optional[NotificationPreferences] = None

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=120)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    notification_preferences: Optional[NotificationPreferences] = None

class UserInDB(UserBase):
    """Schema for user information stored in the database."""
    id: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class User(UserBase):
    """Schema for user information returned by API."""
    id: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ChangePassword(BaseModel):
    """Schema for changing a user's password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('new_password')
    def passwords_must_be_different(cls, v, info):
        """Validate that new password is different from current."""
        current_password = info.data.get('current_password')
        if current_password is not None and v == current_password:
            raise ValueError('New password must be different from current password')
        return v

class UpdateNotificationPreferences(BaseModel):
    """Schema for updating a user's notification preferences."""
    email_notifications: Optional[bool] = None
    email_on_job_completion: Optional[bool] = None
    email_on_job_failure: Optional[bool] = None
    notification_frequency: Optional[str] = None

    @field_validator('notification_frequency')
    def validate_notification_frequency(cls, v):
        """Validate that notification frequency is a valid option."""
        if v is not None and v not in ["immediate", "hourly", "daily"]:
            raise ValueError('Notification frequency must be one of: immediate, hourly, daily')
        return v 