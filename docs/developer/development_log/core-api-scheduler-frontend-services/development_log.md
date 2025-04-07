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

## Phase 3: Frontend UI Scaffolding (Complete)

**Date:** April 7, 2024

**Changes:**
*   Resolved issues with frontend directory structure (removed nested `frontend/frontend`).
*   Created correct `frontend/src` subdirectories: `components`, `layouts`, `pages`, `router`, `store`, `services`, `utils`.
*   Manually initialized Tailwind CSS (`tailwind.config.js`, `postcss.config.js`) due to npx issues.
*   Added Tailwind directives to `frontend/src/assets/main.css` and ensured it's imported in `frontend/src/main.js`.
*   Created `frontend/src/router/index.js` and configured Vue Router with placeholder routes (Dashboard, Devices, Jobs, Logs, Users, Login, Unauthorized) and a basic navigation guard structure based on `frontend_sot.md`.
*   Integrated Pinia and Vue Router into the main Vue app instance (`frontend/src/main.js`).
*   Created Pinia store modules (`auth.js`, `job.js`, `notifications.js`) in `frontend/src/store/` with state and placeholder actions based on `frontend_sot.md`.
*   Created `frontend/src/services/api.js` and configured an Axios instance with a base URL and interceptors for adding JWT tokens and basic error handling (e.g., 401).
*   Created placeholder Vue components for the main pages (`Dashboard.vue`, `Devices.vue`, `Jobs.vue`, `Logs.vue`, `Users.vue`, `Login.vue`, `Unauthorized.vue`) in `frontend/src/pages/`.

**Rationale:**
*   Established the foundational file structure, tooling (Vite, Tailwind), routing (Vue Router), state management (Pinia), and API communication layer (Axios) for the frontend application based on `frontend_sot.md`.
*   Placeholder components and routes allow the application structure to be visualized and tested during development.
*   The navigation guard and Axios interceptors provide the basic framework for authentication and authorization.

**Issues Encountered:**
*   Significant issues running `npm create vue`, `npm install`, and `npx` commands via the tool, likely due to WSL/UNC path conflicts or permissions. Required manual execution by the user for these steps.
*   Shell context persistence within the tool was inconsistent, leading to incorrect relative paths. Required using absolute paths or workspace-relative paths and manual correction of directory structures.

**Next Steps:**
*   Proceed to Phase 4: Review and Align Minor Gaps (Config loading, Setup scripts, Tests).

## Phase 4: Review and Align Minor Gaps (Complete)

**Date:** April 7, 2024

**Changes:**
*   Implemented central configuration loader (`netraven/config/loader.py`) supporting `default.yaml`, `{env}.yaml`, and `NETRAVEN_` prefixed environment variables.
*   Added `PyYAML` dependency (already present).
*   Created `netraven/config/environments/dev.yaml` with initial config keys for database, scheduler, worker, logging, api, and git.
*   Updated `netraven/db/session.py` to use `load_config()`.
*   Updated `netraven/scheduler/scheduler_runner.py` to use `load_config()`.
*   Removed the redundant root-level `/config` directory (manually by user).
*   Verified `setup/dev_runner.py` and `setup/setup_postgres.sh` against SOTs.
*   Created `setup/setup_redis.sh` based on SOT and made it executable.
*   Verified `tests/test_db_connection.py` against SOT.
*   Reviewed `tests/worker/` directory (contains tests for git_writer, redactor, runner).
*   Rewritten `tests/config/test_loader.py` to accurately test the new `netraven.config.loader`.

**Rationale:**
*   Standardized configuration loading across services, adhering to the defined hierarchy (YAML + Env Vars).
*   Ensured necessary setup scripts are present and aligned with documentation.
*   Confirmed baseline test coverage for existing DB and Worker components.
*   Updated configuration tests to match the implemented loader.
*   Cleaned up project structure by removing the redundant root config directory.

**Next Steps:**
*   Proceed to Phase 5: Documentation & Final Review.
