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
from netraven.web.routers.auth import User, get_current_active_user, get_current_admin_user
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
    delete_job_logs_by_retention_policy
)
from netraven.core.logging import get_logger
from netraven.core.config import load_config, get_default_config_path
import os
from netraven.web.schemas.job_log import JobLog, JobLogEntry, JobLogFilter

# Create router
router = APIRouter(prefix="/api/job-logs", tags=["job-logs"])

# Initialize logger
logger = get_logger("netraven.web.routers.job_logs")

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

@router.get("", response_model=List[job_log_schemas.JobLog])
async def list_job_logs(
    device_id: Optional[str] = None,
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    start_time_from: Optional[datetime] = None,
    start_time_to: Optional[datetime] = None,
    session_id: Optional[str] = None,
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[job_log_schemas.JobLog]:
    """
    List job logs with optional filtering.
    
    This endpoint returns a list of job logs that match the specified filters.
    Regular users can only see logs for devices they own, while admin users
    can see all logs.
    """
    # Check if user is admin
    is_admin = current_user.is_admin
    
    # For regular users, only show logs for their devices
    created_by = None if is_admin else current_user.id
    
    # Create filter parameters
    filter_params = JobLogFilter(
        device_id=device_id,
        job_type=job_type,
        status=status,
        start_date=start_time_from,
        end_date=start_time_to,
        created_by=created_by,
        session_id=session_id
    )
    
    # Get job logs
    job_logs = get_job_logs(
        db=db,
        filter_params=filter_params,
        skip=offset,
        limit=limit
    )
    
    # Convert to Pydantic models
    return [job_log_schemas.JobLog.model_validate(job_log) for job_log in job_logs]

@router.get("/{job_log_id}", response_model=job_log_schemas.JobLogComplete)
async def get_job_log_details(
    job_log_id: str,
    include_entries: bool = Query(False),
    entry_limit: int = Query(100, gt=0, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> job_log_schemas.JobLogComplete:
    """
    Get detailed information about a job log.
    
    This endpoint returns detailed information about a job log, including
    device and user details, and optionally log entries.
    """
    # Get job log with details
    job_log = get_job_log_with_details(
        db=db,
        log_id=job_log_id
    )
    
    if not job_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job log with ID {job_log_id} not found"
        )
    
    # Check if user has access to this job log
    if not current_user.is_admin and job_log.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this job log"
        )
    
    return job_log

@router.get("/{job_log_id}/entries", response_model=List[job_log_schemas.JobLogEntry])
async def get_job_log_entries_endpoint(
    job_log_id: str,
    level: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[job_log_schemas.JobLogEntry]:
    """
    Get entries for a job log.
    
    This endpoint returns entries for a job log, with optional filtering
    by log level and category.
    """
    # Get job log
    job_log = get_job_log(db, job_log_id)
    
    if not job_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job log with ID {job_log_id} not found"
        )
    
    # Check if user has access to this job log
    if not current_user.is_admin and job_log.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this job log"
        )
    
    # Get entries
    entries = get_job_log_entries(
        db=db,
        log_id=job_log_id,
        level=level,
        skip=offset,
        limit=limit
    )
    
    # Convert to Pydantic models
    return [job_log_schemas.JobLogEntry.model_validate(entry) for entry in entries]

@router.delete("/{job_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_log_endpoint(
    job_log_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a job log.
    
    This endpoint deletes a job log and all its entries.
    Only admin users can delete job logs.
    """
    # Delete job log
    success = delete_job_log(db, job_log_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job log with ID {job_log_id} not found"
        )

@router.post("/retention", status_code=status.HTTP_200_OK)
async def update_retention_policy(
    retention_policy: job_log_schemas.RetentionPolicyUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update the retention policy for job logs.
    
    This endpoint updates the default retention period for job logs.
    Only admin users can update the retention policy.
    """
    # Update configuration
    config["logging"]["retention_days"] = retention_policy.default_retention_days
    
    # Save configuration
    # Note: In a real implementation, this would save the config to disk
    logger.info(f"Updated job log retention policy to {retention_policy.default_retention_days} days")
    
    # Apply to existing logs if requested
    updated_count = 0
    if retention_policy.apply_to_existing:
        # Update all logs without a retention_days value
        logs_to_update = db.query(JobLogModel).filter(JobLogModel.retention_days.is_(None)).all()
        for log in logs_to_update:
            log.retention_days = retention_policy.default_retention_days
            updated_count += 1
        
        db.commit()
        logger.info(f"Applied retention policy to {updated_count} existing job logs")
    
    return {
        "message": f"Retention policy updated to {retention_policy.default_retention_days} days",
        "updated_logs": updated_count
    }

@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_job_logs(
    days: Optional[int] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clean up old job logs.
    
    This endpoint deletes job logs based on the retention policy.
    If days is specified, it deletes logs older than the specified number of days.
    Otherwise, it uses the retention_days field of each log.
    Only admin users can clean up job logs.
    """
    if days is not None:
        # Delete logs older than the specified number of days
        deleted_count = delete_old_job_logs(db, days)
        return {
            "message": f"Deleted {deleted_count} job logs older than {days} days"
        }
    else:
        # Delete logs based on their retention policy
        deleted_count = delete_job_logs_by_retention_policy(db)
        return {
            "message": f"Deleted {deleted_count} job logs based on retention policy"
        } 