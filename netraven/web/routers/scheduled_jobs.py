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
import os

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
from netraven.core.logging import get_logger
from netraven.jobs.scheduler import get_scheduler
from netraven.web.models.job_log import JobLog as JobLogModel

# Create router
router = APIRouter(prefix="", tags=["scheduled-jobs"])

# Initialize logger
logger = get_logger("netraven.web.routers.scheduled_jobs")

@router.get("", response_model=List[scheduled_job_schemas.ScheduledJobWithDevice])
async def list_scheduled_jobs(
    device_id: Optional[str] = None,
    schedule_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserPrincipal = Depends(get_current_principal),
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
        
        logger.info(f"Access granted: user={current_user.username}, " 
                  f"resource=scheduled_jobs, scope=read:schedules, count={len(result)}")
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

@router.get("/{job_id}", response_model=scheduled_job_schemas.ScheduledJobComplete)
async def get_scheduled_job_details(
    job_id: str,
    current_user: UserPrincipal = Depends(get_current_principal),
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
        
        logger.info(f"Access granted: user={current_user.username}, " 
                  f"resource=scheduled_job:{job_id}, scope=read:schedules, action=get_details")
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

@router.post("", response_model=scheduled_job_schemas.ScheduledJob, status_code=status.HTTP_201_CREATED)
async def create_scheduled_job_endpoint(
    job_data: scheduled_job_schemas.ScheduledJobCreate,
    current_user: UserPrincipal = Depends(get_current_principal),
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
    # Check permission
    if not current_user.has_scope("write:schedules") and not current_user.is_admin:
        logger.warning(f"Access denied: user={current_user.username}, " 
                     f"resource=scheduled_jobs, scope=write:schedules, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: write:schedules required"
        )
    
    try:
        # Check if user has access to the device
        device = check_device_access(
            principal=current_user,
            device_id_or_obj=job_data.device_id,
            required_scope="read:devices",
            db=db
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
        
        # Create the scheduled job
        job = create_scheduled_job(db, job_data, current_user.id)
        
        # Get scheduler instance
        scheduler = get_scheduler()
        
        # Add job to scheduler
        try:
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
        
        logger.info(f"Access granted: user={current_user.username}, " 
                  f"resource=scheduled_job:{job.id}, scope=write:schedules, action=create, name={job.name}")
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

@router.put("/{job_id}", response_model=scheduled_job_schemas.ScheduledJob)
async def update_scheduled_job_endpoint(
    job_id: str,
    job_data: scheduled_job_schemas.ScheduledJobUpdate,
    current_user: UserPrincipal = Depends(get_current_principal),
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
    # Use our permission check function to check permissions and get the job
    job = check_scheduled_job_access(
        principal=current_user,
        job_id_or_obj=job_id,
        required_scope="write:schedules",
        db=db
    )
    
    try:
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
        
        # Update the scheduled job
        updated_job = update_scheduled_job(db, job_id, update_data)
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheduled job with ID {job_id} not found"
            )
        
        # Update scheduler if job is enabled
        if updated_job.enabled:
            # Get device info for scheduler
            device = get_device(db, updated_job.device_id)
            
            # Get scheduler instance
            scheduler = get_scheduler()
            
            # Update job in scheduler
            try:
                # First remove the old job if it exists
                scheduler.remove_job(job_id)
                
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
        
        logger.info(f"Access granted: user={current_user.username}, " 
                  f"resource=scheduled_job:{job_id}, scope=write:schedules, action=update, name={updated_job.name}")
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
            scheduler.remove_job(job_id)
        except Exception as e:
            logger.error(f"Error removing job from scheduler: {e}")
            # Continue anyway, as the job is deleted from the database
        
        logger.info(f"Access granted: user={current_user.username}, " 
                  f"resource=scheduled_job:{job_id}, scope=write:schedules, action=delete")
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
        toggle_data: Toggle data
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
                scheduler.remove_job(job_id)
        except Exception as e:
            logger.error(f"Error updating job in scheduler: {e}")
            # Continue anyway, as the job is updated in the database
        
        logger.info(f"Access granted: user={current_user.username}, " 
                  f"resource=scheduled_job:{job_id}, scope=write:schedules, action=toggle, enabled={toggle_data.enabled}")
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
        
        # Create a unique job run ID
        run_id = str(uuid.uuid4())
        
        # Update last run time
        update_job_last_run(db, job_id)
        
        # Create a job log entry
        job_log = JobLogModel(
            id=run_id,
            session_id=run_id,
            job_type="manual_backup",  # Always backup type for scheduled jobs
            status="running",
            start_time=datetime.utcnow(),
            device_id=device.id,
            created_by=current_user.id,
            job_data={
                "scheduled_job_id": job_id,
                "scheduled_job_name": job.name,
                "device_hostname": device.hostname,
                "device_ip": device.ip_address
            }
        )
        db.add(job_log)
        db.commit()
        
        # Import gateway client here to avoid circular imports
        from netraven.gateway.client import GatewayClient
        from netraven.core.auth import create_token
        from datetime import timedelta
        
        # Create service token for gateway
        token = create_token(
            subject="scheduler",
            token_type="service",
            scopes=["admin:*"],
            expiration=timedelta(minutes=10)  # 10 minutes expiration
        )
        
        # Get gateway URL
        gateway_url = os.environ.get("GATEWAY_URL", "http://device_gateway:8001")
        
        # Create gateway client
        gateway = GatewayClient(
            gateway_url=gateway_url,
            token=token,
            client_id=f"scheduler-{current_user.username}"
        )
        
        # Execute backup
        try:
            backup_result = gateway.backup_device_config(
                host=device.ip_address,
                username=device.username,
                password=device.password,
                device_type=device.device_type,
                port=device.port,
                device_id=device.id
            )
            
            # Update job log with result
            job_log.status = "completed" if backup_result.get("status") == "success" else "failed"
            job_log.end_time = datetime.utcnow()
            job_log.result_message = (
                "Backup completed successfully" 
                if backup_result.get("status") == "success" 
                else f"Backup failed: {backup_result.get('message', 'Unknown error')}"
            )
            db.commit()
            
            logger.info(f"Access granted: user={current_user.username}, " 
                      f"resource=scheduled_job:{job_id}, scope=write:schedules, action=run, name={job.name}")
            
            return {
                "job_id": job_id,
                "run_id": run_id,
                "status": job_log.status,
                "result": backup_result
            }
        except Exception as exec_error:
            # Update job log with error
            job_log.status = "failed"
            job_log.end_time = datetime.utcnow()
            job_log.result_message = f"Error executing backup: {str(exec_error)}"
            db.commit()
            
            logger.error(f"Error executing manual backup for job {job_id}: {str(exec_error)}")
            
            return {
                "job_id": job_id,
                "run_id": run_id,
                "status": "failed",
                "error": str(exec_error)
            }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error running scheduled job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running scheduled job: {str(e)}"
        ) 