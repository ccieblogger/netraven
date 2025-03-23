"""
Scheduled jobs router for the NetRaven web interface.

This module provides endpoints for managing scheduled backup jobs, including
creating, listing, updating, and deleting scheduled jobs.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import uuid
import os
import calendar
from sqlalchemy import func

# Import authentication dependencies
from netraven.web.auth import (
    get_current_principal, 
    UserPrincipal, 
    require_scope,
    check_scheduled_job_access,
    check_device_access
)
from netraven.web.models.auth import User
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
from netraven.web.constants import JobTypeEnum, ScheduleTypeEnum
from netraven.core.logging import get_logger
from netraven.jobs.scheduler import get_scheduler
from netraven.web.models.job_log import JobLog as JobLogModel
from netraven.web.services.scheduler_service import get_scheduler_service
from netraven.web.models.device import Device

# Create router
router = APIRouter(prefix="", tags=["scheduled-jobs"])

# Initialize logger
logger = get_logger("netraven.web.routers.scheduled_jobs")

@router.get("", response_model=List[scheduled_job_schemas.ScheduledJobWithDetails])
async def list_scheduled_jobs(
    device_id: Optional[str] = None,
    schedule_type: Optional[str] = None,
    job_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[scheduled_job_schemas.ScheduledJobWithDetails]:
    """
    Get a list of scheduled jobs with optional filtering.
    
    Args:
        device_id: Filter by device ID
        schedule_type: Filter by schedule type
        job_type: Filter by job type
        enabled: Filter by enabled status
        limit: Maximum number of records to return
        offset: Number of records to skip
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of scheduled jobs with details
    """
    # Check permission
    if not current_user.has_scope("read:schedules") and not current_user.is_admin:
        logger.warning(f"Access denied: user={current_user.username}, " 
                     f"resource=scheduled_jobs, scope=read:schedules, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: read:schedules required"
        )
    
    try:
        # If device_id is provided, verify access to that device
        if device_id:
            check_device_access(
                principal=current_user,
                device_id_or_obj=device_id,
                required_scope="read:devices",
                db=db
            )
        
        # Create filter parameters
        filter_params = scheduled_job_schemas.ScheduledJobFilter(
            device_id=device_id,
            schedule_type=schedule_type,
            job_type=job_type,
            enabled=enabled,
            created_by=None if current_user.is_admin else current_user.id
        )
        
        # Get scheduled jobs
        jobs = get_scheduled_jobs(db, offset, limit, filter_params)
        
        # Enhance with device and user details
        result = []
        for job in jobs:
            device = get_device(db, job.device_id)
            user = db.query(User).filter(User.id == job.created_by).first()
            
            if device:
                job_dict = {
                    # Base job fields
                    "id": job.id,
                    "name": job.name,
                    "device_id": job.device_id,
                    "job_type": job.job_type,
                    "schedule_type": job.schedule_type,
                    "enabled": job.enabled,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                    "last_run": job.last_run,
                    "next_run": job.next_run,
                    "created_by": job.created_by,
                    "job_data": job.job_data,
                    
                    # New scheduling fields
                    "start_datetime": job.start_datetime,
                    "recurrence_day": job.recurrence_day,
                    "recurrence_month": job.recurrence_month,
                    "recurrence_time": job.recurrence_time,
                    
                    # Device details
                    "device_name": device.name,
                    "device_type": device.device_type,
                    
                    # User details
                    "username": user.username if user else "Unknown",
                }
                result.append(job_dict)
        
        logger.info(f"Retrieved {len(result)} scheduled jobs for user={current_user.username}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error listing scheduled jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing scheduled jobs: {str(e)}"
        )

@router.get("/{job_id}", response_model=scheduled_job_schemas.ScheduledJobWithDetails)
async def get_scheduled_job_details(
    job_id: str,
    current_user: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get details of a specific scheduled job.
    
    Args:
        job_id: Scheduled job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Scheduled job details
    """
    # Use our permission check function to check permissions and get the job
    job = check_scheduled_job_access(
        principal=current_user,
        job_id_or_obj=job_id,
        required_scope="read:schedules",
        db=db
    )
    
    try:
        # Get detailed job information
        job_details = get_scheduled_job_with_details(db, job_id)
        if not job_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheduled job with ID {job_id} not found"
            )
        
        logger.info(f"Retrieved scheduled job details: user={current_user.username}, job_id={job_id}")
        return job_details
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error retrieving scheduled job details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving scheduled job details: {str(e)}"
        )

