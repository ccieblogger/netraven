## NetRaven Scheduler Service: State of Technology (SOT)

### Executive Summary

This document defines the implementation plan and responsibilities for the NetRaven scheduler service. The scheduler is responsible for managing job timing and execution by enqueueing device tasks to be handled by the `device_comm` worker. It uses RQ (Redis Queue) and RQ Scheduler to support recurring and one-time tasks. This service operates in a synchronous, non-containerized environment and integrates with the central PostgreSQL database.

### Core Responsibilities

- Poll the PostgreSQL database for enabled job entries.
- Use RQ Scheduler to enqueue jobs at specified intervals or one-time schedules.
- Schedule jobs with parameters like device list, job type, and execution time.
- Trigger `device_comm.run_job(job_id)` to perform the actual device communication.
- Monitor job execution flow and record logs for traceability.
- Retry failed jobs up to `max_retries` using exponential backoff.
- Use structured logging for all stages of job lifecycle.
- Log job scheduling attempts and errors.

> ℹ️ Redis is a required component for job persistence and queue management, used internally by both RQ and rq-scheduler.
- Monitor the Redis queue for due jobs and enqueue them.
- Trigger the `device_comm` service by passing job IDs for execution.
- Log job scheduling attempts and errors.

### Technology Stack

```yaml
language: Python 3.11+
queue_system: RQ (Redis Queue)
scheduler_library: rq-scheduler
database_layer: SQLAlchemy (sync)
logging: structlog + JSON
```

### Directory Structure
```
/netraven/
├── scheduler/
│   ├── __init__.py
│   ├── scheduler_runner.py      # Main entry point
│   ├── job_definitions.py       # RQ job logic
│   ├── job_registration.py      # Maps DB jobs to scheduler
│   └── utils.py                 # Retry logic, error handling
```

### Configuration File (`config/environments/dev.yaml`)

A local Redis server (v7+) is required for RQ and rq-scheduler to operate correctly.

```yaml
scheduler:
  redis_url: redis://localhost:6379/0
  polling_interval_seconds: 10
  max_retries: 3
  retry_backoff_seconds: 5
```

### Scheduler Runner Example (`scheduler_runner.py`)
```python
from redis import Redis
from rq_scheduler import Scheduler
from time import sleep
from datetime import datetime
from netraven.scheduler.job_registration import sync_jobs_from_db
import structlog

log = structlog.get_logger()

redis_conn = Redis.from_url("redis://localhost:6379/0")  # Required for RQ to function
scheduler = Scheduler(connection=redis_conn)

if __name__ == "__main__":
    while True:
        try:
            log.info("Polling for new jobs...")
            sync_jobs_from_db(scheduler)
        except Exception as e:
            log.error("Error polling jobs", error=str(e))
        sleep(10)
```python
from rq_scheduler import Scheduler
from redis import Redis
from datetime import datetime
from netraven.scheduler.job_definitions import run_device_job

redis_conn = Redis.from_url("redis://localhost:6379/0")
scheduler = Scheduler(connection=redis_conn)

# Enqueue a job to run once
scheduler.enqueue_at(datetime(2024, 1, 1, 12, 0), run_device_job, job_id)

# Or recurring jobs
scheduler.schedule(
    scheduled_time=datetime.utcnow(),
    func=run_device_job,
    args=[job_id],
    interval=86400,  # daily
    repeat=None
)
```

### Job Definition (`job_definitions.py`)
```python
from netraven.worker.runner import run_job
import structlog

log = structlog.get_logger()

def run_device_job(job_id: int):
    try:
        log.info("Running scheduled job", job_id=job_id)
        run_job(job_id)
        log.info("Job completed", job_id=job_id)
    except Exception as e:
        log.error("Job failed", job_id=job_id, error=str(e))
        raise
```python
from netraven.worker.runner import run_job

def run_device_job(job_id):
    run_job(job_id)
```

### Job Registration Logic (`job_registration.py`)
```python
from netraven.db.session import get_db
from netraven.db.models import Job
from datetime import datetime, timedelta
from redis import Redis
from rq_scheduler import Scheduler
from netraven.scheduler.job_definitions import run_device_job

scheduler = Scheduler(connection=Redis.from_url("redis://localhost:6379/0"))

def sync_jobs_from_db(scheduler):
    db = next(get_db())
    jobs = db.query(Job).filter(Job.enabled == True).all()

    for job in jobs:
        # This is placeholder logic - should match real fields
        next_run = datetime.utcnow() + timedelta(seconds=job.interval or 3600)
        scheduler.schedule(
            scheduled_time=next_run,
            func=run_device_job,
            args=[job.id],
            interval=job.interval or 3600,
            repeat=None
        )
```

### Wireframe: Scheduler CLI/Log Output (Low-Fidelity)
```
+---------------------------------------------------------------+
|                 Scheduler Runtime Console Output              |
+---------------------------------------------------------------+
| [2025-04-06 10:01] Loaded 2 scheduled jobs                    |
| [2025-04-06 10:01] Job 123 (Backup-Core) scheduled at 02:00   |
| [2025-04-06 10:01] Job 124 (Audit-Edge) scheduled for once     |
|---------------------------------------------------------------|
| [2025-04-06 10:10] Job 123 enqueued to RQ                     |
| [2025-04-06 10:11] Job 124 failed to schedule: missing time   |
+---------------------------------------------------------------+
```

### Developer Commands
```bash
# Run the scheduler loop
python netraven/scheduler/scheduler_runner.py

# Register all scheduled jobs from DB
python netraven/scheduler/job_registration.py
```

### Testing Plan
- Unit tests for:
  - Job registration logic
  - Error handling & retries
  - Time interval calculations
- Integration test:
  - Enqueue job and verify it executes via `device_comm`
- Mock Redis and `run_job()` for isolated testing

### Appendix: Local Redis Setup (`setup/setup_redis.sh`)
To run the scheduler locally, Redis must be installed and running. Use the following script:

```bash
#!/bin/bash

sudo apt update
sudo apt install -y redis-server

sudo systemctl enable redis-server
sudo systemctl start redis-server

echo "✅ Redis installed and running."
```

This script installs Redis 7+ and ensures it's running on the default port `6379`. This is required for RQ and rq-scheduler to enqueue and schedule jobs.

If Redis is unavailable, the scheduler cannot function.

> 🔐 Redis is used by RQ and rq-scheduler for storing job queues and schedules. This setup assumes a single local Redis instance for development.

---
