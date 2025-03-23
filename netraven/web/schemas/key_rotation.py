"""
Key rotation schemas for the NetRaven web API.

This module defines the Pydantic models used for key rotation API endpoints,
including key creation, activation, rotation, backup, and restoration.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class KeyMetadata(BaseModel):
    """Key metadata information."""
    id: str = Field(..., description="Unique identifier for the key")
    created_at: datetime = Field(..., description="Timestamp when the key was created")
    active: bool = Field(False, description="Whether the key is currently active")
    description: Optional[str] = Field(None, description="Optional description for the key")
    last_used: Optional[datetime] = Field(None, description="Timestamp when the key was last used")


class KeyInfo(BaseModel):
    """Key information without sensitive data."""
    id: str = Field(..., description="Unique identifier for the key")
    created_at: datetime = Field(..., description="Timestamp when the key was created")
    active: bool = Field(False, description="Whether the key is currently active")
    description: Optional[str] = Field(None, description="Optional description for the key")
    last_used: Optional[datetime] = Field(None, description="Timestamp when the key was last used")


class KeyList(BaseModel):
    """List of encryption keys."""
    keys: List[KeyInfo] = Field(..., description="List of key information")
    active_key_id: Optional[str] = Field(None, description="ID of the currently active key")


class KeyCreate(BaseModel):
    """Request model for creating a new key."""
    description: Optional[str] = Field(None, description="Optional description for the key")


class KeyResponse(BaseModel):
    """Response model for key operations."""
    id: str = Field(..., description="Unique identifier for the key")
    created_at: datetime = Field(..., description="Timestamp when the key was created")
    active: bool = Field(False, description="Whether the key is currently active")
    description: Optional[str] = Field(None, description="Optional description for the key")


class KeyActivate(BaseModel):
    """Request model for activating a key."""
    key_id: str = Field(..., description="ID of the key to activate")


class KeyRotate(BaseModel):
    """Request model for key rotation."""
    force: bool = Field(False, description="Whether to force key rotation regardless of schedule")
    description: Optional[str] = Field(None, description="Optional description for the new key")


class KeyRotationResponse(BaseModel):
    """Response model for key rotation."""
    new_key_id: str = Field(..., description="ID of the newly created and activated key")
    previous_key_id: Optional[str] = Field(None, description="ID of the previously active key")
    reencrypted_count: int = Field(0, description="Number of credentials re-encrypted with the new key")
    created_at: datetime = Field(..., description="Timestamp when the new key was created")


class KeyBackupCreate(BaseModel):
    """Request model for creating a key backup."""
    password: str = Field(..., description="Password to encrypt the backup")
    key_ids: Optional[List[str]] = Field(None, description="Optional list of key IDs to include in the backup")


class KeyBackupResponse(BaseModel):
    """Response model for key backup."""
    backup_id: str = Field(..., description="ID of the created backup")
    created_at: datetime = Field(..., description="Timestamp when the backup was created")
    key_count: int = Field(..., description="Number of keys included in the backup")
    includes_active_key: bool = Field(..., description="Whether the backup includes the active key")


class KeyBackupList(BaseModel):
    """List of key backups."""
    backups: List[Dict[str, Any]] = Field(..., description="List of backup information")


class KeyRestore(BaseModel):
    """Request model for restoring keys from a backup."""
    backup_data: str = Field(..., description="Backup data (from a previous backup operation)")
    password: str = Field(..., description="Password used to encrypt the backup")
    activate_key: bool = Field(False, description="Whether to activate the previously active key from the backup")


class KeyRestoreResponse(BaseModel):
    """Response model for key restore."""
    imported_keys: List[str] = Field(..., description="List of imported key IDs")
    activated_key_id: Optional[str] = Field(None, description="ID of the activated key, if any") 