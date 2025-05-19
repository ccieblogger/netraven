## NetRaven Architecture

### Executive Summary

This document outlines the complete architecture for NetRaven, a network device configuration backup system designed for deployment in customer environments. NetRaven retrieves and stores device configurations for auditing, historical tracking, and operational assurance. The system prioritizes simplicity, testability, and maintainability, while still supporting targeted concurrency for tasks like device polling.

### System Overview

#### System Diagram (ASCII)
```
                        ┌────────────────────┐
                        │     Frontend UI     │
                        │    (Vue 3 + REST)   │
                        └────────▲───────────┘
                                 │ REST API
                                 ▼
                        ┌────────────────────┐
                        │    API Service      │
                        │     (FastAPI)       │
                        └────────▲───────────┘
                                 │
             ┌──────────────────┼────────────────────┐
             │                  │                    │
      Device │          Job CRUD│           User/Auth│
     Records │                  ▼                    ▼
         ┌───┴────┐     ┌──────────────┐      ┌──────────────┐
         │Devices │     │   Jobs Table │      │   Users/Roles│
         └───┬────┘     └──────┬───────┘      └────┬─────────┘
             │                │                    │
             ▼                ▼                    ▼
      ┌────────────┐  ┌──────────────┐      ┌──────────────┐
      │ PostgreSQL │  │  Redis Queue │      │ JWT Security │
      └────┬───────┘  └──────┬───────┘      └──────────────┘
           │                 │
           ▼                 ▼
   ┌─────────────────────────────────┐
   │        Job Scheduler            │
   │    (RQ + RQ Scheduler)          │
   └────────────┬───────────────────┘
                ▼
       ┌──────────────────────────────┐
       │ Dedicated Worker Container   │
       │ (RQ Worker, Python, Docker) │
       └────────┬────────────────────┘
                ▼
       ┌───────────────────┐
       │  Device Comm Job  │
       │   (Netmiko-based) │
       └────────┬──────────┘
                ▼
        ┌─────────────┐
        │ Network Gear│
        └─────────────┘
                │
                ▼
        ┌───────────────────────────┐
        │ Git Repo (Config Storage) │
        └───────────────────────────┘
```

NetRaven supports:

1. Retrieval of running configuration and identifying information from network devices (primarily via SSH).
2. Storing configuration snapshots in a Git repository for version control.
3. Job scheduling for one-time or recurring configuration backups.
4. REST API access for external integrations.
5. Role-based web UI for inventory management and job monitoring.

---

### **Containerized Deployment Model (Critical)**

**NetRaven is designed and supported exclusively as a Docker Compose environment.**  
All services must be run as containers. Local, bare-metal, or non-containerized operation is not supported.

#### **Required Containers (as defined in `docker-compose.yml`):**
- **nginx**: Reverse proxy for API and frontend (dev/prod)
- **frontend**: Vue 3 + Vite + Pinia UI
- **api**: FastAPI backend (REST API)
- **worker**: RQ Worker for device communication jobs
- **postgres**: PostgreSQL 14 database
- **redis**: Redis 7 for job queue and log streaming
- **scheduler**: (if separate) RQ Scheduler for job orchestration

All developer and production workflows must use the provided Docker Compose setup.  
**Do not attempt to run any service outside of Docker.**

**All frontend–backend API communication must go through the NGINX container using the `/api` prefix. Direct calls to the backend service are not supported or permitted.**

For integration and troubleshooting details, see [`frontend_backend_integration.md`](./frontend_backend_integration.md).

---

### Directory Layout (as of this release)

```
/ (project root)
├── netraven/      # All backend Python code (api, worker, scheduler, db, config, services, utils)
├── frontend/      # Vue 3 + Vite + Pinia frontend app
├── setup/         # Bootstrap and developer scripts
├── tests/         # Unit, integration, and E2E tests
├── docker/        # Dockerfiles and container configs (api, nginx, postgres, etc.)
├── alembic/       # Alembic migration environment (single initial migration only)
├── docker-compose.yml
├── docker-compose.prod.yml
├── pyproject.toml
├── poetry.lock
└── ...
```

---

### Core Architectural Principles

