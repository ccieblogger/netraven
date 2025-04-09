from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, text, union_all
from sqlalchemy.sql import select
import math

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user
from netraven.db import models

router = APIRouter(
    prefix="/logs",
    tags=["Logs"],
    dependencies=[Depends(get_current_active_user)] # Apply auth to all log routes
)

@router.get("/", response_model=schemas.log.PaginatedCombinedLogResponse)
def read_logs(
    job_id: Optional[int] = Query(None, description="Filter logs by Job ID"),
    device_id: Optional[int] = Query(None, description="Filter logs by Device ID"),
    log_type: Optional[str] = Query(None, description="Filter by log type ('job_log' or 'connection_log')"),
    level: Optional[str] = Query(None, description="Filter job logs by level (ERROR, INFO, etc.)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve job logs and connection logs, with filtering and pagination.
    
    - **job_id**: Filter logs by Job ID
    - **device_id**: Filter logs by Device ID
    - **log_type**: Filter by log type ('job_log' or 'connection_log')
    - **level**: Filter job logs by level (ERROR, INFO, etc.)
    - **page**: Page number (starts at 1)
    - **size**: Number of items per page
    """
    offset = (page - 1) * size
    
    # Start building queries for each log type
    job_log_query = db.query(
        models.JobLog.id, 
        models.JobLog.job_id,
        models.JobLog.device_id,
        models.JobLog.message.label('log'),  # Alias for unified schema
        models.JobLog.level,
        models.JobLog.timestamp,
        text("'job_log' as log_type")  # Add type discriminator
    )
    
    conn_log_query = db.query(
        models.ConnectionLog.id,
        models.ConnectionLog.job_id,
        models.ConnectionLog.device_id,
        models.ConnectionLog.log,
        text("null as level"),  # NULL for level in connection logs
        models.ConnectionLog.timestamp,
        text("'connection_log' as log_type")  # Add type discriminator
    )
    
    # Apply filters to both queries
    if job_id is not None:
        job_log_query = job_log_query.filter(models.JobLog.job_id == job_id)
        conn_log_query = conn_log_query.filter(models.ConnectionLog.job_id == job_id)
        
    if device_id is not None:
        job_log_query = job_log_query.filter(models.JobLog.device_id == device_id)
        conn_log_query = conn_log_query.filter(models.ConnectionLog.device_id == device_id)
    
    if level is not None:
        job_log_query = job_log_query.filter(models.JobLog.level == level)
    
    # Create the final query based on log_type filter
    if log_type == "job_log":
        query = job_log_query.order_by(desc(models.JobLog.timestamp))
        total = job_log_query.count()
    elif log_type == "connection_log":
        query = conn_log_query.order_by(desc(models.ConnectionLog.timestamp))
        total = conn_log_query.count()
    else:
        # Unified query with UNION ALL
        union_query = job_log_query.union_all(conn_log_query).subquery()
        query = db.query(union_query).order_by(desc(union_query.c.timestamp))
        
        # Count total records (this is more efficient than fetching all and counting in Python)
        total_job_logs = job_log_query.count()
        total_conn_logs = conn_log_query.count()
        total = total_job_logs + total_conn_logs
    
    # Apply pagination
    logs = query.offset(offset).limit(size).all()
    
    # Calculate pagination metadata
    pages = math.ceil(total / size) if total > 0 else 1
    
    # Transform raw query results to appropriate schema objects
    result_logs = []
    for log in logs:
        if log.log_type == "job_log":
            result_logs.append(schemas.log.JobLog(
                id=log.id,
                job_id=log.job_id,
                device_id=log.device_id,
                message=log.log,  # Using the aliased field
                level=log.level,
                timestamp=log.timestamp,
                log_type="job_log"
            ))
        else:  # connection_log
            result_logs.append(schemas.log.ConnectionLog(
                id=log.id,
                job_id=log.job_id,
                device_id=log.device_id,
                log=log.log,
                timestamp=log.timestamp,
                log_type="connection_log"
            ))
    
    # Return paginated response
    return {
        "items": result_logs,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

# Optional: Add endpoint to get a specific log entry by ID if needed later
# Requires determining if ID belongs to JobLog or ConnectionLog table
