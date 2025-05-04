from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime

from netraven.api.dependencies import get_db_session, get_current_active_user
from netraven.db.models import JobResult, Device, Job, Tag
from netraven.api.schemas.job_result import JobResultRead, PaginatedJobResultResponse
from netraven.utils.unified_logger import get_unified_logger

router = APIRouter(
    prefix="/job-results",
    tags=["Job Results"],
    dependencies=[Depends(get_current_active_user)]
)

logger = get_unified_logger()

@router.get("/", response_model=PaginatedJobResultResponse)
def list_job_results(
    device_id: Optional[int] = Query(None),
    job_id: Optional[int] = Query(None),
    tag_id: Optional[int] = Query(None),
    job_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_session)
):
    """Retrieve job results with flexible filtering and pagination."""
    query = db.query(JobResult)
    filters = []
    if device_id:
        filters.append(JobResult.device_id == device_id)
    if job_id:
        filters.append(JobResult.job_id == job_id)
    if job_type:
        filters.append(JobResult.job_type == job_type)
    if status:
        filters.append(JobResult.status == status)
    if start_time:
        filters.append(JobResult.result_time >= start_time)
    if end_time:
        filters.append(JobResult.result_time <= end_time)
    # Tag filter (join to DeviceTagAssociation or Job.tags)
    if tag_id:
        # Devices with this tag
        device_ids = db.query(Device.id).join(Device.tags).filter(Tag.id == tag_id).all()
        device_ids = [d[0] for d in device_ids]
        if device_ids:
            filters.append(JobResult.device_id.in_(device_ids))
        else:
            # No devices for this tag, return empty
            return PaginatedJobResultResponse(items=[], total=0, page=page, size=size, pages=0)
    if filters:
        query = query.filter(and_(*filters))
    total = query.count()
    pages = (total + size - 1) // size
    offset = (page - 1) * size
    results = query.order_by(JobResult.result_time.desc()).offset(offset).limit(size).all()
    logger.log(
        f"JobResults listed (total={total}) with filters: device_id={device_id}, job_id={job_id}, tag_id={tag_id}, job_type={job_type}, status={status}",
        level="INFO", destinations=["stdout", "file", "db"]
    )
    return PaginatedJobResultResponse(
        items=results,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/{job_result_id}", response_model=JobResultRead)
def get_job_result(job_result_id: int, db: Session = Depends(get_db_session)):
    job_result = db.query(JobResult).filter(JobResult.id == job_result_id).first()
    if not job_result:
        logger.log(
            f"JobResult not found: id={job_result_id}",
            level="WARNING", destinations=["stdout", "file", "db"]
        )
        raise HTTPException(status_code=404, detail="JobResult not found")
    logger.log(
        f"JobResult retrieved: id={job_result_id}",
        level="INFO", destinations=["stdout", "file", "db"]
    )
    return job_result 