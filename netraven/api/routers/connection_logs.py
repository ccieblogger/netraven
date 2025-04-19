from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
import math

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user
from netraven.db import models

router = APIRouter(
    prefix="/connection-logs",
    tags=["Connection Logs"],
    dependencies=[Depends(get_current_active_user)] # Apply auth to all log routes
)

@router.get("/", response_model=schemas.log.PaginatedConnectionLogResponse)
def read_logs(
    job_id: Optional[int] = Query(None, description="Filter logs by Job ID"),
    device_id: Optional[int] = Query(None, description="Filter logs by Device ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve connection logs only, with filtering and pagination.
    - **job_id**: Filter logs by Job ID
    - **device_id**: Filter logs by Device ID
    - **page**: Page number (starts at 1)
    - **size**: Number of items per page
    """
    offset = (page - 1) * size
    query = db.query(models.ConnectionLog)
    if job_id is not None:
        query = query.filter(models.ConnectionLog.job_id == job_id)
    if device_id is not None:
        query = query.filter(models.ConnectionLog.device_id == device_id)
    total = query.count()
    logs = query.order_by(desc(models.ConnectionLog.timestamp)).offset(offset).limit(size).all()
    pages = math.ceil(total / size) if total > 0 else 1
    return {
        "items": logs,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    } 