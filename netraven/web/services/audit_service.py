"""
Audit Logging Service for NetRaven.

This service provides a centralized way to log security and operational events
to the audit log for compliance and security monitoring.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from fastapi import Request

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from netraven.core.logging import get_logger
from netraven.web.models.audit_log import AuditLog
from netraven.web.schemas.audit_log import AuditLogCreate, AuditLogFilter


logger = get_logger("netraven.web.services.audit")


class AuditService:
    """
    Service for managing audit log entries.
    
    This service provides methods for creating and querying audit log entries,
    with support for filtering and pagination.
    """
    
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        event_name: str,
        actor_id: Optional[str] = None,
        actor_type: Optional[str] = None,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Log an event to the audit log.
        
        Args:
            db: Database session
            event_type: Type of event (auth, admin, key, data)
            event_name: Specific event name (login, logout, etc.)
            actor_id: ID of the user or service that performed the action
            actor_type: Type of actor (user, service, system)
            target_id: ID of the resource being acted upon
            target_type: Type of target resource
            description: Description of the event
            status: Status of the event (success, failure, error)
            metadata: Additional metadata about the event
            request: Request object for extracting IP and user agent
            
        Returns:
            The created audit log entry
        """
        # Extract request information if available
        ip_address = None
        user_agent = None
        session_id = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("User-Agent")
            # Try to extract session ID from cookies or headers
            session_id = (
                request.cookies.get("session") or 
                request.headers.get("X-Session-ID")
            )
        
        # Create audit log entry
        audit_log_data = AuditLogCreate(
            event_type=event_type,
            event_name=event_name,
            actor_id=actor_id,
            actor_type=actor_type,
            target_id=target_id,
            target_type=target_type,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            description=description,
            status=status,
            metadata=metadata
        )
        
        # Create DB model instance
        audit_log = AuditLog(
            event_type=audit_log_data.event_type,
            event_name=audit_log_data.event_name,
            actor_id=audit_log_data.actor_id,
            actor_type=audit_log_data.actor_type,
            target_id=audit_log_data.target_id,
            target_type=audit_log_data.target_type,
            ip_address=audit_log_data.ip_address,
            user_agent=audit_log_data.user_agent,
            session_id=audit_log_data.session_id,
            description=audit_log_data.description,
            status=audit_log_data.status,
            metadata=audit_log_data.metadata
        )
        
        # Save to database
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        # Also log to application logs for immediate visibility
        log_message = f"AUDIT: {event_type}:{event_name} by {actor_id}"
        if status != "success":
            logger.warning(f"{log_message} - {status.upper()}: {description}")
        else:
            logger.info(f"{log_message}: {description}")
            
        return audit_log
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        filter_params: Optional[AuditLogFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get audit log entries with filtering and pagination.
        
        Args:
            db: Database session
            filter_params: Filter parameters for querying logs
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with items (list of logs) and total count
        """
        query = db.query(AuditLog)
        
        # Apply filters if provided
        if filter_params:
            filters = []
            
            if filter_params.event_type:
                filters.append(AuditLog.event_type == filter_params.event_type)
                
            if filter_params.event_name:
                filters.append(AuditLog.event_name == filter_params.event_name)
                
            if filter_params.actor_id:
                filters.append(AuditLog.actor_id == filter_params.actor_id)
                
            if filter_params.target_id:
                filters.append(AuditLog.target_id == filter_params.target_id)
                
            if filter_params.status:
                filters.append(AuditLog.status == filter_params.status)
                
            if filter_params.start_date:
                filters.append(AuditLog.created_at >= filter_params.start_date)
                
            if filter_params.end_date:
                filters.append(AuditLog.created_at <= filter_params.end_date)
                
            if filters:
                query = query.filter(and_(*filters))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply sorting and pagination
        query = (
            query
            .order_by(desc(AuditLog.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        # Execute query
        items = query.all()
        
        return {
            "items": items,
            "total": total
        }
    
    @staticmethod
    def get_audit_log_by_id(db: Session, audit_log_id: str) -> Optional[AuditLog]:
        """
        Get an audit log entry by ID.
        
        Args:
            db: Database session
            audit_log_id: ID of the audit log entry
            
        Returns:
            The audit log entry if found, None otherwise
        """
        return db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
    
    # Shortcut methods for common audit events
    
    @classmethod
    def log_auth_event(
        cls,
        db: Session,
        event_name: str,
        actor_id: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log an authentication event."""
        return cls.log_event(
            db=db,
            event_type="auth",
            event_name=event_name,
            actor_id=actor_id,
            actor_type="user",
            description=description,
            status=status,
            metadata=metadata,
            request=request
        )
    
    @classmethod
    def log_admin_event(
        cls,
        db: Session,
        event_name: str,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log an admin action event."""
        return cls.log_event(
            db=db,
            event_type="admin",
            event_name=event_name,
            actor_id=actor_id,
            actor_type="user",
            target_id=target_id,
            target_type=target_type,
            description=description,
            status=status,
            metadata=metadata,
            request=request
        )
    
    @classmethod
    def log_key_event(
        cls,
        db: Session,
        event_name: str,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log a key management event."""
        return cls.log_event(
            db=db,
            event_type="key",
            event_name=event_name,
            actor_id=actor_id,
            actor_type="user",
            target_id=target_id,
            target_type="key",
            description=description,
            status=status,
            metadata=metadata,
            request=request
        )
    
    @classmethod
    def log_data_event(
        cls,
        db: Session,
        event_name: str,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log a data access or modification event."""
        return cls.log_event(
            db=db,
            event_type="data",
            event_name=event_name,
            actor_id=actor_id,
            actor_type="user",
            target_id=target_id,
            target_type=target_type,
            description=description,
            status=status,
            metadata=metadata,
            request=request
        ) 