- **Container-First**: All services run as containers, orchestrated by Docker Compose.
- **Local Redis Required**: Redis is a core local dependency for job queuing, scheduling, and log streaming.
- **Synchronous-First Design**: Synchronous services simplify development and debugging.
- **Targeted Concurrency**: Uses threads only where concurrency offers clear benefits (e.g., connecting to multiple devices).
- **Modular Design**: Isolated services for API, job scheduling, communication, and logging.
- **Detailed Logging**: Unified log model with per-device and per-job logs, supporting both redacted and raw entries.
- **Secure by Default**: JWT authentication and role-based access controls.

---

### Core Services

#### 1. API Service (FastAPI - Sync Mode)
- Exposes REST API endpoints for all system functions.
- JWT-based authentication with role enforcement (admin/user).
- CRUD for devices, device groups (tags), jobs, users, and roles.
- Status endpoints for job monitoring.
- Log endpoints for querying and streaming logs (see Logging section).

#### 2. Device Communication Worker (Dedicated Container)
- Executes device jobs triggered by scheduler or on demand.
- Runs as a dedicated container using RQ Worker.
- **Healthcheck:** Uses a process-based healthcheck script that verifies the RQ worker process is running and Redis is reachable. The container is marked healthy only when both are true. (Previous HTTP healthcheck was removed for the worker container.)
- Connects to network devices using **Netmiko** (and Paramiko for extensibility).
- Retrieves `show running-config` and basic facts (hostname, serial number).
- Uses `ThreadPoolExecutor` for concurrent device access (default: 5).
- Reports logs and results to database.
- Picks up jobs from the Redis queue and updates job status in the database.
- Git-based configuration storage is implemented in `netraven/worker/git_writer.py`.

#### 2a. System Jobs (e.g., Reachability)
- System jobs are created automatically during system installation (e.g., reachability job).
- System jobs are associated with a default tag and credentials.
- System jobs are not user-deletable or editable.
- The worker processes system jobs just like regular jobs, but with special handling for job type and status.
- If no devices are associated with the job's tags, the job is marked as `COMPLETED_NO_DEVICES`.

#### 3. Job Scheduler
- Based on **RQ + RQ Scheduler**.
- **Implemented in**: `netraven/scheduler/scheduler_runner.py` (main scheduler process) and `netraven/scheduler/job_registration.py` (job sync and registration logic).
- Queues and schedules jobs (one-time, recurring, with start/end window support).
- Triggers device communication jobs in the background.

#### 4. PostgreSQL Database
- Stores all persistent data:
  - Devices, jobs, logs
  - Credentials (encrypted)
  - User accounts and roles
  - System configuration
- Managed with **SQLAlchemy (sync)**.
- **Alembic is used only for the initial schema setup** (single migration file, no legacy migrations).

#### 5. Frontend UI
- Directory: `/frontend/` (Vue 3 + Vite + Pinia + TailwindCSS)
- Integrates via REST API
- **All frontend API calls must use the `/api` prefix and be routed through the NGINX reverse proxy.**
- For details and best practices on wiring up frontend to backend, see [`frontend_backend_integration.md`](./frontend_backend_integration.md).
- For UI component and workflow details, see [`/docs/source_of_truth/frontend_sot.md`](../source_of_truth/frontend_sot.md)

#### 6. Configuration Loader
- Module: `netraven/config/loader.py`
- Loads configuration in order:
  1. Environment variables
  2. Database values
  3. YAML files in `/netraven/config/`
- Exposes uniform API for all components

#### 7. Service & Utilities
- `netraven/services/`: domain-level services (credential resolution, job dispatch, health checks)
- `netraven/utils/`: shared utilities (logging helpers, redaction, retry logic, validation)

---

### Logging & Log Endpoints

NetRaven uses a **unified log model** for all log events (job, connection, session, system, etc.), with a `log_type` field to distinguish log categories. All logs are stored in a single `logs` table and exposed via a unified set of API endpoints:

