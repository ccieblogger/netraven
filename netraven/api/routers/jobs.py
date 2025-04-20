"""Job management router for scheduling and executing device operations.

This module provides API endpoints for managing job definitions in the system.
It implements CRUD operations for jobs as well as job triggering functionality
to initiate device operations on demand.

The router handles job creation, retrieval, update, and deletion, with
filtering and pagination capabilities. It also provides integration with
Redis Queue (RQ) for job execution.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_
from datetime import datetime

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user, require_admin_role
from netraven.db import models
from netraven.db.models import JobLog, Device
from netraven.api.schemas.log import JobLog as JobLogSchema

# Potentially move to utils?
from .devices import get_tags_by_ids # Reuse tag helper from device router for now

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
    dependencies=[Depends(get_current_active_user)]
)

@router.post("/", response_model=schemas.job.Job, status_code=status.HTTP_201_CREATED)
def create_job(
    job: schemas.job.JobCreate,
    db: Session = Depends(get_db_session),
):
    """Create a new job definition.
    
    Registers a new job with the provided details and assigns tags or device_id if specified.
    Jobs are used to define operations that will be performed on network devices,
    either on-demand or according to a schedule.
    
    Args:
        job: Job creation schema with job details
        db: Database session
        
    Returns:
        The created job object with its assigned ID
        
    Raises:
        HTTPException (400): If the job name already exists
        HTTPException (404): If any of the specified tags don't exist
    """
    # Check for duplicate name?
    existing_job = db.query(models.Job).filter(models.Job.name == job.name).first()
    if existing_job:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job name already exists")

    # Prepare job data
    job_data = job.model_dump(exclude={'tags'})
    db_job = models.Job(
        **job_data,
        status="pending" # Initial status
    )

    # Handle tags or device_id
    if job.device_id is not None:
        db_job.device_id = job.device_id
        db_job.tags = []  # Ensure no tags are set
    elif job.tags:
        tags = get_tags_by_ids(db, job.tags)
        db_job.tags = tags
        db_job.device_id = None
    else:
        # Should not happen due to schema validation, but double check
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either device_id or tags must be provided.")

    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    # Eager load tags for response
    db.query(models.Job).options(selectinload(models.Job.tags)).filter(models.Job.id == db_job.id).first()
    return db_job

@router.get("/", response_model=schemas.job.PaginatedJobResponse)
def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    name: Optional[str] = None,
    status: Optional[str] = None,
    is_enabled: Optional[bool] = None, 
    schedule_type: Optional[str] = None,
    tag_id: Optional[List[int]] = Query(None, description="Filter by tag IDs"),
    db: Session = Depends(get_db_session)
):
    """Retrieve a list of job definitions with pagination and filtering.
    
    Returns a paginated list of jobs with optional filtering by name,
    status, enabled state, schedule type, and tags.
    
    Args:
        page: Page number (starts at 1)
        size: Number of items per page (1-100)
        name: Optional filter by job name (partial match)
        status: Optional filter by job status (e.g., "pending", "running", "completed")
        is_enabled: Optional filter by enabled/disabled state
        schedule_type: Optional filter by schedule type (interval, cron, onetime)
        tag_id: Optional filter by tag IDs (can specify multiple)
        db: Database session
        
    Returns:
        Paginated response containing job items, total count, and pagination info
    """
    query = db.query(models.Job).options(selectinload(models.Job.tags))
    
    # Apply filters
    filters = []
    if name:
        filters.append(models.Job.name.ilike(f"%{name}%"))
    if status:
        filters.append(models.Job.status == status)
    if is_enabled is not None:
        filters.append(models.Job.is_enabled == is_enabled)
    if schedule_type:
        filters.append(models.Job.schedule_type == schedule_type)
    
    # Apply all filters
    if filters:
        query = query.filter(and_(*filters))
    
    # Apply tag filter if specified
    if tag_id:
        query = query.join(models.Job.tags).filter(models.Tag.id.in_(tag_id)).group_by(models.Job.id)
    
    # Get total count for pagination
    total = query.count()
    
    # Calculate pagination values
    pages = (total + size - 1) // size
    offset = (page - 1) * size
    
    # Get paginated jobs
    jobs = query.offset(offset).limit(size).all()
    
    # Return paginated response
    return {
        "items": jobs,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/{job_id}", response_model=schemas.job.Job)
def get_job(
    job_id: int,
    db: Session = Depends(get_db_session)
):
    """Retrieve a specific job definition by ID.
    
    Fetches detailed information about a single job, including
    its assigned tags.
    
    Args:
        job_id: ID of the job to retrieve
        db: Database session
        
    Returns:
        Job object with its details and tags
        
    Raises:
        HTTPException (404): If the job with the specified ID is not found
    """
    db_job = (
        db.query(models.Job)
        .options(selectinload(models.Job.tags))
        .filter(models.Job.id == job_id)
        .first()
    )
    if db_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return db_job

@router.put("/{job_id}", response_model=schemas.job.Job)
def update_job(
    job_id: int,
    job: schemas.job.JobUpdate,
    db: Session = Depends(get_db_session)
):
    """Update an existing job definition.
    
    Updates the specified job with the provided information.
    Only fields that are explicitly set in the request will be updated.
    
    Args:
        job_id: ID of the job to update
        job: Update schema containing fields to update
        db: Database session
        
    Returns:
        Updated job object
        
    Raises:
        HTTPException (404): If the job with the specified ID is not found
        HTTPException (400): If the new job name already exists
        HTTPException (404): If any of the specified tags don't exist
    """
    db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if db_job.is_system_job:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System jobs cannot be updated.")

    update_data = job.model_dump(exclude_unset=True)

    # Check for name conflict
    if 'name' in update_data and update_data['name'] != db_job.name:
        if db.query(models.Job).filter(models.Job.name == update_data['name']).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job name already exists")

    for key, value in update_data.items():
        if key != "tags":
            setattr(db_job, key, value)
    
    # Handle tags update
    if "tags" in update_data:
        if update_data["tags"] is None:
            db_job.tags = []
        else:
            tags = get_tags_by_ids(db, update_data["tags"])
            db_job.tags = tags

    db.commit()
    db.refresh(db_job)
    # Eager load tags for response
    db.query(models.Job).options(selectinload(models.Job.tags)).filter(models.Job.id == job_id).first()
    return db_job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db_session),
    _: models.User = Depends(require_admin_role) # Protect deletion
):
    """Delete a job definition.
    
    Removes the specified job from the system. This operation cannot be undone.
    This endpoint requires admin privileges.
    
    Args:
        job_id: ID of the job to delete
        db: Database session
        _: Current user with admin role (injected by dependency)
        
    Returns:
        No content (204) if successful
        
    Raises:
        HTTPException (404): If the job with the specified ID is not found
        HTTPException (403): If the user does not have admin privileges
    """
    db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if db_job.is_system_job:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System jobs cannot be deleted.")

    # TODO: Consider implications - should deleting a job also cancel scheduled RQ jobs?
    # This might require interaction with the scheduler or RQ itself.

    db.delete(db_job)
    db.commit()
    return None

# --- Job Execution Endpoint (Moved from placeholder) ---

from rq import Queue
from redis import Redis
from netraven.config.loader import load_config
# Assuming worker runner is the target function defined in the SOTs
# Adjust the import path if the worker/scheduler structure differs
from netraven.worker.runner import run_job as run_worker_job 

config = load_config()
redis_url = config.get('scheduler', {}).get('redis_url', 'redis://localhost:6379/0')
try:
    redis_conn = Redis.from_url(redis_url)
    rq_queue = Queue(connection=redis_conn)
    redis_conn.ping() # Check connection
    print("Successfully connected to Redis for RQ.")
except Exception as e:
    print(f"ERROR: Could not connect to Redis at {redis_url} for RQ. Job trigger endpoint will fail.")
    print(f"Error details: {e}")
    # Set queue to None or handle differently so endpoint fails gracefully
    rq_queue = None 

@router.post("/run/{job_id}", status_code=status.HTTP_202_ACCEPTED, summary="Trigger a Job Manually")
async def trigger_job_run(
    job_id: int, 
    db: Session = Depends(get_db_session)
):
    """Trigger immediate execution of a job.
    
    Enqueues the specified job for immediate execution using Redis Queue.
    The job will be executed asynchronously, and the endpoint returns 
    immediately with an "Accepted" status.
    
    Args:
        job_id: ID of the job to trigger
        db: Database session
        
    Returns:
        Acceptance message with job details and queue status
        
    Raises:
        HTTPException (404): If the job with the specified ID is not found
        HTTPException (503): If the Redis Queue connection is not available
    """
    # Check if RQ is set up
    if not rq_queue:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job queue is not available. Check Redis connection."
        )
        
    # Check if job exists
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    # Update job status to 'queued'
    job.status = "queued"
    job.last_run_time = datetime.utcnow()
    db.commit()
    
    # Enqueue the job using RQ
    rq_job = rq_queue.enqueue(run_worker_job, job_id)
    
    return {
        "message": "Job triggered successfully", 
        "job_id": job_id,
        "job_name": job.name,
        "queue_job_id": rq_job.id
    }

@router.get("/{job_id}/devices", response_model=List[dict])
def get_job_device_results(
    job_id: int,
    db: Session = Depends(get_db_session)
):
    """Return per-device job results for a given job."""
    # Query all job logs for this job that are associated with a device
    logs = (
        db.query(JobLog, Device)
        .join(Device, JobLog.device_id == Device.id)
        .filter(JobLog.job_id == job_id)
        .all()
    )
    results = []
    for log, device in logs:
        results.append({
            "device_id": device.id,
            "device_name": device.hostname,
            "device_ip": device.ip_address,
            "log": JobLogSchema.model_validate(log).model_dump(),
        })
    return results
