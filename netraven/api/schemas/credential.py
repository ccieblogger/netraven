"""Credential schemas for the NetRaven API.

This module defines Pydantic models for credential-related API operations, including
creating, updating, and retrieving network device authentication credentials. These
schemas enforce validation rules and security practices for handling sensitive
authentication information.
"""

from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from typing import Optional, List
from pydantic import Field, field_validator, SecretStr
import re

from .tag import Tag # Import Tag schema for relationships

# --- Credential Schemas ---

class CredentialBase(BaseSchema):
    """Base schema for credential data shared by multiple credential schemas.
    
    This schema defines the common fields and validation rules for authentication
    credentials, excluding sensitive data like passwords that are handled
    in specific child schemas.
    
    Attributes:
        username: Username for device authentication
        priority: Order of precedence when multiple credentials match a device
        description: Optional description for the credential set
    """
    username: str = Field(
        ...,
        min_length=1,
        max_length=255,
        example="admin",
        description="Username for authentication to network devices"
    )
    # Password will be write-only, not included in response models
    priority: int = Field(
        100,
        ge=1,
        le=1000,
        description="Priority of the credential (lower numbers are higher priority). When multiple credentials match a device via tags, the highest priority one will be used.",
        example=100
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        example="Admin credentials for core network devices",
        description="Optional description for the credential set"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username is not empty.
        
        Args:
            v: The username value to validate
            
        Returns:
            The validated username
            
        Raises:
            ValueError: If the username is empty or contains only whitespace
        """
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v

class CredentialCreate(CredentialBase):
    """Schema for creating a new credential.
    
    Extends CredentialBase to include password and tag associations
    needed when creating a new credential.
    
    Attributes:
        password: Password for device authentication
        tags: Optional list of tag IDs to associate with the credential
    """
    password: str = Field(
        ...,
        min_length=1,
        max_length=255,
        example="secureP@ssw0rd",
        description="Password for authentication (will be stored securely)"
    )
    tags: Optional[List[int]] = Field(
        None,
        description="List of tag IDs to associate with this credential. Devices with matching tags will use this credential.",
        example=[1, 2]
    )
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password is not empty.
        
        Args:
            v: The password value to validate
            
        Returns:
            The validated password
            
        Raises:
            ValueError: If the password is empty or contains only whitespace
        """
        if not v.strip():
            raise ValueError("Password cannot be empty")
        # Note: Consider adding more password strength requirements if needed
        return v

class CredentialUpdate(BaseSchema):
    """Schema for updating an existing credential.
    
    Unlike CredentialCreate, all fields are optional since updates may modify
    only a subset of credential properties.
    
    Attributes:
        username: Optional updated username
        password: Optional updated password
        priority: Optional updated priority
        description: Optional updated description
        tags: Optional updated list of tag IDs
    """
    username: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        example="admin",
        description="Username for authentication"
    )
    password: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        example="newSecureP@ssw0rd",
        description="Password for authentication (will be stored securely)"
    )
    priority: Optional[int] = Field(
        None,
        ge=1,
        le=1000,
        example=100,
        description="Priority of the credential"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        example="Admin credentials for core network devices",
        description="Description for the credential set"
    )
    tags: Optional[List[int]] = Field(
        None,
        description="List of tag IDs to associate with this credential",
        example=[1, 2]
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username is not empty if provided in an update.
        
        Args:
            v: The username value to validate
            
        Returns:
            The validated username
            
        Raises:
            ValueError: If the username is empty or contains only whitespace
        """
        if v is not None and not v.strip():
            raise ValueError("Username cannot be empty")
        return v
        
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password is not empty if provided in an update.
        
        Args:
            v: The password value to validate
            
        Returns:
            The validated password
            
        Raises:
            ValueError: If the password is empty or contains only whitespace
        """
        if v is not None and not v.strip():
            raise ValueError("Password cannot be empty")
        return v

# Response model, excludes password
class Credential(CredentialBase, BaseSchemaWithId):
    """Complete credential schema used for responses.
    
    Extends CredentialBase and includes additional fields available when
    retrieving credential information. Notably, this schema does NOT include
    the password field, as passwords should never be returned in responses.
    
    Attributes:
        id: Primary key identifier for the credential
        is_system: Whether this is a system-managed credential
        tags: List of Tag objects associated with this credential
    """
    is_system: bool = Field(
        default=False,
        description="Whether this is a system credential (cannot be deleted)"
    )
    tags: List[Tag] = Field(
        default=[],
        description="List of tags associated with this credential"
    )

# Paginated response model
PaginatedCredentialResponse = create_paginated_response(Credential) 