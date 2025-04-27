from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from netraven.api.schemas.log import LogEntry, PaginatedLogResponse, LogTypeMeta, LogLevelMeta, LogStats
from netraven.api.dependencies import get_db_session, get_current_active_user
from netraven.db.models import Log, LogType, LogLevel
from datetime import datetime
import math
import asyncio
import json
from fastapi import Response
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as redis
from netraven.config.loader import load_config

router = APIRouter(
    prefix="/logs",
    tags=["Logs"],
    dependencies=[Depends(get_current_active_user)]
)

@router.get("/types", response_model=List[LogTypeMeta])
def get_log_types():
    # Static for now; could be dynamic if log types are extended
    return [
        LogTypeMeta(log_type=lt.value, description=lt.name.title()) for lt in LogType
    ]

@router.get("/levels", response_model=List[LogLevelMeta])
def get_log_levels():
    # Static for now; could be dynamic if log levels are extended
    return [
        LogLevelMeta(level=ll.value, description=ll.name.title()) for ll in LogLevel
    ]

@router.get("/stats", response_model=LogStats)
def get_log_stats(db: Session = Depends(get_db_session)):
    total = db.query(func.count(Log.id)).scalar() or 0
    by_type = {row[0]: row[1] for row in db.query(Log.log_type, func.count(Log.id)).group_by(Log.log_type).all()}
    by_level = {row[0]: row[1] for row in db.query(Log.level, func.count(Log.id)).group_by(Log.level).all()}
    last_log_time = db.query(func.max(Log.timestamp)).scalar()
    return LogStats(total=total, by_type=by_type, by_level=by_level, last_log_time=last_log_time)

@router.get("/", response_model=PaginatedLogResponse)
def list_logs(
    log_type: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    job_id: Optional[int] = Query(None),
    device_id: Optional[int] = Query(None),
    source: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None, description="Filter logs by the job_type of the related Job (e.g., backup, reachability, etc.)"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db_session)
):
    """
    List logs with flexible filters, including job_type (from related Job).
    """
    query = db.query(Log)
    if job_type:
        from netraven.db.models.job import Job
        query = query.join(Job, Log.job_id == Job.id).filter(Job.job_type == job_type)
    if log_type:
        query = query.filter(Log.log_type == log_type)
    if level:
        query = query.filter(Log.level == level)
    if job_id:
        query = query.filter(Log.job_id == job_id)
    if device_id:
        query = query.filter(Log.device_id == device_id)
    if source:
        query = query.filter(Log.source == source)
    if start_time:
        query = query.filter(Log.timestamp >= start_time)
    if end_time:
        query = query.filter(Log.timestamp <= end_time)
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(Log.message.ilike(search_term), func.cast(Log.meta, str).ilike(search_term)))
    total = query.count()
    order_by = desc(Log.timestamp) if order == "desc" else asc(Log.timestamp)
    logs = query.order_by(order_by).offset((page - 1) * size).limit(size).all()
    pages = math.ceil(total / size) if total > 0 else 1
    return {
        "items": logs,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/stream")
async def stream_logs(
    job_id: Optional[int] = Query(None, description="Filter streamed logs by job_id"),
    device_id: Optional[int] = Query(None, description="Filter streamed logs by device_id")
):
    """
    Stream real-time log events as Server-Sent Events (SSE).
    Optionally filter by job_id and/or device_id.
    Sends a keep-alive comment every 15 seconds to prevent idle timeouts.
    """
    config = load_config()
    redis_cfg = config.get('logging', {}).get('redis', {})
    redis_host = redis_cfg.get('host', 'redis')
    redis_port = redis_cfg.get('port', 6379)
    redis_db = redis_cfg.get('db', 0)
    redis_channel = redis_cfg.get('channel_prefix', 'netraven-logs')

    async def event_generator():
        redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
        redis_conn = await redis.from_url(redis_url)
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe(redis_channel)
        try:
            while True:
                try:
                    message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True, timeout=15), timeout=15)
                    if message and message['type'] == 'message':
                        try:
                            log_event = json.loads(message['data'])
                        except Exception:
                            continue
                        if job_id is not None and log_event.get('job_id') != job_id:
                            continue
                        if device_id is not None and log_event.get('device_id') != device_id:
                            continue
                        yield {
                            "event": "log",
                            "data": json.dumps(log_event)
                        }
                    else:
                        yield {"data": ": keepalive"}
                except asyncio.TimeoutError:
                    yield {"data": ": keepalive"}
        finally:
            await pubsub.unsubscribe(redis_channel)
            await pubsub.close()
            await redis_conn.close()

    return EventSourceResponse(event_generator())

@router.get("/{log_id}", response_model=LogEntry)
def get_log(log_id: int, db: Session = Depends(get_db_session)):
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return log 