"""
Database models for audit logs in the NetRaven system.

This module defines SQLAlchemy models for audit log entries, which are used to track
security and operational events throughout the application.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import Column, String, DateTime, Text, Index, JSON
from sqlalchemy.dialects.postgresql import UUID

from netraven.web.database import Base


class AuditLog(Base):
    """SQLAlchemy model for audit log entries."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(32), nullable=False, 
                         comment="Type of event (auth, admin, key, data)")
    event_name = Column(String(64), nullable=False, 
                         comment="Specific event name (login, update, etc.)")
    actor_id = Column(String(255), nullable=True, 
                       comment="ID of the user or system component that initiated the action")
    actor_type = Column(String(32), nullable=True, 
                        comment="Type of actor (user, system, service)")
    target_id = Column(String(255), nullable=True, 
                        comment="ID of the resource being acted upon")
    target_type = Column(String(32), nullable=True, 
                         comment="Type of target resource (user, device, backup, etc.)")
    ip_address = Column(String(45), nullable=True, 
                         comment="IP address of the client")
    user_agent = Column(Text, nullable=True, 
                         comment="User agent of the client")
    session_id = Column(String(64), nullable=True, 
                         comment="Session ID for the request")
    description = Column(Text, nullable=False, 
                          comment="Human-readable description of the event")
    status = Column(String(16), nullable=False, 
                     comment="Outcome status (success, failure, error, warning)")
    event_metadata = Column(JSON, nullable=True, 
                       comment="Additional structured data about the event")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, 
                         comment="Timestamp when the event was logged")
    
    # Add indexes for common queries
    __table_args__ = (
        # Index for searching by event type and name
        Index("ix_audit_logs_event_type_name", "event_type", "event_name"),
        
        # Index for searching by actor and target
        Index("ix_audit_logs_actor_target", "actor_id", "target_id"),
        
        # Index for searching by status and date range
        Index("ix_audit_logs_status_created", "status", "created_at"),
    )
    
    def __repr__(self) -> str:
        """String representation of the audit log entry."""
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', event_name='{self.event_name}', created_at='{self.created_at}')>"
    
    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> "AuditLog":
        """Create an audit log entry from a dictionary."""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the audit log entry to a dictionary."""
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "event_name": self.event_name,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "description": self.description,
            "status": self.status,
            "metadata": self.event_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        } 