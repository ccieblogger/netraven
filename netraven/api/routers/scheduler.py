from fastapi import APIRouter, Depends, HTTPException
from netraven.api.dependencies import get_current_active_user
from netraven.api.schemas.job import ScheduledJobSummary, RQQueueStatus, QueueJobDetail
from typing import List
from redis import Redis
from rq_scheduler import Scheduler
from rq import Queue
from netraven.config.loader import load_config
from datetime import datetime

router = APIRouter(
    prefix="/scheduler",
    tags=["Scheduler"],
    dependencies=[Depends(get_current_active_user)]
)

def get_redis_conn():
    config = load_config()
    redis_url = config.get('scheduler', {}).get('redis_url', 'redis://localhost:6379/0')
    return Redis.from_url(redis_url)

@router.get("/jobs", response_model=List[ScheduledJobSummary])
def list_scheduled_jobs():
    """List all jobs currently scheduled in RQ Scheduler."""
    try:
        redis_conn = get_redis_conn()
        scheduler = Scheduler(connection=redis_conn)
        jobs = scheduler.get_jobs()
        result = []
        for job in jobs:
            meta = job.meta or {}
            result.append(ScheduledJobSummary(
                id=meta.get('db_job_id', 0),
                name=job.description or "",
                job_type=meta.get('schedule_type', ''),
                description=job.description,
                schedule_type=meta.get('schedule_type', None),
                interval_seconds=meta.get('interval_seconds', None),
                cron_string=meta.get('cron_string', None),
                scheduled_for=getattr(job, 'enqueued_at', None),
                next_run=getattr(job, 'next_run', None),
                repeat=getattr(job, 'repeat', None),
                args=getattr(job, 'args', None),
                meta=meta,
                tags=[],
                is_enabled=True,
                is_system_job=False
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch scheduled jobs: {e}")

@router.get("/queue/status", response_model=List[RQQueueStatus])
def queue_status():
    """Show queue length and details of jobs currently in the queue."""
    try:
        redis_conn = get_redis_conn()
        queue_names = ['default', 'high', 'low']
        result = []
        for qname in queue_names:
            q = Queue(qname, connection=redis_conn)
            jobs = q.jobs
            job_count = len(jobs)
            oldest_job_ts = jobs[0].enqueued_at if jobs else None
            job_details = []
            for job in jobs:
                job_details.append(QueueJobDetail(
                    job_id=job.id,
                    enqueued_at=getattr(job, 'enqueued_at', None),
                    func_name=getattr(job, 'func_name', None),
                    args=getattr(job, 'args', None),
                    meta=getattr(job, 'meta', None)
                ))
            result.append(RQQueueStatus(
                name=qname,
                job_count=job_count,
                oldest_job_ts=oldest_job_ts,
                jobs=job_details
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch queue status: {e}") 