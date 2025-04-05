"""
Audit Logging Service for NetRaven.

This service provides a centralized way to log security and operational events
to the audit log for compliance and security monitoring.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from fastapi import Request
import logging # Use standard logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, func, select, and_, or_ # Import select for async queries

from netraven.core.logging import get_logger
from netraven.web.models.audit_log import AuditLog
from netraven.web.schemas.audit_log import AuditLogCreate, AuditLogFilter


logger = get_logger("netraven.web.services.audit")
# Use standard logger for general info/errors within the service
service_logger = logging.getLogger(__name__)


class AsyncAuditService:
    """
    Asynchronous service for managing audit log entries.
    
    This service provides methods for creating and querying audit log entries,
    with support for filtering and pagination using an AsyncSession.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize the service with an async database session."""
        self.db = db
    
    async def log_event(
        self,
        event_type: str,
        event_name: str,
        actor_id: Optional[str] = None,
        actor_type: Optional[str] = None,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "success",
        event_metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Log an event to the audit log asynchronously.
        
        Args:
            event_type: Type of event (auth, admin, key, data)
            event_name: Specific event name (login, logout, etc.)
            actor_id: ID of the user or system component that initiated the action
            actor_type: Type of actor (user, system, service)
            target_id: ID of the resource being acted upon
            target_type: Type of target resource (user, device, backup, etc.)
            description: Human-readable description of the event
            status: Outcome status (success, failure, error, warning)
            event_metadata: Additional structured data about the event
            request: FastAPI request object, used to extract client IP and user agent
            
        Returns:
            The created AuditLog entry
        """
        # Extract request information if available
        ip_address = None
        user_agent = None
        session_id = None
        
        if request:
            client = request.client
            if client:
                ip_address = client.host
                
            user_agent = request.headers.get("User-Agent")
            
            # Extract session ID from cookies or headers if implemented
            # session_id = request.cookies.get("session_id")
        
        # Create a friendly default description if none provided
        if not description:
            actor_str = f"User {actor_id}" if actor_id else "System"
            target_str = f" {target_type} {target_id}" if target_id else ""
            description = f"{actor_str} performed {event_name} on{target_str}."
        
        # Create the audit log entry
        audit_log = AuditLog(
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
            event_metadata=event_metadata,
            created_at=datetime.utcnow()
        )
        
        # Save to database asynchronously
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        
        # Also log to application logs for immediate visibility
        log_message = f"AUDIT: {event_type}:{event_name} by {actor_id}"
        if status != "success":
            service_logger.warning(f"{log_message} - {status.upper()}: {description}")
        else:
            service_logger.info(f"{log_message}: {description}")
            
        return audit_log
    
    async def get_audit_logs(
        self,
        filter_params: Optional[AuditLogFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get audit log entries with filtering and pagination asynchronously.
        
        Args:
            filter_params: Filter parameters for querying logs
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with items (list of logs) and total count
        """
        # Base query using select() for async execution
        stmt = select(AuditLog)
        
        # Apply filters if provided
        if filter_params:
            filters = []
            
            if filter_params.event_type:
                filters.append(AuditLog.event_type == filter_params.event_type)
                stmt = stmt.where(AuditLog.event_type == filter_params.event_type)
                
            if filter_params.event_name:
                filters.append(AuditLog.event_name == filter_params.event_name)
                stmt = stmt.where(AuditLog.event_name == filter_params.event_name)
                
            if filter_params.actor_id:
                filters.append(AuditLog.actor_id == filter_params.actor_id)
                stmt = stmt.where(AuditLog.actor_id == filter_params.actor_id)
                
            if filter_params.target_id:
                filters.append(AuditLog.target_id == filter_params.target_id)
                stmt = stmt.where(AuditLog.target_id == filter_params.target_id)
                
            if filter_params.status:
                filters.append(AuditLog.status == filter_params.status)
                stmt = stmt.where(AuditLog.status == filter_params.status)
                
            if filter_params.start_date:
                filters.append(AuditLog.created_at >= filter_params.start_date)
                stmt = stmt.where(AuditLog.created_at >= filter_params.start_date)
                
            if filter_params.end_date:
                filters.append(AuditLog.created_at <= filter_params.end_date)
                stmt = stmt.where(AuditLog.created_at <= filter_params.end_date)
                
            if filters:
                stmt = stmt.filter(and_(*filters))
        
        # Get total count for pagination before applying limit/offset
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()
        
        # Apply sorting, offset, and limit to the main query
        stmt = (
            stmt
            .order_by(desc(AuditLog.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        # Execute query
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def get_audit_log_by_id(self, audit_log_id: str) -> Optional[AuditLog]:
        """
        Get an audit log entry by ID.
        
        Args:
            audit_log_id: ID of the audit log entry
            
        Returns:
            The audit log entry if found, None otherwise
        """
        stmt = select(AuditLog).where(AuditLog.id == audit_log_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    # Shortcut methods for common audit events
    
    async def log_auth_event(
        self,
        event_name: str,
        actor_id: Optional[str] = None,
        actor_type: str = "user",
        description: Optional[str] = None,
        status: str = "success",
        event_metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Log an authentication event.
        
        Args:
            event_name: Authentication event (login, logout, password_change, etc.)
            actor_id: User ID or service name
            actor_type: Type of actor (user, service, system)
            description: Description of the event
            status: Outcome status (success, failure)
            event_metadata: Additional data about the event
            request: FastAPI request object
            
        Returns:
            The created audit log entry
        """
        return await self.log_event(
            event_type="auth",
            event_name=event_name,
            actor_id=actor_id,
            actor_type=actor_type,
            description=description,
            status=status,
            event_metadata=event_metadata,
            request=request
        )
    
    async def log_admin_event(
        self,
        event_name: str,
        actor_id: str,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "success",
        event_metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Log an administrative action.
        
        Args:
            event_name: Admin event (user_create, role_change, settings_update, etc.)
            actor_id: ID of the admin user
            target_id: ID of the affected resource
            target_type: Type of affected resource
            description: Description of the event
            status: Outcome status
            event_metadata: Additional data about the event
            request: FastAPI request object
            
        Returns:
            The created audit log entry
        """
        return await self.log_event(
            event_type="admin",
            event_name=event_name,
            actor_id=actor_id,
            actor_type="user",
            target_id=target_id,
            target_type=target_type,
            description=description,
            status=status,
            event_metadata=event_metadata,
            request=request
        )
    
    async def log_key_event(
        self,
        event_name: str,
        actor_id: Optional[str] = None,
        actor_type: str = "system",
        target_id: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "success",
        event_metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Log a key management event.
        
        Args:
            event_name: Key event (key_rotation, key_generation, etc.)
            actor_id: ID of the user or service
            actor_type: Type of actor
            target_id: ID of the affected key or service
            description: Description of the event
            status: Outcome status
            event_metadata: Additional data about the event
            request: FastAPI request object
            
        Returns:
            The created audit log entry
        """
        return await self.log_event(
            event_type="key",
            event_name=event_name,
            actor_id=actor_id,
            actor_type=actor_type,
            target_id=target_id,
            target_type="key",
            description=description,
            status=status,
            event_metadata=event_metadata,
            request=request
        )
    
    async def log_data_event(
        self,
        event_name: str,
        actor_id: Optional[str] = None,
        actor_type: str = "user",
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "success",
        event_metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Log a data access or modification event.
        
        Args:
            event_name: Data event (read, create, update, delete)
            actor_id: ID of the user or service
            actor_type: Type of actor
            target_id: ID of the data resource
            target_type: Type of data resource (backup, device, config)
            description: Description of the event
            status: Outcome status
            event_metadata: Additional data about the event
            request: FastAPI request object
            
        Returns:
            The created audit log entry
        """
        return await self.log_event(
            event_type="data",
            event_name=event_name,
            actor_id=actor_id,
            actor_type=actor_type,
            target_id=target_id,
            target_type=target_type,
            description=description,
            status=status,
            event_metadata=event_metadata,
            request=request
        ) 