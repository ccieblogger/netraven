"""
User schemas for the NetRaven web interface.

This module provides Pydantic models for user-related API requests and responses.
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional, Annotated
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

class UserBase(BaseModel):
    """Base user schema with common attributes."""
    username: str = Field(..., min_length=3, max_length=64)
    email: Annotated[str, LocalEmailStr]  # Use our custom validator
    full_name: Optional[str] = Field(None, max_length=120)
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False

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