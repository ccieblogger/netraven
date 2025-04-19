from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
import math

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user
from netraven.db import models

router = APIRouter(
    prefix="/job-logs",
    tags=["Job Logs"],
    dependencies=[Depends(get_current_active_user)]
)

@router.get("/", response_model=schemas.log.PaginatedJobLogResponse)
def read_job_logs(
    job_id: Optional[int] = Query(None, description="Filter logs by Job ID"),
    device_id: Optional[int] = Query(None, description="Filter logs by Device ID"),
    level: Optional[str] = Query(None, description="Filter job logs by level (ERROR, INFO, etc.)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve job logs only, with filtering and pagination.
    - **job_id**: Filter logs by Job ID
    - **device_id**: Filter logs by Device ID
    - **level**: Filter job logs by level (ERROR, INFO, etc.)
    - **page**: Page number (starts at 1)
    - **size**: Number of items per page
    """
    offset = (page - 1) * size
    query = db.query(models.JobLog)
    if job_id is not None:
        query = query.filter(models.JobLog.job_id == job_id)
    if device_id is not None:
        query = query.filter(models.JobLog.device_id == device_id)
    if level is not None:
        query = query.filter(models.JobLog.level == level)
    total = query.count()
    logs = query.order_by(desc(models.JobLog.timestamp)).offset(offset).limit(size).all()
    pages = math.ceil(total / size) if total > 0 else 1
    return {
        "items": logs,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    } 