"""
Schemas for audit log events in the NetRaven system.

This module defines Pydantic models for audit log entries, which are used to track
security and operational events throughout the application.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogBase(BaseModel):
    """Base schema for audit log entries."""
    event_type: str = Field(..., description="Type of event (auth, admin, key, data)")
    event_name: str = Field(..., description="Specific event name (login, update, etc.)")
    description: str = Field(..., description="Human-readable description of the event")
    status: str = Field(..., description="Outcome status (success, failure, error, warning)")
    
    # Actor information
    actor_id: Optional[str] = Field(None, description="ID of the user or system component that initiated the action")
    actor_type: Optional[str] = Field(None, description="Type of actor (user, system, service)")
    
    # Target information (optional)
    target_id: Optional[str] = Field(None, description="ID of the resource being acted upon")
    target_type: Optional[str] = Field(None, description="Type of target resource (user, device, backup, etc.)")
    
    # Request information (optional)
    ip_address: Optional[str] = Field(None, description="IP address of the client")
    user_agent: Optional[str] = Field(None, description="User agent of the client")
    session_id: Optional[str] = Field(None, description="Session ID for the request")
    
    # Additional data
    event_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional structured data about the event")


class AuditLogCreate(AuditLogBase):
    """Schema for creating a new audit log entry."""
    pass


class AuditLogInDB(AuditLogBase):
    """Schema for an audit log entry as stored in the database."""
    id: UUID = Field(..., description="Unique identifier for the audit log entry")
    created_at: datetime = Field(..., description="Timestamp when the event was logged")

    class Config:
        orm_mode = True


class AuditLogResponse(AuditLogInDB):
    """Schema for returning an audit log entry in API responses."""
    pass


class AuditLogFilter(BaseModel):
    """Schema for filtering audit log entries."""
    event_type: Optional[str] = Field(None, description="Filter by event type")
    event_name: Optional[str] = Field(None, description="Filter by event name")
    actor_id: Optional[str] = Field(None, description="Filter by actor ID")
    target_id: Optional[str] = Field(None, description="Filter by target ID")
    status: Optional[str] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Filter for events after this date")
    end_date: Optional[datetime] = Field(None, description="Filter for events before this date")


class AuditLogList(BaseModel):
    """Schema for returning a list of audit log entries."""
    items: List[AuditLogResponse]
    total: int = Field(..., description="Total number of items matching the query") 