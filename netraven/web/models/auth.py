"""
Authentication models for NetRaven web API.

This module contains Pydantic models for authentication entities
like User and ServiceAccount.
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime


class User(BaseModel):
    """User model for authentication."""
    
    username: str = Field(..., description="Username for login")
    email: str = Field(..., description="User email address")
    permissions: List[str] = Field(default_factory=list, description="Permission scopes")
    is_active: bool = Field(default=True, description="Whether the user is active")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "username": "admin",
                "email": "admin@example.com",
                "permissions": ["admin:*"],
                "is_active": True
            }
        }
    )


class ServiceAccount(BaseModel):
    """Service account model for machine-to-machine authentication."""
    
    name: str = Field(..., description="Service account name")
    permissions: List[str] = Field(default_factory=list, description="Permission scopes")
    is_active: bool = Field(default=True, description="Whether the service account is active")
    description: Optional[str] = Field(None, description="Description of the service account")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "monitoring-service",
                "permissions": ["read:metrics", "read:logs"],
                "is_active": True,
                "description": "Service account for monitoring system"
            }
        }
    )


class TokenRequest(BaseModel):
    """Request model for token issuance."""
    
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "password"
            }
        }
    )


class TokenResponse(BaseModel):
    """Response model for token issuance."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_at": "2023-06-01T12:00:00Z"
            }
        }
    )


class ServiceTokenRequest(BaseModel):
    """Request model for service token creation."""
    
    service_name: str = Field(..., description="Service account name")
    scopes: List[str] = Field(..., description="Permission scopes")
    description: Optional[str] = Field(None, description="Description of the token")
    expires_in_days: Optional[int] = Field(None, description="Days until token expiration (null for non-expiring)")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "service_name": "monitoring-service",
                "scopes": ["read:metrics", "read:logs"],
                "description": "Monitoring service token",
                "expires_in_days": 30
            }
        }
    )


class TokenMetadata(BaseModel):
    """Model for token metadata."""
    
    token_id: str = Field(..., description="Unique token identifier (jti)")
    subject: str = Field(..., description="Token subject (username or service name)")
    token_type: str = Field(..., description="Token type (user or service)")
    created_at: datetime = Field(..., description="Token creation time")
    created_by: Optional[str] = Field(None, description="User who created the token")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "token_id": "550e8400-e29b-41d4-a716-446655440000",
                "subject": "monitoring-service",
                "token_type": "service",
                "created_at": "2023-05-01T12:00:00Z",
                "created_by": "admin",
                "expires_at": "2023-06-01T12:00:00Z"
            }
        }
    ) 