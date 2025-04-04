"""
Audit Logs router for NetRaven web API.

This module provides API endpoints for querying and managing audit logs.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from netraven.web.database import get_db
from netraven.web.auth import UserPrincipal, get_current_principal
from netraven.web.auth.permissions import require_scope, require_admin
from netraven.web.models.audit_log import AuditLog
from netraven.web.schemas.audit_log import (
    AuditLogResponse, 
    AuditLogFilter,
    AuditLogList
)
from netraven.web.services.audit_service import AuditService
from netraven.core.logging import get_logger

# Create router
router = APIRouter(prefix="/audit-logs", tags=["audit logs"])

# Initialize logger
logger = get_logger(__name__)


@router.get("/", response_model=AuditLogList)
async def list_audit_logs(
    request: Request,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    event_name: Optional[str] = Query(None, description="Filter by event name"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    target_id: Optional[str] = Query(None, description="Filter by target ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    skip: int = Query(0, description="Number of records to skip", ge=0),
    limit: int = Query(50, description="Maximum number of records to return", ge=1, le=100),
    principal: UserPrincipal = Depends(require_admin("admin:audit")),
    db: Session = Depends(get_db)
):
    """
    List audit log entries with filtering and pagination.
    
    This endpoint requires admin privileges with the admin:audit scope.
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
        
        logger.info(f"Audit logs listed: user={principal.username}, count={len(result['items'])}, total={result['total']}")
        
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
        
        logger.error(f"Error listing audit logs: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit logs: {str(e)}"
        )


@router.get("/{audit_log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_log_id: str,
    request: Request,
    principal: UserPrincipal = Depends(require_admin("admin:audit")),
    db: Session = Depends(get_db)
):
    """
    Get a specific audit log entry by ID.
    
    This endpoint requires admin privileges with the admin:audit scope.
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
            
            logger.warning(f"Audit log not found: id={audit_log_id}, user={principal.username}")
            
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
        
        logger.info(f"Audit log retrieved: id={audit_log_id}, user={principal.username}")
        
        return audit_log
    except HTTPException:
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
        
        logger.error(f"Error retrieving audit log: id={audit_log_id}, error={str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit log: {str(e)}"
        ) 