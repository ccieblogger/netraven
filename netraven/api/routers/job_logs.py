from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
import math

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user
from netraven.db import models
from netraven.db.models.job import Job
from netraven.db.models.device import Device

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
    job_name: Optional[str] = Query(None, description="Filter logs by Job Name"),
    device_names: Optional[str] = Query(None, description="Comma-separated list of device names to filter"),
    job_type: Optional[str] = Query(None, description="Filter logs by Job Type"),
    search: Optional[str] = Query(None, description="Keyword search in message, job name, or device name"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve job logs with advanced filtering and pagination.
    - **job_id**: Filter logs by Job ID
    - **device_id**: Filter logs by Device ID
    - **level**: Filter job logs by level (ERROR, INFO, etc.)
    - **job_name**: Filter logs by Job Name
    - **device_names**: Comma-separated list of device names to filter
    - **job_type**: Filter logs by Job Type
    - **search**: Keyword search in message, job name, or device name
    - **page**: Page number (starts at 1)
    - **size**: Number of items per page
    """
    offset = (page - 1) * size
    query = db.query(models.JobLog, Job, Device)
    query = query.join(Job, models.JobLog.job_id == Job.id)
    query = query.outerjoin(Device, models.JobLog.device_id == Device.id)

    if job_id is not None:
        query = query.filter(models.JobLog.job_id == job_id)
    if device_id is not None:
        query = query.filter(models.JobLog.device_id == device_id)
    if level is not None:
        query = query.filter(models.JobLog.level == level)
    if job_name is not None:
        query = query.filter(Job.name == job_name)
    if device_names:
        names = [n.strip() for n in device_names.split(",") if n.strip()]
        if names:
            query = query.filter(Device.hostname.in_(names))
    if job_type is not None:
        query = query.filter(Job.job_type == job_type)
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(models.JobLog.message.ilike(search_term), Job.name.ilike(search_term), Device.hostname.ilike(search_term)))

    total = query.count()
    logs = query.order_by(models.JobLog.timestamp.desc()).offset(offset).limit(size).all()
    pages = math.ceil(total / size) if total > 0 else 1

    # Build response with enriched fields
    items = []
    for log, job, device in logs:
        item = schemas.log.JobLog.model_validate(log).model_dump()
        item["job_name"] = job.name if job else None
        item["device_name"] = device.hostname if device else None
        item["job_type"] = job.job_type if job else None
        items.append(item)

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/job-names", response_model=list)
def get_job_log_job_names(db: Session = Depends(get_db_session)):
    """
    Return unique job names that have job logs.
    """
    job_names = db.query(Job.name).join(models.JobLog, models.JobLog.job_id == Job.id).distinct().all()
    return [name for (name,) in job_names] 