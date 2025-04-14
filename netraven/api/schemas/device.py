from pydantic import Field, IPvAnyAddress, field_validator, model_validator
from datetime import datetime
from typing import Optional, List, Dict
import re

from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from .tag import Tag # Import Tag schema for relationships

# --- Device Schemas ---

class DeviceBase(BaseSchema):
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
        """Validate hostname format"""
        if not re.match(r"^[a-zA-Z0-9][\w\.\-]*$", v):
            raise ValueError("Hostname must start with alphanumeric character and can contain letters, numbers, periods, hyphens, and underscores")
        return v
    
    @field_validator('device_type')
    @classmethod
    def validate_device_type(cls, v):
        """Validate device type format"""
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
    tags: Optional[List[int]] = Field(
        None,
        description="List of tag IDs to associate with the device",
        example=[1, 2]
    )

class DeviceUpdate(BaseSchema):
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
        if v is not None and not re.match(r"^[a-zA-Z0-9][\w\.\-]*$", v):
            raise ValueError("Hostname must start with alphanumeric character and can contain letters, numbers, periods, hyphens, and underscores")
        return v
    
    @field_validator('device_type')
    @classmethod
    def validate_device_type(cls, v):
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
    # configurations: List[...] # TBD: Add DeviceConfiguration schema later if needed

# Paginated response model
PaginatedDeviceResponse = create_paginated_response(Device)
