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
    """
    Schema for creating a new device.
    
    Either username/password or tag_ids should be provided for authentication.
    If tag_ids are provided, credentials will be retrieved from the credential
    store based on the tags.
    """
    username: Optional[str] = Field(None, min_length=1, max_length=64)
    password: Optional[str] = Field(None, min_length=1, max_length=128)
    tag_ids: Optional[List[str]] = Field(None, description="List of tag IDs to use for credential retrieval")
    
    @field_validator('tag_ids', 'username', 'password')
    def validate_authentication_method(cls, v, info):
        """Validate that either username/password or tag_ids are provided."""
        # We'll check the combined fields during model validation
        return v
    
    @field_validator('tag_ids')
    def validate_tag_ids(cls, v, info):
        """Validate the tag_ids field."""
        # Allow None but not empty list
        if v is not None and len(v) == 0:
            raise ValueError("tag_ids cannot be an empty list")
        return v
    
    model_config = ConfigDict(validate_default=True)
    
    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        """Validate that at least one authentication method is provided."""
        model = super().model_validate(obj, *args, **kwargs)
        
        # Check if at least one authentication method is provided
        has_username_password = model.username is not None and model.password is not None
        has_tag_ids = model.tag_ids is not None and len(model.tag_ids) > 0
        
        if not (has_username_password or has_tag_ids):
            # Create a more informative error message
            raise ValueError(
                "Either username/password or tag_ids must be provided. "
                "If using tag_ids, make sure the tags are associated with credentials."
            )
        
        return model

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
    tag_ids: Optional[List[str]] = Field(None, description="List of tag IDs to use for credential retrieval")
    
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
    serial_number: Optional[str] = None

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