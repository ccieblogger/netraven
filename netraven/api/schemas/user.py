"""User schemas for the NetRaven API.

This module defines Pydantic models for user-related API operations, including
user creation, authentication, and management. These schemas enforce validation
rules for user properties and define the structure of request and response
payloads for user endpoints.
"""

from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from typing import Optional, Literal
from pydantic import Field, field_validator, EmailStr
import re

# Define valid user roles
UserRole = Literal["admin", "user"]
"""Type definition for valid user roles in the system.

Only "admin" and "user" are valid roles, with different permission levels.
"""

# --- User Schemas ---

class UserBase(BaseSchema):
    """Base schema for user data shared by multiple user schemas.
    
    This schema defines the common fields and validation rules for users,
    serving as the foundation for more specific user-related schemas.
    
    Attributes:
        username: Unique username for login
        email: Optional email address
        full_name: Optional full name
        role: User's role determining permissions
    """
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
        """Validate username format.
        
        Ensures the username follows the required pattern: can only contain 
        letters, numbers, underscores, hyphens, and periods.
        
        Args:
            v: The username value to validate
            
        Returns:
            The validated username
            
        Raises:
            ValueError: If the username doesn't match the required pattern
        """
        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores, hyphens, and periods")
        return v

class UserCreate(UserBase):
    """Schema for creating a new user.
    
    Extends UserBase to include password needed when creating a new user account.
    
    Attributes:
        password: Password for authentication (will be hashed before storage)
    """
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
        """Validate password strength.
        
        Ensures the password meets minimum security requirements.
        
        Args:
            v: The password value to validate
            
        Returns:
            The validated password
            
        Raises:
            ValueError: If the password doesn't meet strength requirements
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        # Consider adding more password strength checks like requiring numbers, special chars, etc.
        return v

class UserUpdate(BaseSchema):
    """Schema for updating an existing user.
    
    Unlike UserCreate, all fields are optional since updates may modify
    only a subset of user properties.
    
    Attributes:
        email: Optional updated email address
        full_name: Optional updated full name
        password: Optional updated password
        role: Optional updated role
        is_active: Optional updated account status
    """
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
        """Validate password if provided in an update.
        
        Args:
            v: The password value to validate
            
        Returns:
            The validated password
            
        Raises:
            ValueError: If the password doesn't meet strength requirements
        """
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class User(UserBase, BaseSchemaWithId):
    """Complete user schema used for responses.
    
    Extends UserBase and includes additional fields like ID and active status.
    This schema is used when returning user information to API clients.
    
    Attributes:
        id: Primary key identifier for the user
        is_active: Whether the user account is currently active
    """
    is_active: bool = Field(
        ...,
        description="Whether the user account is active",
        example=True
    )

# For displaying in lists, maybe without sensitive info
class UserPublic(BaseSchemaWithId):
    """Public user information schema.
    
    A limited subset of user information suitable for public display,
    omitting private or sensitive fields.
    
    Attributes:
        id: Primary key identifier for the user
        username: User's login name
        role: User's role/permission level
        is_active: Whether the user account is active
    """
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
