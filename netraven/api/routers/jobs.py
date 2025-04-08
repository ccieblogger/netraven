from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user, require_admin_role
from netraven.db import models

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
    """Create a new job definition."""
    # Check for duplicate name?
    existing_job = db.query(models.Job).filter(models.Job.name == job.name).first()
    if existing_job:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job name already exists")

    db_job = models.Job(
        **job.model_dump(exclude={'tags'}),
        status="pending" # Initial status
    )
    
    # Handle tags
    if job.tags:
        tags = get_tags_by_ids(db, job.tags)
        db_job.tags = tags

    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    # Eager load tags for response
    db.query(models.Job).options(selectinload(models.Job.tags)).filter(models.Job.id == db_job.id).first()
    return db_job

@router.get("/", response_model=List[schemas.job.Job])
def list_jobs(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False, # Optional filter
    db: Session = Depends(get_db_session)
):
    """Retrieve a list of job definitions."""
    query = db.query(models.Job).options(selectinload(models.Job.tags))
    if enabled_only:
        query = query.filter(models.Job.is_enabled == True)
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs

@router.get("/{job_id}", response_model=schemas.job.Job)
def get_job(
    job_id: int,
    db: Session = Depends(get_db_session)
):
    """Retrieve a specific job definition by ID."""
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
    """Update a job definition."""
    db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

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
    """Delete a job definition."""
    db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

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
    """Manually trigger a job to run immediately via the background worker queue."""
    db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    if not db_job.is_enabled:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is disabled")

    if rq_queue is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis connection not available for job queuing.")

    try:
        # Enqueue the job using the worker's run_job function
        # The actual execution happens in a separate worker process listening to the queue.
        enqueued_job = rq_queue.enqueue(run_worker_job, job_id) 
        return {"status": "queued", "job_id": job_id, "queue_job_id": enqueued_job.id}
    except Exception as e:
        # Log the error appropriately
        print(f"ERROR: Failed to enqueue job {job_id}: {e}") 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to queue job: {e}")
