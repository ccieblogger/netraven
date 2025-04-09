from pydantic import Field, IPvAnyAddress
from datetime import datetime
from typing import Optional, List

from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from .tag import Tag # Import Tag schema for relationships

# --- Device Schemas ---

class DeviceBase(BaseSchema):
    hostname: str = Field(..., example="core-switch-01")
    ip_address: IPvAnyAddress # Use IPvAnyAddress for validation
    device_type: str = Field(..., example="cisco_ios") # Match netmiko types
    description: Optional[str] = None
    port: Optional[int] = Field(default=22, example=22)

class DeviceCreate(DeviceBase):
    tags: Optional[List[int]] = None # Associate tags by ID on create

class DeviceUpdate(BaseSchema):
    hostname: Optional[str] = None
    ip_address: Optional[IPvAnyAddress] = None
    device_type: Optional[str] = None
    description: Optional[str] = None
    port: Optional[int] = None
    tags: Optional[List[int]] = None # Update tags by ID

# Response model
class Device(DeviceBase, BaseSchemaWithId):
    last_seen: Optional[datetime] = None
    tags: List[Tag] = []
    # configurations: List[...] # TBD: Add DeviceConfiguration schema later if needed

# Paginated response model
PaginatedDeviceResponse = create_paginated_response(Device)
