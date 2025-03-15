"""
Scheduled jobs router for the NetRaven web interface.

This module provides endpoints for managing scheduled backup jobs, including
creating, listing, updating, and deleting scheduled jobs.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid

# Import authentication dependencies
from netraven.web.routers.auth import User, get_current_active_user, get_current_admin_user
from netraven.web.database import get_db
from netraven.web.models.scheduled_job import ScheduledJob as ScheduledJobModel
from netraven.web.schemas import scheduled_job as scheduled_job_schemas
from netraven.web.crud import (
    get_scheduled_jobs,
    get_scheduled_job,
    get_scheduled_job_with_details,
    create_scheduled_job,
    update_scheduled_job,
    delete_scheduled_job,
    toggle_scheduled_job,
    update_job_last_run,
    get_device
)
from netraven.core.logging import get_logger
from netraven.jobs.scheduler import get_scheduler

# Create router
router = APIRouter()

# Initialize logger
logger = get_logger("netraven.web.routers.scheduled_jobs")

@router.get("", response_model=List[scheduled_job_schemas.ScheduledJobWithDevice])
async def list_scheduled_jobs(
    device_id: Optional[str] = None,
    schedule_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[scheduled_job_schemas.ScheduledJobWithDevice]:
    """
    Get a list of scheduled jobs with optional filtering.
    
    Args:
        device_id: Filter by device ID
        schedule_type: Filter by schedule type
        enabled: Filter by enabled status
        limit: Maximum number of records to return
        offset: Number of records to skip
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of scheduled jobs
    """
    # Create filter parameters
    filter_params = scheduled_job_schemas.ScheduledJobFilter(
        device_id=device_id,
        schedule_type=schedule_type,
        enabled=enabled,
        created_by=None if current_user.is_admin else current_user.id
    )
    
    # Get scheduled jobs
    jobs = get_scheduled_jobs(db, offset, limit, filter_params)
    
    # Enhance with device details
    result = []
    for job in jobs:
        device = get_device(db, job.device_id)
        if device:
            job_dict = {
                **job.__dict__,
                "device_hostname": device.hostname,
                "device_ip": device.ip_address,
                "device_type": device.device_type
            }
            result.append(job_dict)
    
    return result

@router.get("/{job_id}", response_model=scheduled_job_schemas.ScheduledJobComplete)
async def get_scheduled_job_details(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> scheduled_job_schemas.ScheduledJobComplete:
    """
    Get details of a specific scheduled job.
    
    Args:
        job_id: Scheduled job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Scheduled job details
    """
    # Get scheduled job with details
    job = get_scheduled_job_with_details(db, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled job with ID {job_id} not found"
        )
    
    # Check if user has access to this job
    if not current_user.is_admin and job["created_by"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this scheduled job"
        )
    
    return job

@router.post("", response_model=scheduled_job_schemas.ScheduledJob, status_code=status.HTTP_201_CREATED)
async def create_scheduled_job_endpoint(
    job_data: scheduled_job_schemas.ScheduledJobCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> scheduled_job_schemas.ScheduledJob:
    """
    Create a new scheduled job.
    
    Args:
        job_data: Scheduled job data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created scheduled job
    """
    # Validate device exists
    device = get_device(db, job_data.device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {job_data.device_id} not found"
        )
    
    # Check if user has access to this device
    if not current_user.is_admin and device.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create a scheduled job for this device"
        )
    
    # Validate schedule parameters
    if job_data.schedule_type == "daily" or job_data.schedule_type == "weekly":
        if not job_data.schedule_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule time is required for daily and weekly schedules"
            )
    
    if job_data.schedule_type == "weekly" and not job_data.schedule_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule day is required for weekly schedules"
        )
    
    if job_data.schedule_type == "interval" and not job_data.schedule_interval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule interval is required for interval schedules"
        )
    
    # Create scheduled job
    job = create_scheduled_job(db, job_data, current_user.id)
    
    # Add job to scheduler if enabled
    if job.enabled:
        try:
            scheduler = get_scheduler()
            scheduler.schedule_backup(
                device_id=device.id,
                host=device.hostname,
                username=device.username,
                password=device.password,
                device_type=device.device_type,
                schedule_type=job.schedule_type,
                schedule_time=job.schedule_time,
                schedule_interval=job.schedule_interval,
                schedule_day=job.schedule_day,
                job_name=job.name
            )
            
            # Start scheduler if not already running
            if not scheduler.running:
                scheduler.start()
        except Exception as e:
            logger.error(f"Error adding job to scheduler: {e}")
            # Continue anyway, as the job is in the database
    
    return job

@router.put("/{job_id}", response_model=scheduled_job_schemas.ScheduledJob)
async def update_scheduled_job_endpoint(
    job_id: str,
    job_data: scheduled_job_schemas.ScheduledJobUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> scheduled_job_schemas.ScheduledJob:
    """
    Update a scheduled job.
    
    Args:
        job_id: Scheduled job ID
        job_data: Updated scheduled job data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated scheduled job
    """
    # Get scheduled job
    job = get_scheduled_job(db, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled job with ID {job_id} not found"
        )
    
    # Check if user has access to this job
    if not current_user.is_admin and job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this scheduled job"
        )
    
    # Validate schedule parameters
    update_data = job_data.dict(exclude_unset=True)
    
    schedule_type = update_data.get("schedule_type", job.schedule_type)
    schedule_time = update_data.get("schedule_time", job.schedule_time)
    schedule_day = update_data.get("schedule_day", job.schedule_day)
    schedule_interval = update_data.get("schedule_interval", job.schedule_interval)
    
    if schedule_type == "daily" or schedule_type == "weekly":
        if not schedule_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule time is required for daily and weekly schedules"
            )
    
    if schedule_type == "weekly" and not schedule_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule day is required for weekly schedules"
        )
    
    if schedule_type == "interval" and not schedule_interval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule interval is required for interval schedules"
        )
    
    # Update scheduled job
    updated_job = update_scheduled_job(db, job_id, job_data)
    
    # Update job in scheduler if enabled
    if updated_job.enabled:
        try:
            # Get device details
            device = get_device(db, updated_job.device_id)
            
            # Update scheduler
            scheduler = get_scheduler()
            
            # First remove the old job
            scheduler.cancel_job(job_id)
            
            # Then add the updated job
            scheduler.schedule_backup(
                device_id=device.id,
                host=device.hostname,
                username=device.username,
                password=device.password,
                device_type=device.device_type,
                schedule_type=updated_job.schedule_type,
                schedule_time=updated_job.schedule_time,
                schedule_interval=updated_job.schedule_interval,
                schedule_day=updated_job.schedule_day,
                job_name=updated_job.name
            )
            
            # Start scheduler if not already running
            if not scheduler.running:
                scheduler.start()
        except Exception as e:
            logger.error(f"Error updating job in scheduler: {e}")
            # Continue anyway, as the job is updated in the database
    
    return updated_job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_job_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a scheduled job.
    
    Args:
        job_id: Scheduled job ID
        current_user: Current authenticated user
        db: Database session
    """
    # Get scheduled job
    job = get_scheduled_job(db, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled job with ID {job_id} not found"
        )
    
    # Check if user has access to this job
    if not current_user.is_admin and job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this scheduled job"
        )
    
    # Delete scheduled job
    result = delete_scheduled_job(db, job_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting scheduled job"
        )
    
    # Remove job from scheduler
    try:
        scheduler = get_scheduler()
        scheduler.cancel_job(job_id)
    except Exception as e:
        logger.error(f"Error removing job from scheduler: {e}")
        # Continue anyway, as the job is deleted from the database

