"""
Job logs router for the NetRaven web interface.

This module provides endpoints for managing job logs, including listing,
retrieving, and deleting logs, as well as configuring retention policies.
It also provides access to the job tracking service for real-time job monitoring.
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
from netraven.web.services.job_tracking_service import get_job_tracking_service

# Create router
router = APIRouter(prefix="", tags=["job-logs"])

# Initialize logger
logger = get_logger("netraven.web.routers.job_logs")

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

# Get job tracking service
job_tracking_service = get_job_tracking_service()

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
    # Standardized permission check
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
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=job_logs, scope=read:job_logs, count={len(result)}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
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
    # Use standardized resource access check
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
            entries = get_job_log_entries(db, job_log_id=job_log_id, limit=entry_limit)
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
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=job_log:{job_log_id}, scope=read:job_logs, include_entries={include_entries}")
        return job_log_dict
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error retrieving job log: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job log: {str(e)}"
        )

@router.get("/{id}/entries")
def fetch_job_log_entries(
    id: str,
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get job log entries for a job log.
    
    Args:
        id: Job log ID
        principal: User principal
        db: Database session
        
    Returns:
        List of job log entries
        
    Raises:
        HTTPException: If job log not found or user doesn't have permission
    """
    # Use standardized resource access check
    job_log = check_job_log_access(
        principal=principal,
        log_id_or_obj=id,
        required_scope="read:job_logs",
        db=db
    )
    
    try:
        # Get job log entries
        entries = get_job_log_entries(db, job_log_id=id)
        
        # Convert entries to list of dictionaries
        entries_list = []
        for entry in entries:
            entries_list.append({
                "id": entry.id,
                "job_log_id": entry.job_log_id,
                "timestamp": entry.timestamp,
                "level": entry.level,
                "category": entry.category,
                "message": entry.message,
                "details": entry.details,
                "session_log_content": entry.session_log_content,
                "session_log_path": entry.session_log_path,
                "credential_username": entry.credential_username
            })
        
        # Log access granted
        logger.info(f"Access granted: user={principal.username}, " 
                   f"resource=job_log_entries:{id}, scope=read:job_logs, count={len(entries_list)}")
        
        return entries_list
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error getting job log entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting job log entries: {str(e)}"
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
    # Check if user has proper permissions (write:job_logs or admin)
    if not current_principal.has_scope("write:job_logs") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=job_log:{job_log_id}, scope=write:job_logs, action=delete, "
                     f"reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: write:job_logs required"
        )
    
    # Check if job log exists and user has access
    job_log = check_job_log_access(
        principal=current_principal,
        log_id_or_obj=job_log_id,
        required_scope="write:job_logs",
        db=db
    )
    
    try:
        # Delete job log
        delete_job_log(db, job_log_id)
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=job_log:{job_log_id}, scope=write:job_logs, action=delete")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
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
    Update retention policy for job logs.
    
    Args:
        retention_policy: The updated retention policy
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Updated retention policy
        
    Raises:
        HTTPException: If user is not authorized
    """
    # Standardized permission check (admin or write:job_logs)
    if not current_principal.has_scope("write:job_logs") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=job_logs:retention, scope=write:job_logs, "
                     f"reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: write:job_logs required"
        )
    
    try:
        # Apply retention policy and delete old logs
        deleted_count = delete_job_logs_by_retention_policy(db, retention_policy.default_retention_days)
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=job_logs:retention, scope=write:job_logs, "
                  f"action=update, deleted_count={deleted_count}")
        return {
            "default_retention_days": retention_policy.default_retention_days,
            "deleted_count": deleted_count,
            "message": f"{deleted_count} logs deleted based on retention policy"
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error updating retention policy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating retention policy: {str(e)}"
        )

@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_job_logs(
    days: Optional[int] = None,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clean up job logs by deleting logs older than a specified number of days.
    
    Args:
        days: Number of days to keep logs (defaults to 30)
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Cleanup results
        
    Raises:
        HTTPException: If user is not authorized
    """
    # Standardized permission check (admin or write:job_logs)
    if not current_principal.has_scope("write:job_logs") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=job_logs:cleanup, scope=write:job_logs, "
                     f"reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: write:job_logs required"
        )
    
    try:
        # Default to 30 days if not specified
        days = days or 30
        
        # Delete old logs
        deleted_count = delete_old_job_logs(db, days)
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=job_logs:cleanup, scope=write:job_logs, "
                  f"action=cleanup, days={days}, deleted_count={deleted_count}")
        return {
            "days": days,
            "deleted_count": deleted_count,
            "message": f"{deleted_count} logs older than {days} days deleted"
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error cleaning up job logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up job logs: {str(e)}"
        )

