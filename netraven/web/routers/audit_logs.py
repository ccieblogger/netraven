"""
Audit Logs router for NetRaven web API.

This module provides API endpoints for querying and managing audit logs.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from netraven.web.database import get_db
from netraven.web.auth import get_current_principal, require_scope, UserPrincipal
from netraven.web.models.audit_log import AuditLog
from netraven.web.schemas.audit_log import (
    AuditLogResponse, 
    AuditLogFilter,
    AuditLogList
)
from netraven.web.services.audit_service import AuditService

# Create router
router = APIRouter(prefix="", tags=["audit logs"])


@router.get("/", response_model=AuditLogList)
async def list_audit_logs(
    request: Request,
    event_type: Optional[str] = None,
    event_name: Optional[str] = None,
    actor_id: Optional[str] = None,
    target_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(require_scope(["admin:audit"]))
):
    """
    List audit log entries with filtering and pagination.
    
    This endpoint requires admin:audit scope and returns audit log entries
    that match the specified filter criteria.
    """
    # Build filter params from query parameters
    filter_params = AuditLogFilter(
        event_type=event_type,
        event_name=event_name,
        actor_id=actor_id,
        target_id=target_id,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    
    try:
        # Log this access to audit logs
        AuditService.log_admin_event(
            db=db,
            event_name="audit_logs_access",
            actor_id=principal.username,
            description=f"Accessed audit logs with filters: {filter_params.dict(exclude_none=True)}",
            request=request
        )
        
        # Get audit logs with the filter
        result = AuditService.get_audit_logs(
            db=db,
            filter_params=filter_params,
            skip=skip,
            limit=limit
        )
        
        # Return the result
        return AuditLogList(
            items=result["items"],
            total=result["total"],
            page=(skip // limit) + 1,
            page_size=limit
        )
    except Exception as e:
        # Log error to audit logs
        AuditService.log_admin_event(
            db=db,
            event_name="audit_logs_access_error",
            actor_id=principal.username,
            description=f"Error accessing audit logs: {str(e)}",
            status="error",
            request=request
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit logs: {str(e)}"
        )


@router.get("/{audit_log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_log_id: str,
    request: Request,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(require_scope(["admin:audit"]))
):
    """
    Get a specific audit log entry by ID.
    
    This endpoint requires admin:audit scope and returns a single audit log entry.
    """
    try:
        # Get the audit log
        audit_log = AuditService.get_audit_log_by_id(db=db, audit_log_id=audit_log_id)
        
        if not audit_log:
            # Log not found to audit logs
            AuditService.log_admin_event(
                db=db,
                event_name="audit_log_access_not_found",
                actor_id=principal.username,
                target_id=audit_log_id,
                target_type="audit_log",
                description=f"Attempted to access non-existent audit log: {audit_log_id}",
                status="failure",
                request=request
            )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit log with ID {audit_log_id} not found"
            )
        
        # Log this access to audit logs
        AuditService.log_admin_event(
            db=db,
            event_name="audit_log_access",
            actor_id=principal.username,
            target_id=audit_log_id,
            target_type="audit_log",
            description=f"Accessed audit log: {audit_log_id}",
            request=request
        )
        
        return audit_log
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log error to audit logs
        AuditService.log_admin_event(
            db=db,
            event_name="audit_log_access_error",
            actor_id=principal.username,
            target_id=audit_log_id,
            target_type="audit_log",
            description=f"Error accessing audit log: {str(e)}",
            status="error",
            request=request
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit log: {str(e)}"
        ) 