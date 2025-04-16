"""Device schemas for the NetRaven API.

This module defines Pydantic models for device-related API operations, including
creating, updating, and retrieving network devices in the inventory. These schemas
enforce validation rules for device properties and define the structure of
request and response payloads for device endpoints.
"""

from pydantic import Field, IPvAnyAddress, field_validator, model_validator
from datetime import datetime
from typing import Optional, List, Dict
import re

from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from .tag import Tag # Import Tag schema for relationships

# --- Device Schemas ---

class DeviceBase(BaseSchema):
    """Base schema for device data shared by multiple device schemas.
    
    This schema defines the common fields and validation rules for network devices,
    serving as the foundation for more specific device-related schemas. It includes
    essential device information like hostname, IP address, and device type.
    
    Attributes:
        hostname: Unique hostname of the network device
        ip_address: IPv4 or IPv6 address used to connect to the device
        device_type: Type of device, corresponding to Netmiko device types
        description: Optional descriptive text about the device
        port: SSH port number for connecting to the device (defaults to 22)
    """
    hostname: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        pattern=r"^[a-zA-Z0-9][\w\.\-]*$",
        example="core-switch-01",
        description="Device hostname. Must start with alphanumeric character and can contain letters, numbers, periods, hyphens, and underscores."
    )
    ip_address: IPvAnyAddress = Field(
        ...,
        description="IPv4 or IPv6 address of the device",
        example="192.168.1.1"
    )
    device_type: str = Field(
        ..., 
        min_length=2, 
        max_length=50, 
        pattern=r"^[\w\-]+$",
        example="cisco_ios",
        description="Device type following Netmiko naming convention (e.g., cisco_ios, juniper_junos)"
    )
    description: Optional[str] = Field(
        None, 
        max_length=500,
        example="Core Switch in Data Center 1",
        description="Optional description of the device"
    )
    port: Optional[int] = Field(
        default=22, 
        ge=1, 
        le=65535,
        example=22,
        description="SSH port number (default: 22)"
    )

    @field_validator('hostname')
    @classmethod
    def validate_hostname(cls, v):
        """Validate hostname format.
        
        Ensures the hostname follows the required pattern: starts with alphanumeric
        character and can contain letters, numbers, periods, hyphens, and underscores.
        
        Args:
            v: The hostname value to validate
            
        Returns:
            The validated hostname
            
        Raises:
            ValueError: If the hostname doesn't match the required pattern
        """
        if not re.match(r"^[a-zA-Z0-9][\w\.\-]*$", v):
            raise ValueError("Hostname must start with alphanumeric character and can contain letters, numbers, periods, hyphens, and underscores")
        return v
    
    @field_validator('device_type')
    @classmethod
    def validate_device_type(cls, v):
        """Validate device type against supported Netmiko device types.
        
        Ensures the device type is one of the supported values that correspond
        to Netmiko connection types.
        
        Args:
            v: The device_type value to validate
            
        Returns:
            The validated device type
            
        Raises:
            ValueError: If the device type is not in the list of supported types
        """
        valid_device_types = [
            'cisco_ios', 'cisco_xe', 'cisco_nxos', 'cisco_asa', 'cisco_xr',
            'juniper_junos', 'arista_eos', 'hp_comware', 'hp_procurve',
            'huawei', 'fortinet', 'paloalto_panos', 'f5_tmsh',
            'linux', 'dell_os10', 'dell_os6', 'dell_os9'
        ]
        
        if not v or v not in valid_device_types:
            raise ValueError(f"Device type must be one of: {', '.join(valid_device_types)}")
        return v

class DeviceCreate(DeviceBase):
    """Schema for creating a new device.
    
    Extends DeviceBase to include additional fields needed when creating a new device,
    such as tag associations.
    
    Attributes:
        tags: Optional list of tag IDs to associate with the device
    """
    tags: Optional[List[int]] = Field(
        None,
        description="List of tag IDs to associate with the device",
        example=[1, 2]
    )

class DeviceUpdate(BaseSchema):
    """Schema for updating an existing device.
    
    Unlike DeviceCreate, all fields are optional since updates may modify
    only a subset of device properties.
    
    Attributes:
        hostname: Optional updated hostname
        ip_address: Optional updated IP address
        device_type: Optional updated device type
        description: Optional updated description
        port: Optional updated SSH port
        tags: Optional updated list of tag IDs
    """
    hostname: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z0-9][\w\.\-]*$",
        example="core-switch-01",
        description="Device hostname"
    )
    ip_address: Optional[IPvAnyAddress] = Field(
        None,
        description="IPv4 or IPv6 address of the device",
        example="192.168.1.1"
    )
    device_type: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        pattern=r"^[\w\-]+$",
        example="cisco_ios",
        description="Device type following Netmiko naming convention"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        example="Core Switch in Data Center 1",
        description="Description of the device"
    )
    port: Optional[int] = Field(
        None,
        ge=1,
        le=65535,
        example=22,
        description="SSH port number"
    )
    tags: Optional[List[int]] = Field(
        None,
        description="List of tag IDs to associate with the device",
        example=[1, 2]
    )
    
    @field_validator('hostname')
    @classmethod
    def validate_hostname(cls, v):
        """Validate hostname format when provided in an update.
        
        Args:
            v: The hostname value to validate
            
        Returns:
            The validated hostname
            
        Raises:
            ValueError: If the hostname doesn't match the required pattern
        """
        if v is not None and not re.match(r"^[a-zA-Z0-9][\w\.\-]*$", v):
            raise ValueError("Hostname must start with alphanumeric character and can contain letters, numbers, periods, hyphens, and underscores")
        return v
    
    @field_validator('device_type')
    @classmethod
    def validate_device_type(cls, v):
        """Validate device type when provided in an update.
        
        Args:
            v: The device_type value to validate
            
        Returns:
            The validated device type
            
        Raises:
            ValueError: If the device type is not in the list of supported types
        """
        if v is not None:
            valid_device_types = [
                'cisco_ios', 'cisco_xe', 'cisco_nxos', 'cisco_asa', 'cisco_xr',
                'juniper_junos', 'arista_eos', 'hp_comware', 'hp_procurve',
                'huawei', 'fortinet', 'paloalto_panos', 'f5_tmsh',
                'linux', 'dell_os10', 'dell_os6', 'dell_os9'
            ]
            
            if v not in valid_device_types:
                raise ValueError(f"Device type must be one of: {', '.join(valid_device_types)}")
        return v

# Response model
class Device(DeviceBase, BaseSchemaWithId):
    """Complete device schema used for responses.
    
    Extends DeviceBase and includes additional fields available when
    retrieving device information, such as creation time, last seen time,
    and associated tags.
    
    Attributes:
        id: Primary key identifier for the device
        created_at: When the device was first added to the system
        last_seen: When the device was last successfully contacted
        tags: List of Tag objects associated with this device
        matching_credentials_count: Number of credentials that match this device's tags
    """
    created_at: Optional[datetime] = Field(
        None,
        description="Timestamp when the device was created",
        example="2025-04-09T12:34:56.789Z"
    )
    last_seen: Optional[datetime] = Field(
        None,
        description="Timestamp when the device was last contacted successfully",
        example="2025-04-09T12:34:56.789Z"
    )
    tags: List[Tag] = Field(
        default=[],
        description="List of tags associated with the device"
    )
    matching_credentials_count: int = Field(
        0,
        description="Number of credentials matching this device's tags",
        example=2
    )
    # configurations: List[...] # TBD: Add DeviceConfiguration schema later if needed

# Paginated response model
PaginatedDeviceResponse = create_paginated_response(Device)