# New endpoints for job tracking and monitoring

@router.get("/active", response_model=List[Dict[str, Any]])
async def list_active_jobs(
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all currently active jobs.
    
    Args:
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        List[Dict[str, Any]]: List of active jobs
    """
    # Standardized permission check
    if not current_principal.has_scope("read:job_logs") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=active_jobs, scope=read:job_logs, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: read:job_logs required"
        )
    
    try:
        # Get active jobs from job tracking service
        active_jobs = []
        
        # Convert active jobs to list of dictionaries with permission filtering
        for job_id, job_info in job_tracking_service.active_jobs.items():
            # Check if user has access to this job
            user_id = job_info.get("user_id")
            if not current_principal.is_admin and user_id != current_principal.id:
                # For regular users, only show their own jobs
                continue
                
            # Add device and job names for better context
            device_name = "Unknown"
            job_name = "Unknown"
            
            # Get device info if available
            device_id = job_info.get("device_id")
            if device_id:
                from netraven.web.crud.device import get_device
                device = get_device(db, device_id)
                if device:
                    device_name = device.name
            
            # Get job info if it's a scheduled job
            scheduled_job_id = job_info.get("scheduled_job_id")
            if scheduled_job_id:
                from netraven.web.crud.scheduled_job import get_scheduled_job
                scheduled_job = get_scheduled_job(db, scheduled_job_id)
                if scheduled_job:
                    job_name = scheduled_job.name
            
            # Get the job log for more details
            job_log = db.query(JobLogModel).filter(JobLogModel.id == job_id).first()
            
            # Create job info dictionary
            job_dict = {
                "id": job_id,
                "session_id": job_info.get("session_id"),
                "job_type": job_info.get("job_type"),
                "device_id": device_id,
                "device_name": device_name,
                "user_id": user_id,
                "start_time": job_info.get("start_time"),
                "retry_count": job_info.get("retry_count", 0),
                "scheduled_job_id": scheduled_job_id,
                "scheduled_job_name": job_name,
                "status": job_log.status if job_log else "running"
            }
            
            active_jobs.append(job_dict)
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=active_jobs, scope=read:job_logs, count={len(active_jobs)}")
        
        return active_jobs
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error listing active jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing active jobs: {str(e)}"
        )

@router.get("/statistics", response_model=Dict[str, Any])
async def get_job_statistics(
    time_period: str = Query("day", description="Time period for statistics (day, week, month)"),
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get statistics about job executions.
    
    Args:
        time_period: Time period to get statistics for (day, week, month)
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Job statistics
    """
    # Standardized permission check
    if not current_principal.has_scope("read:job_logs") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=job_statistics, scope=read:job_logs, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: read:job_logs required"
        )
    
    try:
        # Validate time period
        if time_period not in ["day", "week", "month"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid time period. Must be one of: day, week, month"
            )
        
        # Get job statistics from job tracking service
        statistics = job_tracking_service.get_job_statistics(time_period)
        
        # For non-admin users, filter statistics to only include their jobs
        if not current_principal.is_admin:
            # This would be a more complex implementation
            # For now, we'll just add a note that user-specific filtering
            # is not implemented yet
            statistics["note"] = "User-specific filtering not implemented yet"
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=job_statistics, scope=read:job_logs, time_period={time_period}")
        
        return statistics
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error getting job statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting job statistics: {str(e)}"
        ) 