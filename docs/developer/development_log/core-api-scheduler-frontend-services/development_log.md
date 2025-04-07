# Development Log: core/api-scheduler-frontend-services

## Phase 1: API Service Scaffolding (Complete)

**Date:** April 7, 2024

**Changes:**
*   Created branch `core/api-scheduler-frontend-services` from `release`.
*   Created development log file: `docs/developer/development_log/core-api-scheduler-frontend-services/development_log.md`.
*   Created API directory structure: `netraven/api/`, `routers/`, `schemas/`.
*   Created initial files: `__init__.py`, `main.py`, `dependencies.py`, `auth.py`, `schemas/base.py`.
*   Added basic FastAPI app instance in `main.py` with health check.
*   Added initial JWT auth placeholders (`dependencies.py`, `auth.py`) including OAuth2 scheme, password hashing, token creation utilities. (Note: `SECRET_KEY` needs moving to config).
*   Added base Pydantic schema (`schemas/base.py`) and placeholder schema files (`device.py`, `job.py`, `user.py`, `log.py`, `token.py`).
*   Created placeholder router files (`devices.py`, `jobs.py`, `auth_router.py`, `users.py`, `logs.py`) with basic endpoint structures.
*   Included placeholder routers in `main.py`.

**Rationale:**
*   Established the foundational file and code structure for the API service based on `api_service_sot.md`.
*   Implemented basic FastAPI app, health check, and JWT/auth scaffolding to enable future development of protected endpoints.
*   Created placeholder routers and schemas to outline the intended API resources.

**Next Steps:**
*   Proceed to Phase 2: Scheduler Service Scaffolding.

## Phase 2: Scheduler Service Scaffolding (Complete)

**Date:** April 7, 2024

**Changes:**
*   Created scheduler directory structure: `netraven/scheduler/`.
*   Created initial files: `__init__.py`, `scheduler_runner.py`, `job_definitions.py`, `job_registration.py`, `utils.py`.
*   Added basic scheduler runner structure (`scheduler_runner.py`) with imports (structlog, Redis, rq-scheduler), config loading placeholder, Redis connection logic, and main polling loop.
*   Added placeholder job definition function (`job_definitions.py`: `run_device_job`) that imports and calls the worker's `run_job` function.
*   Added placeholder job registration logic (`job_registration.py`: `sync_jobs_from_db`) with structure for DB query, checking existing scheduled jobs, and calling `scheduler.schedule` (includes examples for interval, one-time, cron).

**Rationale:**
*   Established the foundational file and code structure for the scheduler service based on `scheduler_sot.md`.
*   Implemented the basic runner loop, connection to Redis, and placeholder logic for dynamically loading and scheduling jobs based on DB entries.
*   Linked the scheduled task (`run_device_job`) to the existing worker service entry point (`netraven.worker.runner.run_job`).

**Next Steps:**
*   Proceed to Phase 3: Frontend UI Scaffolding.
