"""Job management router for scheduling and executing device operations.

This module provides API endpoints for managing job definitions in the system.
It implements CRUD operations for jobs as well as job triggering functionality
to initiate device operations on demand.

The router handles job creation, retrieval, update, and deletion, with
filtering and pagination capabilities. It also provides integration with
Redis Queue (RQ) for job execution.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_
from datetime import datetime, timedelta
from croniter import croniter
from netraven.utils.unified_logger import get_unified_logger

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user, require_admin_role
from netraven.db import models
from netraven.db.models import Job, Device, Log
from netraven.api.schemas.job import (
    ScheduledJobSummary, RecentJobExecution, JobTypeSummary, JobDashboardStatus, RQQueueStatus, WorkerStatus
)
from netraven.api.schemas.tag import Tag as TagSchema

# Potentially move to utils?
from .devices import get_tags_by_ids # Reuse tag helper from device router for now

from netraven.worker.job_registry import JOB_TYPE_META

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
    dependencies=[Depends(get_current_active_user)]
)

logger = get_unified_logger()

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

@router.get("/scheduled", response_model=List[ScheduledJobSummary])
def get_scheduled_jobs(db: Session = Depends(get_db_session)):
    """Return all enabled jobs with a schedule (interval/cron/onetime), including next run time."""
    jobs = db.query(models.Job).options(selectinload(models.Job.tags)).filter(models.Job.is_enabled == True).all()
    result = []
    now = datetime.utcnow()
    for job in jobs:
        # Only include jobs with a schedule
        if not job.schedule_type:
            continue
        # Calculate next_run
        next_run = None
        if job.schedule_type == "interval" and job.started_at:
            next_run = job.started_at + timedelta(seconds=job.interval_seconds or 0)
        elif job.schedule_type == "cron" and job.cron_string:
            try:
                base = job.started_at or now
                next_run = croniter(job.cron_string, base).get_next(datetime)
            except Exception:
                next_run = None
        elif job.schedule_type == "onetime" and job.scheduled_for:
            next_run = job.scheduled_for if (not job.completed_at or job.completed_at < job.scheduled_for) else None
        # Defensive: ensure all required fields are present and not None
        result.append(ScheduledJobSummary(
            id=job.id,
            name=job.name or "",
            job_type=job.job_type or "",
            description=job.description,
            schedule_type=job.schedule_type or None,
            interval_seconds=job.interval_seconds if job.interval_seconds is not None else None,
            cron_string=job.cron_string or None,
            scheduled_for=job.scheduled_for or None,
            next_run=next_run,
            tags=job.tags or [],
            is_enabled=job.is_enabled if job.is_enabled is not None else True,
            is_system_job=job.is_system_job if job.is_system_job is not None else False
        ))
    return result

@router.get("/recent", response_model=List[RecentJobExecution])
def get_recent_jobs(db: Session = Depends(get_db_session), limit: int = 20):
    """Return recent job executions (completed jobs, sorted by run time desc, with duration and device info)."""
    jobs = db.query(models.Job).options(selectinload(models.Job.tags)).filter(models.Job.completed_at != None).order_by(models.Job.completed_at.desc()).limit(limit).all()
    result = []
    for job in jobs:
        # Duration
        duration = None
        if job.started_at and job.completed_at:
            duration = (job.completed_at - job.started_at).total_seconds()
        # Devices (from tags or device_id)
        devices = []
        if job.device_id:
            dev = db.query(Device).filter(Device.id == job.device_id).first()
            if dev:
                devices.append({"id": dev.id, "name": dev.hostname})
        else:
            # Devices from tags
            for tag in job.tags or []:
                for dev in getattr(tag, "devices", []) or []:
                    devices.append({"id": dev.id, "name": dev.hostname})
        # Remove duplicates
        seen = set()
        unique_devices = []
        for d in devices:
            if d["id"] not in seen:
                unique_devices.append(d)
                seen.add(d["id"])
        # Defensive: ensure all required fields are present and not None
        result.append(RecentJobExecution(
            id=job.id,
            name=job.name or "",
            job_type=job.job_type or "",
            run_time=job.completed_at or job.started_at or datetime.utcnow(),
            duration=duration,
            status=job.status or "",
            devices=unique_devices if unique_devices is not None else [],
            tags=job.tags or [],
            is_system_job=job.is_system_job if job.is_system_job is not None else False
        ))
    return result

@router.get("/job-types", response_model=List[JobTypeSummary])
def get_job_types(db: Session = Depends(get_db_session)):
    """Return list of available job types, their labels, descriptions, icons, and last-used timestamp. Deduplicate aliases."""
    job_type_meta = JOB_TYPE_META
    last_used_map = {}
    jobs = db.query(models.Job).all()
    for job in jobs:
        jt = job.job_type
        ts = job.completed_at or job.started_at or job.scheduled_for
        if jt and ts:
            if jt not in last_used_map or (last_used_map[jt] and ts > last_used_map[jt]):
                last_used_map[jt] = ts
    result = []
    seen_signatures = set()
    for jt, meta in job_type_meta.items():
        # Build a signature of label, description, icon to deduplicate aliases
        sig = (meta.get("label"), meta.get("description"), meta.get("icon"))
        if sig in seen_signatures:
            continue  # Skip aliases/duplicates
        seen_signatures.add(sig)
        result.append(JobTypeSummary(
            job_type=jt,
            label=meta.get("label", jt),
            description=meta.get("description"),
            icon=meta.get("icon"),
            last_used=last_used_map.get(jt)
        ))
    return result

@router.get("/status", response_model=JobDashboardStatus)
def get_jobs_status():
    """Return Redis, RQ, and worker status for job/queue/worker dashboard cards only.
    This endpoint does NOT provide system-wide health (see /system/status).
    """
    from rq import Queue, Worker
    from redis import Redis
    from netraven.config.loader import load_config
    config = load_config()
    redis_url = config.get('scheduler', {}).get('redis_url', 'redis://localhost:6379/0')
    try:
        redis_conn = Redis.from_url(redis_url)
        info = redis_conn.info()
        redis_uptime = info.get('uptime_in_seconds')
        redis_memory = info.get('used_memory')
        redis_last_heartbeat = None  # Not tracked unless using Redis Sentinel
    except Exception as e:
        logger.log(f"Failed to get Redis info: {e}", level="ERROR", destinations=["stdout", "file", "db"], source="jobs_router")
        redis_uptime = None
        redis_memory = None
        redis_last_heartbeat = None
        info = {}
        redis_conn = None
    # RQ Queues
    rq_queues = []
    try:
        if redis_conn:
            for qname in ['default', 'high', 'low']:
                q = Queue(qname, connection=redis_conn)
                jobs = q.jobs
                job_count = len(jobs)
                oldest_job_ts = None
                if jobs:
                    oldest_job_ts = jobs[0].enqueued_at if hasattr(jobs[0], 'enqueued_at') else None
                rq_queues.append(RQQueueStatus(
                    name=qname,
                    job_count=job_count,
                    oldest_job_ts=oldest_job_ts
                ))
    except Exception as e:
        logger.log(f"Failed to get RQ queue info: {e}", level="ERROR", destinations=["stdout", "file", "db"], source="jobs_router")
    # Workers
    workers = []
    try:
        if redis_conn:
            for w in Worker.all(connection=redis_conn):
                jobs_in_progress = len(w.get_current_job_ids()) if hasattr(w, 'get_current_job_ids') else 0
                workers.append(WorkerStatus(
                    id=w.name,
                    status=w.state if hasattr(w, 'state') else 'unknown',
                    jobs_in_progress=jobs_in_progress
                ))
    except Exception as e:
        logger.log(f"Failed to get worker info: {e}", level="ERROR", destinations=["stdout", "file", "db"], source="jobs_router")
    return JobDashboardStatus(
        redis_uptime=redis_uptime,
        redis_memory=redis_memory,
        redis_last_heartbeat=redis_last_heartbeat,
        rq_queues=rq_queues,
        workers=workers
    )

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
    logger.log("Successfully connected to Redis for RQ.", level="INFO", destinations=["stdout", "file", "db"], source="jobs_router")
except Exception as e:
    logger.log(f"ERROR: Could not connect to Redis at {redis_url} for RQ. Job trigger endpoint will fail.", level="ERROR", destinations=["stdout", "file", "db"], source="jobs_router")
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
    db: Session = Depends(get_db_session),
    response: Response = None
):
    """[DEPRECATED] Return per-device job results for a given job.\n\n    This endpoint is deprecated and will be removed in a future release.\n    Use `/job-results/?job_id=...` for canonical per-device job status.\n    """
    logger.warning("[DEPRECATED] /jobs/{job_id}/devices called. This endpoint will be removed in a future release. Use /job-results/?job_id=... instead.")
    if response is not None:
        response.headers["Deprecation"] = "true"
        response.headers["Deprecation-Notice"] = "/jobs/{job_id}/devices is deprecated and will be removed. Use /job-results/?job_id=... instead."
    # Query all job logs for this job that are associated with a device
    logs = (
        db.query(Log, Device)
        .join(Device, Log.device_id == Device.id)
        .filter(Log.job_id == job_id, Log.log_type == "job")
        .all()
    )
    results = []
    for log, device in logs:
        results.append({
            "device_id": device.id,
            "device_name": device.hostname,
            "device_ip": device.ip_address,
            "log": log.model_dump(),
        })
    return {
        "deprecation_notice": "/jobs/{job_id}/devices is deprecated and will be removed. Use /job-results/?job_id=... instead.",
        "results": results
    }
