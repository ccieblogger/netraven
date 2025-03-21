"""
Credential schemas for the NetRaven web interface.

This module provides Pydantic schemas for credential-related operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class CredentialBase(BaseModel):
    """Base schema for credential data."""
    name: str = Field(..., description="Name of the credential")
    username: str = Field(..., description="Username for the credential")
    description: Optional[str] = Field(None, description="Description of the credential")
    use_keys: bool = Field(False, description="Whether to use key-based authentication")
    key_file: Optional[str] = Field(None, description="Path to the SSH key file")

class CredentialCreate(CredentialBase):
    """Schema for creating a credential."""
    password: Optional[str] = Field(None, description="Password for the credential")
    tags: Optional[List[str]] = Field(None, description="List of tag IDs to associate with the credential")

class CredentialUpdate(BaseModel):
    """Schema for updating a credential."""
    name: Optional[str] = Field(None, description="Name of the credential")
    username: Optional[str] = Field(None, description="Username for the credential")
    password: Optional[str] = Field(None, description="Password for the credential")
    description: Optional[str] = Field(None, description="Description of the credential")
    use_keys: Optional[bool] = Field(None, description="Whether to use key-based authentication")
    key_file: Optional[str] = Field(None, description="Path to the SSH key file")

class CredentialOut(CredentialBase):
    """Schema for credential output."""
    id: str = Field(..., description="ID of the credential")
    success_count: int = Field(0, description="Number of successful authentications")
    failure_count: int = Field(0, description="Number of failed authentication attempts")
    last_used: Optional[datetime] = Field(None, description="Last time the credential was used")
    last_success: Optional[datetime] = Field(None, description="Last time the credential was used successfully")
    last_failure: Optional[datetime] = Field(None, description="Last time the credential failed")
    created_at: datetime = Field(..., description="Time the credential was created")
    updated_at: datetime = Field(..., description="Time the credential was last updated")
    
    # Password is not returned in output
    class Config:
        orm_mode = True

class CredentialTagAssociation(BaseModel):
    """Schema for credential-tag association."""
    credential_id: str = Field(..., description="ID of the credential")
    tag_id: str = Field(..., description="ID of the tag")
    priority: float = Field(0.0, description="Priority of the credential (higher values are tried first)")

class CredentialTagAssociationOut(CredentialTagAssociation):
    """Schema for credential-tag association output."""
    id: str = Field(..., description="ID of the association")
    success_count: int = Field(0, description="Number of successful authentications with this tag")
    failure_count: int = Field(0, description="Number of failed authentication attempts with this tag")
    last_used: Optional[datetime] = Field(None, description="Last time the credential was used with this tag")
    created_at: datetime = Field(..., description="Time the association was created")
    updated_at: datetime = Field(..., description="Time the association was last updated")
    
    class Config:
        orm_mode = True

class CredentialWithTags(CredentialOut):
    """Schema for credential output with associated tags."""
    tags: List[Dict[str, Any]] = Field([], description="List of associated tags with priority information")

class CredentialTest(BaseModel):
    """Schema for testing a credential against a device."""
    device_id: Optional[str] = Field(None, description="ID of the device to test against")
    hostname: Optional[str] = Field(None, description="Hostname/IP of the device to test against")
    device_type: Optional[str] = Field(None, description="Device type (e.g., cisco_ios)")
    port: int = Field(22, description="Port to connect to")

class CredentialTestResult(BaseModel):
    """Schema for credential test results."""
    success: bool = Field(..., description="Whether the test was successful")
    message: str = Field(..., description="Message describing the test result")
    time_taken: float = Field(..., description="Time taken to complete the test in seconds")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Information about the device if available")

class CredentialBulkOperation(BaseModel):
    """Schema for bulk credential operations."""
    credential_ids: List[str] = Field(..., description="List of credential IDs to operate on")
    tag_ids: List[str] = Field(..., description="List of tag IDs for the operation")

class CredentialStats(BaseModel):
    """Schema for credential statistics."""
    total_count: int = Field(..., description="Total number of credentials in the system")
    active_count: int = Field(..., description="Number of credentials used in the last 30 days")
    success_rate: float = Field(..., description="Overall success rate as a percentage")
    failure_rate: float = Field(..., description="Overall failure rate as a percentage")
    
    # Top and poor performers
    top_performers: List[Dict[str, Any]] = Field([], description="List of top performing credentials (highest success rate)")
    poor_performers: List[Dict[str, Any]] = Field([], description="List of poor performing credentials (highest failure rate)")

class TagCredentialStats(BaseModel):
    """Schema for credential statistics for a specific tag."""
    tag_id: str = Field(..., description="ID of the tag")
    total_count: int = Field(..., description="Total number of credentials for this tag")
    active_count: int = Field(..., description="Number of credentials used in the last 30 days")
    success_rate: float = Field(..., description="Overall success rate as a percentage")
    failure_rate: float = Field(..., description="Overall failure rate as a percentage")
    
    # Top and poor performers for this tag
    top_performers: List[Dict[str, Any]] = Field([], description="List of top performing credentials for this tag")
    poor_performers: List[Dict[str, Any]] = Field([], description="List of poor performing credentials for this tag")

class SmartCredentialRequest(BaseModel):
    """Schema for requesting smart credential selection."""
    tag_id: str = Field(..., description="ID of the tag to get credentials for")
    limit: int = Field(5, description="Maximum number of credentials to return")

class SmartCredentialResponse(BaseModel):
    """Schema for smart credential selection response."""
    credentials: List[Dict[str, Any]] = Field(..., description="List of ranked credentials")
    explanation: Dict[str, Any] = Field({}, description="Explanation of the ranking algorithm and factors") 