@router.post("", response_model=scheduled_job_schemas.ScheduledJobInDB, status_code=status.HTTP_201_CREATED)
async def create_scheduled_job_endpoint(
    job_data: scheduled_job_schemas.ScheduledJobCreate,
    current_user: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> scheduled_job_schemas.ScheduledJobInDB:
    """
    Create a new scheduled job.
    
    Args:
        job_data: Scheduled job data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created scheduled job
    """
    # Log received data for debugging
    logger.info(f"Received scheduled job create request: {job_data.model_dump()}")
    
    # Check permission
    if not current_user.has_scope("write:schedules") and not current_user.is_admin:
        logger.warning(f"Access denied: user={current_user.username}, " 
                     f"resource=scheduled_jobs, scope=write:schedules, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: write:schedules required"
        )
    
    try:
        # Special handling for backup jobs - require device_id
        if job_data.job_type == "backup" and not job_data.device_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A device is required for backup jobs. Please select a valid device."
            )
        
        # Check if device exists when device_id is provided
        if job_data.device_id:
            # First check if any devices exist in the system
            device_count = db.query(func.count()).select_from(Device).scalar()
            if device_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No devices found in the system. Please add at least one device before creating a scheduled job."
                )
            
            # Check if user has access to the device
            try:
                device = check_device_access(
                    principal=current_user,
                    device_id_or_obj=job_data.device_id,
                    required_scope="read:devices",
                    db=db
                )
                
                if not device:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Device with ID {job_data.device_id} not found or you don't have access to it."
                    )
            except Exception as e:
                logger.error(f"Error checking device access: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Error validating device: {str(e)}"
                )
        
        # Validate schedule parameters based on schedule type
        try:
            validate_schedule_parameters(job_data.schedule_type, job_data)
        except HTTPException as e:
            logger.error(f"Schedule parameter validation failed: {e.detail}")
            raise
        
        # Create the scheduled job
        job = create_scheduled_job(db, job_data, current_user.id)
        
        # Get scheduler instance
        scheduler = get_scheduler()
        
        # Add job to scheduler using new field format
        try:
            scheduler.schedule_job(
                job_id=job.id,
                device_id=device.id,
                job_type=job_data.job_type,
                schedule_type=job_data.schedule_type,
                schedule_time=job_data.schedule_time,
                schedule_day=job_data.schedule_day,
                schedule_interval=job_data.schedule_interval,
                start_datetime=job_data.start_datetime,
                recurrence_time=None,
                recurrence_day=None,
                recurrence_month=job_data.recurrence_month,
                job_data=job_data.job_data
            )
            logger.info(f"Scheduled job created: {job.id}, schedule: {job_data.schedule_type}")
        except Exception as e:
            logger.error(f"Error scheduling job {job.id}: {str(e)}")
            # Job is created in database even if scheduling fails
            # Consider adding a status field to mark jobs with scheduling issues
        
        return job
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error creating scheduled job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating scheduled job: {str(e)}"
        )

