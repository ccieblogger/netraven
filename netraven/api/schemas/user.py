from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from typing import Optional, Literal
from pydantic import Field, field_validator, EmailStr
import re

# Define valid user roles
UserRole = Literal["admin", "user"]

# --- User Schemas ---

class UserBase(BaseSchema):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_\-\.]+$",
        example="admin_user",
        description="Username for login. Must be 3-50 characters and can contain letters, numbers, underscores, hyphens, and periods."
    )
    email: Optional[EmailStr] = Field(
        None,
        example="user@example.com",
        description="User's email address"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        example="Jane Smith",
        description="User's full name"
    )
    role: UserRole = Field(
        'user',
        description="User role: 'admin' (full access) or 'user' (limited access)",
        example="user"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format"""
        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores, hyphens, and periods")
        return v

class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        example="secureP@ssw0rd",
        description="User password (will be hashed before storage)"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        # Consider adding more password strength checks like requiring numbers, special chars, etc.
        return v

class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = Field(
        None,
        example="new.email@example.com",
        description="User's email address"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        example="Jane Smith",
        description="User's full name"
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=100,
        example="newSecureP@ssw0rd",
        description="User password"
    )
    role: Optional[UserRole] = Field(
        None,
        description="User role: 'admin' or 'user'",
        example="admin"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether the user account is active",
        example=True
    )
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password if provided"""
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class User(UserBase, BaseSchemaWithId):
    is_active: bool = Field(
        ...,
        description="Whether the user account is active",
        example=True
    )

# For displaying in lists, maybe without sensitive info
class UserPublic(BaseSchemaWithId):
    username: str = Field(
        ...,
        example="admin_user",
        description="Username"
    )
    role: UserRole = Field(
        'user',
        description="User role",
        example="user"
    )
    is_active: bool = Field(
        ...,
        description="Account status",
        example=True
    )

# Paginated response models
PaginatedUserResponse = create_paginated_response(User)
PaginatedUserPublicResponse = create_paginated_response(UserPublic)
