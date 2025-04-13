from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from typing import Optional, List
from pydantic import Field, field_validator, SecretStr
import re

from .tag import Tag # Import Tag schema for relationships

# --- Credential Schemas ---

class CredentialBase(BaseSchema):
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
        """Validate username is not empty"""
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v

class CredentialCreate(CredentialBase):
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
        """Validate password is not empty"""
        if not v.strip():
            raise ValueError("Password cannot be empty")
        # Note: Consider adding more password strength requirements if needed
        return v

class CredentialUpdate(BaseSchema):
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
        """Validate username is not empty if provided"""
        if v is not None and not v.strip():
            raise ValueError("Username cannot be empty")
        return v
        
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password is not empty if provided"""
        if v is not None and not v.strip():
            raise ValueError("Password cannot be empty")
        return v

# Response model, excludes password
class Credential(CredentialBase, BaseSchemaWithId):
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