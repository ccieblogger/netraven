"""
Pydantic models for the Device Gateway API.

This module defines the data models used for API requests and responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Optional, List, Any, Union


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str


class TokenRequest(BaseModel):
    """Token request model."""
    api_key: str = Field(..., description="API key for authentication")


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int


class DeviceConnectionRequest(BaseModel):
    """Device connection request model."""
    host: str = Field(..., description="Hostname or IP address of the device")
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication")
    device_type: str = Field(..., description="Type of device (e.g., cisco_ios, juniper)")
    port: int = Field(22, description="SSH port number")
    use_keys: bool = Field(False, description="Whether to use SSH keys for authentication")
    key_file: Optional[str] = Field(None, description="Path to SSH key file")
    timeout: int = Field(60, description="Connection timeout in seconds")
    
    @validator('device_type')
    def validate_device_type(cls, v):
        """Validate device type."""
        valid_types = ['cisco_ios', 'cisco_nxos', 'juniper', 'arista_eos', 'generic']
        if v not in valid_types:
            raise ValueError(f"Device type must be one of: {', '.join(valid_types)}")
        return v


class DeviceCommandRequest(DeviceConnectionRequest):
    """Device command request model."""
    command: str = Field(..., description="Command to execute on the device")
    
    @validator('command')
    def validate_command(cls, v):
        """Validate command."""
        valid_commands = ['get_running_config', 'get_serial_number', 'get_os_info']
        if v not in valid_commands:
            raise ValueError(f"Command must be one of: {', '.join(valid_commands)}")
        return v


class DeviceResponse(BaseModel):
    """Device response model."""
    status: str = Field(..., description="Status of the operation (success or error)")
    message: str = Field(..., description="Message describing the result")
    data: Optional[Any] = Field(None, description="Response data, if any")


class DeviceBackupRequest(BaseModel):
    """Device backup request model."""
    host: str
    username: str
    password: str
    device_type: Optional[str] = None
    port: int = 22
    use_keys: bool = False
    key_file: Optional[str] = None
    timeout: int = 60
    device_id: Optional[str] = None
    storage_path: Optional[str] = None 