@router.put("/{job_id}", response_model=scheduled_job_schemas.ScheduledJobInDB)
async def update_scheduled_job_endpoint(
    job_id: str,
    job_data: scheduled_job_schemas.ScheduledJobUpdate,
    current_user: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> scheduled_job_schemas.ScheduledJobInDB:
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
    # Use our permission check function to check permissions and get the job
    job = check_scheduled_job_access(
        principal=current_user,
        job_id_or_obj=job_id,
        required_scope="write:schedules",
        db=db
    )
    
    try:
        # Using model_dump() for Pydantic v2 compatibility
        update_data = job_data.model_dump(exclude_unset=True)
        
        # Check if schedule type is being changed
        new_schedule_type = update_data.get("schedule_type", job.schedule_type)
        
        # If schedule type has been provided, validate parameters for that type
        if "schedule_type" in update_data:
            # Create a merged object with both existing and updated values for validation
            merged_data = create_merged_job_data(job, job_data)
            validate_schedule_parameters(new_schedule_type, merged_data)
        
        # Update the scheduled job
        updated_job = update_scheduled_job(db, job_id, job_data)
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheduled job with ID {job_id} not found"
            )
        
        # Get device details
        device = get_device(db, updated_job.device_id)
        if not device:
            logger.warning(f"Device {updated_job.device_id} not found for job {job_id}")
        
        # Get scheduler instance and update the schedule
        scheduler = get_scheduler()
        
        try:
            # Cancel existing job
            scheduler.cancel_job(job_id)
            
            # Reschedule with new parameters if job is enabled
            if updated_job.enabled:
                scheduler.schedule_job(
                    job_id=updated_job.id,
                    device_id=device.id if device else updated_job.device_id,
                    job_type=updated_job.job_type,
                    schedule_type=updated_job.schedule_type,
                    schedule_time=updated_job.schedule_time,
                    schedule_day=updated_job.schedule_day,
                    schedule_interval=updated_job.schedule_interval,
                    start_datetime=updated_job.start_datetime,
                    recurrence_time=updated_job.recurrence_time,
                    recurrence_day=updated_job.recurrence_day,
                    recurrence_month=updated_job.recurrence_month,
                    job_data=updated_job.job_data
                )
            
            logger.info(f"Scheduled job updated: {job_id}, schedule: {updated_job.schedule_type}")
        except Exception as e:
            logger.error(f"Error updating job schedule {job_id}: {str(e)}")
            # Job is updated in database even if scheduling fails
        
        return updated_job
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error updating scheduled job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating scheduled job: {str(e)}"
        )

def validate_schedule_parameters(schedule_type: ScheduleTypeEnum, job_data: Union[scheduled_job_schemas.ScheduledJobCreate, Any]) -> None:
    """
    Validate schedule parameters based on schedule type.
    
    Args:
        schedule_type: Type of schedule
        job_data: Job data containing schedule parameters
        
    Raises:
        HTTPException: If validation fails
    """
    # For ONE_TIME schedules, start_datetime is required
    if schedule_type == ScheduleTypeEnum.ONE_TIME and not job_data.start_datetime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start datetime is required for one-time schedules"
        )
    
    # For DAILY schedules, recurrence_time is required
    if schedule_type == ScheduleTypeEnum.DAILY and not job_data.recurrence_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recurrence time (HH:MM) is required for daily schedules"
        )
    
    # For WEEKLY schedules, recurrence_time and recurrence_day are required
    if schedule_type == ScheduleTypeEnum.WEEKLY:
        if not job_data.recurrence_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recurrence time (HH:MM) is required for weekly schedules"
            )
        if not job_data.recurrence_day:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recurrence day (e.g., 'monday') is required for weekly schedules"
            )
    
    # For MONTHLY schedules, recurrence_time and recurrence_day are required
    if schedule_type == ScheduleTypeEnum.MONTHLY:
        if not job_data.recurrence_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recurrence time (HH:MM) is required for monthly schedules"
            )
        if not job_data.recurrence_day:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recurrence day (1-31) is required for monthly schedules"
            )
    
    # For YEARLY schedules, recurrence_time, recurrence_day, and recurrence_month are required
    if schedule_type == ScheduleTypeEnum.YEARLY:
        if not job_data.recurrence_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recurrence time (HH:MM) is required for yearly schedules"
            )
        if not job_data.recurrence_day:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recurrence day (1-31) is required for yearly schedules"
            )
        if not job_data.recurrence_month:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recurrence month (e.g., 'january') is required for yearly schedules"
            )