@router.post("/{job_id}/toggle", response_model=scheduled_job_schemas.ScheduledJob)
async def toggle_scheduled_job_endpoint(
    job_id: str,
    toggle_data: scheduled_job_schemas.ScheduledJobToggle,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> scheduled_job_schemas.ScheduledJob:
    """
    Toggle a scheduled job's enabled status.
    
    Args:
        job_id: Scheduled job ID
        toggle_data: Toggle data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated scheduled job
    """
    # Get scheduled job
    job = get_scheduled_job(db, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled job with ID {job_id} not found"
        )
    
    # Check if user has access to this job
    if not current_user.is_admin and job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to toggle this scheduled job"
        )
    
    # Toggle scheduled job
    updated_job = toggle_scheduled_job(db, job_id, toggle_data.enabled)
    
    # Update job in scheduler
    try:
        scheduler = get_scheduler()
        
        if toggle_data.enabled:
            # Get device details
            device = get_device(db, updated_job.device_id)
            
            # Add job to scheduler
            scheduler.schedule_backup(
                device_id=device.id,
                host=device.hostname,
                username=device.username,
                password=device.password,
                device_type=device.device_type,
                schedule_type=updated_job.schedule_type,
                schedule_time=updated_job.schedule_time,
                schedule_interval=updated_job.schedule_interval,
                schedule_day=updated_job.schedule_day,
                job_name=updated_job.name
            )
            
            # Start scheduler if not already running
            if not scheduler.running:
                scheduler.start()
        else:
            # Remove job from scheduler
            scheduler.cancel_job(job_id)
    except Exception as e:
        logger.error(f"Error updating job in scheduler: {e}")
        # Continue anyway, as the job is updated in the database
    
    return updated_job

@router.post("/{job_id}/run", response_model=Dict[str, Any])
async def run_scheduled_job_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run a scheduled job immediately.
    
    Args:
        job_id: Scheduled job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Result of the job run
    """
    # Get scheduled job
    job = get_scheduled_job(db, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled job with ID {job_id} not found"
        )
    
    # Check if user has access to this job
    if not current_user.is_admin and job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to run this scheduled job"
        )
    
    # Get device details
    device = get_device(db, job.device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {job.device_id} not found"
        )
    
    # Run job
    try:
        from netraven.jobs.device_connector import backup_device_config
        
        # Run backup
        result = backup_device_config(
            device_id=device.id,
            host=device.hostname,
            username=device.username,
            password=device.password,
            device_type=device.device_type,
            user_id=current_user.id
        )
        
        # Update last run time
        update_job_last_run(db, job_id, result)
        
        return {
            "success": result,
            "message": "Backup job completed successfully" if result else "Backup job failed"
        }
    except Exception as e:
        logger.error(f"Error running scheduled job: {e}")
        
        # Update last run time
        update_job_last_run(db, job_id, False)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running scheduled job: {str(e)}"
        ) 