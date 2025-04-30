# NetRaven Job Lifecycle Design Specification (Updated)

## Executive Summary

This document details the lifecycle of a job in the NetRaven system, from creation through scheduling, execution, and logging. It describes the flow of data and control between system components, the technologies involved, and the code locations responsible for each phase. This specification is intended for developers, maintainers, and integrators seeking to understand or extend NetRaven's job orchestration pipeline.

---

## System Components Involved

- **API Service (`netraven.api`)**: FastAPI-based REST API for job creation, status, and log retrieval.
- **Database (`netraven.db`)**: PostgreSQL with SQLAlchemy models for jobs, devices, logs, and related metadata.
- **Scheduler (`netraven.scheduler`)**: Implemented in `scheduler_runner.py` and `job_registration.py`, using RQ Scheduler for enqueuing jobs into Redis at scheduled times.
- **Redis Queue**: Message broker for job queuing and worker communication.
- **Worker (`netraven.worker`)**: Dedicated RQ Worker container for executing jobs, device communication, and logging. Main logic in `runner.py`.
- **Git Integration**: Device configuration snapshots are committed to a local Git repository via `worker/git_writer.py`.
- **Frontend/UI**: Vue 3 application for user interaction (not covered in code detail here).

---

## Job Lifecycle: Step-by-Step

### 1. Job Creation
- **Initiator**: User via UI or API client
- **Process**:
  - User sends a POST request to `/jobs/` endpoint.
  - API validates input and creates a new job record in the database (`jobs` table).
  - Job metadata includes devices/tags, schedule, credentials, etc.
- **Key Files**:
  - `netraven/api/routers/jobs.py`
  - `netraven/db/models/job.py`

### 2. Job Scheduling
- **Initiator**: Scheduler service
- **Process**:
  - `scheduler_runner.py` runs as a process, polling the DB and syncing jobs.
  - `job_registration.py` fetches enabled jobs from the DB and schedules them in RQ Scheduler (interval, cron, or one-time).
  - Jobs are scheduled to call the worker's `run_job` function by job ID.
- **Key Files**:
  - `netraven/scheduler/scheduler_runner.py`
  - `netraven/scheduler/job_registration.py`
  - `netraven/scheduler/job_definitions.py`

### 3. Job Execution
- **Initiator**: Worker service (RQ Worker)
- **Process**:
  - Worker listens to Redis queue for jobs.
  - On dequeuing a job:
    1. Updates job status to `RUNNING` in the database.
    2. Loads devices (by tag or device_id) and resolves credentials.
    3. Dispatches device operations in parallel via `dispatcher.py`.
    4. Device communication is handled by backend drivers (e.g., Netmiko).
    5. Configuration snapshots are committed to Git via `git_writer.py`.
    6. Logs actions and results to the `logs` table in PostgreSQL.
    7. Updates job status to `COMPLETED`, `FAILED`, or `COMPLETED_NO_DEVICES`.
- **Key Files**:
  - `netraven/worker/runner.py`
  - `netraven/worker/dispatcher.py`
  - `netraven/worker/backends/netmiko_driver.py` (and other backends)
  - `netraven/worker/git_writer.py`
  - `netraven/db/models/log.py`

### 4. Job Monitoring & Logging
- **Initiator**: API/UI
- **Process**:
  - API exposes endpoints for job status and logs.
  - UI polls these endpoints for real-time job progress and logs.
- **Key Files**:
  - `netraven/api/routers/logs.py`
  - `netraven/api/routers/jobs.py`

---

## Job Lifecycle Flow Diagram (ASCII)

```
User/UI/API
    │
    ▼
[ FastAPI API Service ]
    │  (POST /jobs/)
    ▼
[ PostgreSQL: jobs table ]
    │
    ▼
[ Scheduler Service (scheduler_runner.py, job_registration.py) ]
    │  (Enqueue job in Redis)
    ▼
[ Redis Queue ]
    │
    ▼
[ Worker Service (RQ Worker) ]
    │
    ├─► [ Load Devices & Credentials ]
    │         │
    │         ├─► [ Dispatch Device Tasks (dispatcher.py) ]
    │         │         │
    │         │         ├─► [ Device Communication (netmiko_driver.py, etc.) ]
    │         │         │
    │         │         └─► [ Store Config in Git (git_writer.py) ]
    │         │
    │         └─► [ Log Results to PostgreSQL ]
    │
    └─► [ Update Job Status in DB ]
    │
    ▼
[ API/UI: Job Status & Logs ]
```

---

## Responsibilities and Code Locations

| Step                | Component/Service         | Technology         | Code Location(s)                                         |
|---------------------|--------------------------|--------------------|----------------------------------------------------------|
| Job Creation        | API Service              | FastAPI, SQLAlchemy| `api/routers/jobs.py`                                    |
| Job Scheduling      | Scheduler                | RQ, RQ Scheduler   | `scheduler/scheduler_runner.py`, `scheduler/job_registration.py` |
| Job Enqueue         | Scheduler                | Redis Queue        | `scheduler/job_registration.py`                          |
| Job Execution       | Worker                   | RQ Worker, Netmiko | `worker/runner.py`, `worker/dispatcher.py`, `worker/backends/netmiko_driver.py` |
| Config Storage      | Worker                   | GitPython          | `worker/git_writer.py`                                   |
| Logging             | Worker/API               | PostgreSQL         | `db/models/log.py`                                       |
| Status/Logs Display | API/UI                   | FastAPI, Vue       | `api/routers/logs.py`                                    |

---

## Notes & Clarifications
- There is **no `netraven/git/` directory**; Git commit logic is in `worker/git_writer.py`.
- Job scheduling is handled by `scheduler_runner.py` and `job_registration.py`, not `scheduler.py`.
- Device operations are dispatched in parallel using a thread pool in `dispatcher.py`.
- Device communication supports multiple backends (Netmiko, Paramiko, etc.).

---

## References
- [NetRaven System Architecture Statement of Truth](architecture_sot.md)
- [Logging System Spec](logging_system_spec.md)
- [REST API Log Query](rest_api_log_query.md)

---

*This document is maintained as part of the NetRaven architecture documentation. For updates or corrections, please submit a pull request or contact the project maintainers.* 