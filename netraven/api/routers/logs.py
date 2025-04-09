from typing import List, Union, TypeVar, Generic
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import math

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user
from netraven.db import models

# Define a type variable for the paginated response items
T = TypeVar('T')

# Define a generic Pydantic model for paginated responses
class PaginatedResponse(schemas.BaseSchema, Generic[T]):
    total_items: int
    total_pages: int
    current_page: int
    page_size: int
    items: List[T]


router = APIRouter(
    prefix="/logs",
    tags=["Logs"],
    dependencies=[Depends(get_current_active_user)] # Apply auth to all log routes
)

# Define a union type for the response model items
LogEntry = Union[schemas.log.JobLog, schemas.log.ConnectionLog]

@router.get("/", response_model=PaginatedResponse[LogEntry])
def read_logs(
    job_id: int | None = Query(default=None, description="Filter logs by Job ID"),
    device_id: int | None = Query(default=None, description="Filter logs by Device ID"),
    log_type: str | None = Query(default=None, description="Filter by log type ('job' or 'connection')"),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"), # Changed default and max size
    db: Session = Depends(get_db_session)
):
    """Retrieve job logs and connection logs, with optional filtering and pagination.

    Returns a combined list sorted by timestamp, with pagination metadata.
    """
    # Calculate offset
    offset = (page - 1) * size

    # Base queries
    job_log_query = db.query(models.JobLog)
    conn_log_query = db.query(models.ConnectionLog)

    # Apply filters
    if job_id is not None:
        job_log_query = job_log_query.filter(models.JobLog.job_id == job_id)
        conn_log_query = conn_log_query.filter(models.ConnectionLog.job_id == job_id)

    if device_id is not None:
        job_log_query = job_log_query.filter(models.JobLog.device_id == device_id)
        conn_log_query = conn_log_query.filter(models.ConnectionLog.device_id == device_id)

    # Combine queries if possible before counting/fetching for efficiency
    # Note: Combining Union queries in SQLAlchemy for pagination and total count can be complex.
    # This approach fetches filtered lists, combines, sorts, then counts/paginates in Python.
    # For very large datasets, a more complex SQL-level UNION or view might be needed.

    job_logs = []
    conn_logs = []
    if log_type is None or log_type == 'job':
        job_logs = job_log_query.order_by(models.JobLog.timestamp.desc()).all()
    if log_type is None or log_type == 'connection':
        conn_logs = conn_log_query.order_by(models.ConnectionLog.timestamp.desc()).all()

    # Combine and sort results (in memory)
    combined_logs = sorted(
        job_logs + conn_logs,
        key=lambda log: log.timestamp,
        reverse=True
    )

    # Calculate total items based on the combined list
    total_items = len(combined_logs)
    total_pages = math.ceil(total_items / size)

    # Apply pagination to the combined list (in memory)
    paginated_logs = combined_logs[offset : offset + size]

    return PaginatedResponse(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        page_size=size,
        items=paginated_logs
    )

# Optional: Add endpoint to get a specific log entry by ID if needed later
# Requires determining if ID belongs to JobLog or ConnectionLog table
