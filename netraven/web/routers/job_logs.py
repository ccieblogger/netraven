"""
Job logs router for the NetRaven web interface.

This module provides endpoints for managing job logs, including listing,
retrieving, and deleting logs, as well as configuring retention policies.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import uuid

# Import authentication dependencies
from netraven.web.auth import (
    get_current_principal, 
    UserPrincipal, 
    require_scope,
    check_job_log_access
)
from netraven.web.models.auth import User
from netraven.web.database import get_db
from netraven.web.models.job_log import JobLog as JobLogModel, JobLogEntry as JobLogEntryModel
from netraven.web.schemas import job_log as job_log_schemas
from netraven.web.crud import (
    get_job_logs, 
    get_job_log, 
    get_job_log_entries, 
    get_job_log_with_entries,
    get_job_log_with_details,
    delete_job_log,
    delete_old_job_logs,
    delete_job_logs_by_retention_policy,
    get_user
)
from netraven.core.logging import get_logger
from netraven.core.config import load_config, get_default_config_path
import os
from netraven.web.schemas.job_log import JobLog, JobLogEntry, JobLogFilter

# Create router
router = APIRouter(prefix="", tags=["job-logs"])

# Initialize logger
logger = get_logger("netraven.web.routers.job_logs")

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

# Note on job_data field:
# The job_data field in the JobLog model uses PostgreSQL's JSONB type for storing
# structured data with better performance and query capabilities compared to regular JSON.
# This allows for efficient indexing and querying of nested JSON data.

@router.get("", response_model=List[job_log_schemas.JobLog])
async def list_job_logs(
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[job_log_schemas.JobLog]:
    """
    List job logs with optional filtering.
    
    Args:
        device_id: Optional device ID to filter logs
        status: Optional status to filter logs
        job_type: Optional job type to filter logs
        limit: Maximum number of logs to return
        offset: Number of logs to skip
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        List[job_log_schemas.JobLog]: List of job logs
    """
    # Check if user has read:job_logs scope
    if not current_principal.has_scope("read:job_logs") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=job_logs, scope=read:job_logs, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: read:job_logs required"
        )
        
    try:
        # Create filter params
        filter_params = job_log_schemas.JobLogFilter(
            device_id=device_id,
            status=status,
            job_type=job_type
        )
        
        # Get job logs from database
        job_logs = get_job_logs(
            db, 
            skip=offset,
            limit=limit,
            filter_params=filter_params
        )
        
        # Filter job logs based on user permissions
        result = []
        for job_log in job_logs:
            # Check if user has access to this device
            if job_log.device and not current_principal.is_admin and job_log.device.owner_id != current_principal.id:
                continue  # Skip logs for devices user doesn't own
            
            # Add log to result
            result.append(job_log)
        
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=job_logs, scope=read:job_logs, count={len(result)}")
        return result
    except Exception as e:
        logger.exception(f"Error listing job logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing job logs: {str(e)}"
        )

@router.get("/{job_log_id}")
async def get_job_log(
    job_log_id: str,
    include_entries: bool = Query(False),
    entry_limit: int = Query(100, gt=0, le=1000),
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a specific job log with optional entries.
    
    Args:
        job_log_id: The job log ID
        include_entries: Whether to include log entries
        entry_limit: Maximum number of entries to return
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Job log with entries
        
    Raises:
        HTTPException: If the job log is not found or user is not authorized
    """
    # Use our permission check function to check access and get the job log
    job_log = check_job_log_access(
        principal=current_principal,
        log_id_or_obj=job_log_id,
        required_scope="read:job_logs",
        db=db
    )
    
    try:
        # Convert job log to dictionary (for JSON response)
        job_log_dict = {
            "id": job_log.id,
            "session_id": job_log.session_id,
            "job_type": job_log.job_type,
            "status": job_log.status,
            "start_time": job_log.start_time,
            "end_time": job_log.end_time,
            "result_message": job_log.result_message,
            "job_data": job_log.job_data,
            "device_id": job_log.device_id,
            "created_by": job_log.created_by,
            "retention_days": job_log.retention_days
        }
        
        # Get entries if requested
        entries = []
        if include_entries:
            entries = get_job_log_entries(db, job_log_id, limit=entry_limit)
            # Convert entries to list of dictionaries
            entries_list = []
            for entry in entries:
                entries_list.append({
                    "id": entry.id,
                    "job_log_id": entry.job_log_id,
                    "timestamp": entry.timestamp,
                    "level": entry.level,
                    "message": entry.message,
                    "data": entry.data
                })
            job_log_dict["entries"] = entries_list
        else:
            job_log_dict["entries"] = []
        
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=job_log:{job_log_id}, scope=read:job_logs, include_entries={include_entries}")
        return job_log_dict
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error retrieving job log: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job log: {str(e)}"
        )

@router.get("/{job_log_id}/entries", response_model=List[job_log_schemas.JobLogEntry])
async def get_job_log_entries_endpoint(
    job_log_id: str,
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[job_log_schemas.JobLogEntry]:
    """
    Get entries for a specific job log.
    
    Args:
        job_log_id: The job log ID
        limit: Maximum number of entries to return
        offset: Number of entries to skip
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        List[job_log_schemas.JobLogEntry]: List of job log entries
        
    Raises:
        HTTPException: If the job log is not found or user is not authorized
    """
    # Use our permission check function to check access and get the job log
    job_log = check_job_log_access(
        principal=current_principal,
        log_id_or_obj=job_log_id,
        required_scope="read:job_logs",
        db=db
    )
    
    try:
        # Get entries
        entries = get_job_log_entries(db, job_log_id, limit=limit, offset=offset)
        
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=job_log:{job_log_id}, scope=read:job_logs, action=get_entries, count={len(entries)}")
        return entries
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error retrieving job log entries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job log entries: {str(e)}"
        )

@router.delete("/{job_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_log_endpoint(
    job_log_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a job log.
    
    Args:
        job_log_id: The job log ID
        current_principal: The authenticated user
        db: Database session
        
    Raises:
        HTTPException: If the job log is not found or user is not authorized
    """
    # Use our permission check function to check access and get the job log
    job_log = check_job_log_access(
        principal=current_principal,
        log_id_or_obj=job_log_id,
        required_scope="write:job_logs",
        db=db
    )
    
    try:
        # Delete the job log
        delete_job_log(db, job_log_id)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=job_log:{job_log_id}, scope=write:job_logs, action=delete")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error deleting job log: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting job log: {str(e)}"
        )

@router.post("/retention", status_code=status.HTTP_200_OK)
async def update_retention_policy(
    retention_policy: job_log_schemas.RetentionPolicyUpdate,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update the job log retention policy.
    
    Args:
        retention_policy: The retention policy update
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Updated retention policy
    """
    require_scope(current_principal, "admin:settings")
    
    # Update retention policy
    # In a real implementation, this would update a configuration in the database
    # For now, we'll just return a success response
    
    return {
        "message": "Retention policy updated successfully",
        "retention_days": retention_policy.retention_days
    }

@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_job_logs(
    days: Optional[int] = None,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clean up old job logs.
    
    Args:
        days: Number of days to keep logs (optional)
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Cleanup results
    """
    require_scope(current_principal, "admin:logs")
    
    # Clean up job logs
    # In a real implementation, this would delete logs older than the specified days
    # For now, we'll just return a success response
    
    return {
        "message": "Job logs cleanup initiated",
        "retention_days": days or 30,
        "status": "success"
    } 