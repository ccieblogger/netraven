from typing import List, Union
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user
from netraven.db import models

router = APIRouter(
    prefix="/logs",
    tags=["Logs"],
    dependencies=[Depends(get_current_active_user)] # Apply auth to all log routes
)

# Define a union type for the response model
LogEntry = Union[schemas.log.JobLog, schemas.log.ConnectionLog]

@router.get("/", response_model=List[LogEntry])
def read_logs(
    job_id: int | None = Query(default=None, description="Filter logs by Job ID"),
    device_id: int | None = Query(default=None, description="Filter logs by Device ID"),
    log_type: str | None = Query(default=None, description="Filter by log type ('job' or 'connection')"),
    skip: int = Query(default=0, ge=0), 
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db_session)
):
    """Retrieve job logs and connection logs, with optional filtering.
    
    Returns a combined list sorted by timestamp.
    """
    job_log_query = db.query(models.JobLog)
    conn_log_query = db.query(models.ConnectionLog)

    if job_id is not None:
        job_log_query = job_log_query.filter(models.JobLog.job_id == job_id)
        conn_log_query = conn_log_query.filter(models.ConnectionLog.job_id == job_id)

    if device_id is not None:
        job_log_query = job_log_query.filter(models.JobLog.device_id == device_id)
        conn_log_query = conn_log_query.filter(models.ConnectionLog.device_id == device_id)

    # Fetch results based on log_type filter
    job_logs = []
    conn_logs = []
    if log_type is None or log_type == 'job':
        job_logs = job_log_query.order_by(models.JobLog.timestamp.desc()).all()
    if log_type is None or log_type == 'connection':
        conn_logs = conn_log_query.order_by(models.ConnectionLog.timestamp.desc()).all()

    # Combine and sort results
    combined_logs = sorted(
        job_logs + conn_logs, 
        key=lambda log: log.timestamp, 
        reverse=True
    )

    # Apply pagination to the combined list
    paginated_logs = combined_logs[skip : skip + limit]

    return paginated_logs

# Optional: Add endpoint to get a specific log entry by ID if needed later
# Requires determining if ID belongs to JobLog or ConnectionLog table
