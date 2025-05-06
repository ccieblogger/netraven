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

## Job Results and Logs: Dual Write and Canonical Sources

During job execution, the system writes per-device job outcomes to both:
- **Job Results Table (`job_results`)**: Structured, canonical per-device job outcome (status, details, timestamps). Used for reporting, analytics, and dashboards. Exposed via `/job-results/`.
- **Unified Logs Table (`logs`)**: Unstructured, canonical event log (job, connection, system, etc.). Used for log/event tables, filtering, and streaming. Exposed via `/logs/`.

### Endpoint Relationships
- `/job-results/`: Canonical for per-device job outcomes.
- `/jobs/{job_id}/devices`: **DEPRECATED**. Use `/job-results/?job_id=...` for canonical per-device job status. This endpoint is maintained for legacy UI compatibility only and will be removed after migration.
- `/logs/`: Canonical for all log events.
- `/job-logs/`: **REMOVED**. This endpoint is not implemented in the backend and should not be referenced in frontend or documentation. Use `/logs/` for all log/event queries.

### Migration Guidance
- **Frontend**: Use `/job-results/` for per-device job status. Use `/logs/` for log/event tables. Do not use `/job-logs/` (endpoint is not implemented and all references should be removed).
- **Backend**: Maintain both tables for now; `/jobs/{job_id}/devices` is deprecated and will be removed after migration to `/job-results/` is complete.

# Migration Notes

- `/jobs/{job_id}/devices` is deprecated. All consumers should migrate to `/job-results/?job_id=...` for per-device job status.
- `/job-logs/` is not implemented and should be removed from all documentation and frontend code. Use `/logs/` for all log/event queries.
- **Canonical Data Sources:**
    - `/job-results/` is the only source for per-device job status.
    - `/logs/` is the canonical source for event/audit logs.

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