def create_merged_job_data(job: ScheduledJobModel, job_data: scheduled_job_schemas.ScheduledJobUpdate) -> Any:
    """
    Create a merged object with both existing and updated values for validation.
    
    Args:
        job: Existing job from database
        job_data: Updated job data
        
    Returns:
        Object containing merged data
    """
    # Create a simple object to hold the merged data
    class MergedData:
        pass
    
    merged = MergedData()
    
    # Start with existing values
    merged.start_datetime = job.start_datetime
    merged.recurrence_time = job.recurrence_time
    merged.recurrence_day = job.recurrence_day
    merged.recurrence_month = job.recurrence_month
    
    # Update with new values if provided
    update_data = job_data.model_dump(exclude_unset=True)
    
    if "start_datetime" in update_data:
        merged.start_datetime = update_data["start_datetime"]
    if "recurrence_time" in update_data:
        merged.recurrence_time = update_data["recurrence_time"]
    if "recurrence_day" in update_data:
        merged.recurrence_day = update_data["recurrence_day"]
    if "recurrence_month" in update_data:
        merged.recurrence_month = update_data["recurrence_month"]
    
    return merged

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_job_endpoint(
    job_id: str,
    current_user: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a scheduled job.
    
    Args:
        job_id: Scheduled job ID
        current_user: Current authenticated user
        db: Database session
    """
    # Use our permission check function to check permissions and get the job
    job = check_scheduled_job_access(
        principal=current_user,
        job_id_or_obj=job_id,
        required_scope="write:schedules",
        db=db
    )
    
    try:
        # Delete scheduled job
        result = delete_scheduled_job(db, job_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheduled job with ID {job_id} not found"
            )
        
        # Remove job from scheduler
        try:
            scheduler = get_scheduler()
            scheduler.cancel_job(job_id)
            logger.info(f"Job {job_id} removed from scheduler")
        except Exception as e:
            logger.error(f"Error removing job from scheduler: {str(e)}")
            # Continue anyway, as the job is deleted from the database
        
        logger.info(f"Scheduled job deleted: user={current_user.username}, job_id={job_id}")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error deleting scheduled job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting scheduled job: {str(e)}"
        )

@router.post("/{job_id}/toggle", response_model=scheduled_job_schemas.ScheduledJob)
async def toggle_scheduled_job_endpoint(
    job_id: str,
    toggle_data: scheduled_job_schemas.ScheduledJobToggle,
    current_user: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> scheduled_job_schemas.ScheduledJob:
    """
    Toggle a scheduled job's enabled status.
    
    Args:
        job_id: Scheduled job ID
        toggle_data: Toggle data (enabled status)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated scheduled job
    """
    # Use our permission check function to check permissions and get the job
    job = check_scheduled_job_access(
        principal=current_user,
        job_id_or_obj=job_id,
        required_scope="write:schedules",
        db=db
    )
    
    try:
        # Toggle scheduled job
        updated_job = toggle_scheduled_job(db, job_id, toggle_data.enabled)
        
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheduled job with ID {job_id} not found"
            )
        
        # Update job in scheduler
        try:
            scheduler = get_scheduler()
            
            if toggle_data.enabled:
                # Get device details
                device = get_device(db, updated_job.device_id)
                if not device:
                    logger.warning(f"Device {updated_job.device_id} not found for job {job_id}")
                    
                # Add job to scheduler using new architecture
                scheduler.schedule_job(
                    job_id=updated_job.id,
                    device_id=device.id if device else updated_job.device_id,
                    job_type=updated_job.job_type,
                    schedule_type=updated_job.schedule_type,
                    schedule_time=updated_job.schedule_time,
                    schedule_day=updated_job.schedule_day,
                    schedule_interval=updated_job.schedule_interval,
                    start_datetime=updated_job.start_datetime,
                    recurrence_time=updated_job.recurrence_time,
                    recurrence_day=updated_job.recurrence_day,
                    recurrence_month=updated_job.recurrence_month,
                    job_data=updated_job.job_data
                )
                
                logger.info(f"Job {job_id} enabled and scheduled")
            else:
                # Remove job from scheduler
                scheduler.cancel_job(job_id)
                logger.info(f"Job {job_id} disabled and removed from scheduler")
        except Exception as e:
            logger.error(f"Error updating job in scheduler: {str(e)}")
            # Continue anyway, as the job is updated in the database
        
        logger.info(f"Scheduled job toggled: user={current_user.username}, " 
                  f"job_id={job_id}, enabled={toggle_data.enabled}")
        return updated_job
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error toggling scheduled job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling scheduled job: {str(e)}"
        )

@router.post("/{job_id}/run", response_model=Dict[str, Any])
async def run_scheduled_job_endpoint(
    job_id: str,
    current_user: UserPrincipal = Depends(get_current_principal),
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
    # Use our permission check function to check permissions and get the job
    job = check_scheduled_job_access(
        principal=current_user,
        job_id_or_obj=job_id,
        required_scope="write:schedules",
        db=db
    )
    
    try:
        # Get device
        device = get_device(db, job.device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {job.device_id} not found"
            )
        
        # Use the scheduler service to run the job immediately
        scheduler_service = get_scheduler_service()
        result = scheduler_service.run_job(job_id, current_user.id)
        
        # Log the action
        logger.info(f"Scheduled job {job_id} ({job.name}) run manually by {current_user.username}")
        
        # Return result
        return {
            "job_id": job_id,
            "job_name": job.name,
            "device_id": device.id,
            "device_name": device.name,
            "result": result,
            "message": "Job started successfully" if result else "Failed to start job"
        }
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error running scheduled job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running scheduled job: {str(e)}"
        )

@router.post("/test/create-examples", response_model=Dict[str, Any])
async def create_example_jobs(
    device_id: str,
    current_user: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create example scheduled jobs for testing.
    
    Args:
        device_id: Device ID to use for the example jobs
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dictionary with created job IDs
    """
    # Check admin permission
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Check if device exists
        device = get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found"
            )
        
        # Create example jobs for each schedule type
        created_jobs = {}
        
        # 1. Immediate job
        immediate_job = scheduled_job_schemas.ScheduledJobCreate(
            name="Example Immediate Backup",
            device_id=device_id,
            job_type=JobTypeEnum.BACKUP,
            schedule_type=ScheduleTypeEnum.IMMEDIATE,
            enabled=True
        )
        immediate_result = create_scheduled_job(db, immediate_job, current_user.id)
        created_jobs["immediate"] = immediate_result.id
        
        # 2. One-time job (tomorrow)
        one_time_job = scheduled_job_schemas.ScheduledJobCreate(
            name="Example One-Time Backup",
            device_id=device_id,
            job_type=JobTypeEnum.BACKUP,
            schedule_type=ScheduleTypeEnum.ONE_TIME,
            start_datetime=datetime.utcnow() + timedelta(days=1),
            enabled=True
        )
        one_time_result = create_scheduled_job(db, one_time_job, current_user.id)
        created_jobs["one_time"] = one_time_result.id
        
        # 3. Daily job (every day at 3:00 AM)
        daily_job = scheduled_job_schemas.ScheduledJobCreate(
            name="Example Daily Backup",
            device_id=device_id,
            job_type=JobTypeEnum.BACKUP,
            schedule_type=ScheduleTypeEnum.DAILY,
            recurrence_time="03:00",
            enabled=True
        )
        daily_result = create_scheduled_job(db, daily_job, current_user.id)
        created_jobs["daily"] = daily_result.id
        
        # 4. Weekly job (every Monday at 4:00 AM)
        weekly_job = scheduled_job_schemas.ScheduledJobCreate(
            name="Example Weekly Backup",
            device_id=device_id,
            job_type=JobTypeEnum.BACKUP,
            schedule_type=ScheduleTypeEnum.WEEKLY,
            recurrence_day="monday",
            recurrence_time="04:00",
            enabled=True
        )
        weekly_result = create_scheduled_job(db, weekly_job, current_user.id)
        created_jobs["weekly"] = weekly_result.id
        
        # 5. Monthly job (1st day of every month at 2:00 AM)
        monthly_job = scheduled_job_schemas.ScheduledJobCreate(
            name="Example Monthly Backup",
            device_id=device_id,
            job_type=JobTypeEnum.BACKUP,
            schedule_type=ScheduleTypeEnum.MONTHLY,
            recurrence_day="1",
            recurrence_time="02:00",
            enabled=True
        )
        monthly_result = create_scheduled_job(db, monthly_job, current_user.id)
        created_jobs["monthly"] = monthly_result.id
        
        # 6. Yearly job (January 1st every year at 1:00 AM)
        yearly_job = scheduled_job_schemas.ScheduledJobCreate(
            name="Example Yearly Backup",
            device_id=device_id,
            job_type=JobTypeEnum.BACKUP,
            schedule_type=ScheduleTypeEnum.YEARLY,
            recurrence_month="january",
            recurrence_day="1",
            recurrence_time="01:00",
            enabled=True
        )
        yearly_result = create_scheduled_job(db, yearly_job, current_user.id)
        created_jobs["yearly"] = yearly_result.id
        
        # Load all jobs in the scheduler
        scheduler_service = get_scheduler_service()
        scheduler_service.load_jobs_from_db()
        
        logger.info(f"Created example scheduled jobs for testing: {created_jobs}")
        
        return {
            "message": "Example scheduled jobs created successfully",
            "created_jobs": created_jobs
        }
    except Exception as e:
        logger.exception(f"Error creating example scheduled jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating example scheduled jobs: {str(e)}"
        ) 