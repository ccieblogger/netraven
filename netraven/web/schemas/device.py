"""
Device schemas for the NetRaven web interface.

This module provides Pydantic models for device-related API requests and responses.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
import ipaddress

class DeviceBase(BaseModel):
    """Base device schema with common attributes."""
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: str = Field(..., max_length=45)
    device_type: str = Field(..., min_length=1, max_length=50)
    port: Optional[int] = Field(22, ge=1, le=65535)
    description: Optional[str] = None
    enabled: Optional[bool] = True
    
    @field_validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate that ip_address is a valid IP address."""
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address')
        return v

class DeviceCreate(DeviceBase):
    """Schema for creating a new device."""
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)

class DeviceUpdate(BaseModel):
    """Schema for updating an existing device."""
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    device_type: Optional[str] = Field(None, min_length=1, max_length=50)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, min_length=1, max_length=64)
    password: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    enabled: Optional[bool] = None
    
    @field_validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate that ip_address is a valid IP address."""
        if v is None:
            return v
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address')
        return v

class Device(DeviceBase):
    """Schema for device information returned by API."""
    id: str
    owner_id: str
    last_backup_at: Optional[datetime] = None
    last_backup_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DeviceWithCredentials(Device):
    """Schema for device information with credentials (for admin use only)."""
    username: str
    password: str

    model_config = ConfigDict(from_attributes=True)

class DeviceBackupResult(BaseModel):
    """Schema for the result of a backup operation."""
    device_id: str
    job_id: str
    status: str
    message: str 