- `GET /logs/` — List logs with flexible filters (job_id, device_id, log_type, level, source, time range, pagination)
- `GET /logs/{log_id}` — Retrieve a single log entry by ID
- `GET /logs/types` — List available log types
- `GET /logs/levels` — List available log levels
- `GET /logs/stats` — Get log statistics (total, by type, by level, last log time)
- `GET /logs/stream` — Stream real-time log events via Server-Sent Events (SSE) using Redis pub/sub

---

### Device Communication

- Primary protocol: **SSH via Netmiko** (with Paramiko as a backend option)
- Vendor extensibility via Netmiko platform mapping
- Device grouping (tags) determines credential selection
- Detailed logs include:
  - Start/end time
  - Auth failures
  - Unreachable device errors
  - Output with sensitive line redaction

---

### Authentication & Authorization

- JWT-based access for both API and UI users
- Admin and user roles
- Users can be assigned visibility to specific device groups

---

### Configuration Management

- Hierarchical loading:
  1. Environment variables
  2. Admin-set values from DB
  3. YAML files in `/netraven/config/`
- All components read configuration via a common loader

---

### Git Integration

NetRaven uses a local Git repository as the versioned storage backend for device configuration files. This approach offers simplicity, traceability, and built-in change tracking with minimal infrastructure overhead.

- Each configuration snapshot is saved as a text file and committed to a local Git repository.
- Commit messages include structured metadata such as job ID, device hostname, and timestamp.
- Git provides built-in versioning, rollback, and readable diffs to show changes between snapshots.
- The Git repository is stored in a dedicated project folder (e.g., `/data/git-repo/`) and initialized on first use.
- GitPython is used to interface with the repository programmatically.
- Git logic is implemented in `netraven/worker/git_writer.py`.

---

### Testing Strategy

- **Unit Tests**: Business logic, validation, utilities
- **Integration Tests**: DB transactions, API/worker behavior
- **E2E Tests**: Simulate full workflows from API → device → Git → UI
- Test database with Alembic-migrated schemas
- Threaded jobs tested for isolation, timing, logging

---

#### Job Lifecycle & Orchestration (Updated)
- Jobs are created via the API or automatically (system jobs).
- Jobs are enqueued in Redis and picked up by the dedicated worker container.
- The worker updates job status (`QUEUED` → `RUNNING` → `COMPLETED`/`FAILED`/`COMPLETED_NO_DEVICES`).
- Job logs and connection logs are written to the database for UI consumption, differentiated by `log_type`.
- System jobs are protected from deletion and have special status handling in the UI and backend.

---

### Scheduler & Queue API Endpoints (2025-04)

NetRaven now exposes dedicated API endpoints for real-time visibility into scheduled jobs and the RQ job queue, supporting the UI's job dashboard and operational monitoring features.

- **GET /scheduler/jobs**: Lists all jobs currently scheduled in RQ Scheduler, including job ID, description, schedule type, interval/cron, next run, and metadata. Example response:

```json
[
  {
    "id": 1,
    "name": "Backup Core Routers Daily",
    "job_type": "interval",
    "description": "Nightly backup job",
    "schedule_type": "interval",
    "interval_seconds": 86400,
    "cron_string": null,
    "scheduled_for": null,
    "next_run": "2025-04-28T02:00:00Z",
    "repeat": null,
    "args": [1],
    "meta": {"db_job_id": 1, "schedule_type": "interval"},
    "tags": [],
    "is_enabled": true,
    "is_system_job": false
  }
]
```

- **GET /scheduler/queue/status**: Returns the status of each RQ queue (default, high, low), including job count, oldest job timestamp, and per-job details (job_id, enqueued_at, func_name, args, meta). Example response:

```json
[
  {
    "name": "default",
    "job_count": 2,
    "oldest_job_ts": "2025-04-27T22:00:00Z",
    "jobs": [
      {
        "job_id": "rq-job-1",
        "enqueued_at": "2025-04-27T22:00:00Z",
        "func_name": "run_job",
        "args": [1],
        "meta": {"db_job_id": 1}
      }
    ]
  }
]
```

- **Authentication**: Both endpoints require JWT authentication and enforce role-based access. Unauthenticated requests receive 401/403.

- **Intended Usage**: These endpoints power the UI's scheduled jobs and queue status dashboard, enabling real-time and on-demand monitoring for NetOps and admin users.

---
