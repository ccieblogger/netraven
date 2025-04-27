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

## Phase 5: Documentation & Final Review (Complete)

**Date:** April 7, 2024

**Changes:**
*   Reviewed main `README.md`.
*   Updated `README.md` to correctly state Vue 3 is used for the frontend (instead of React).
*   Confirmed development log is up-to-date with progress through Phase 4.

**Rationale:**
*   Ensured primary project documentation reflects the current state after scaffolding.
*   Completed all planned scaffolding and alignment tasks for this feature branch.

**Branch Status:** `core/api-scheduler-frontend-services` now contains the scaffolded structures for the API, Scheduler, and Frontend services, along with aligned configuration loading and setup scripts.

**Next Steps:**
*   Implement the actual functionality within the scaffolded services as detailed in the plan below.

---

## Implementation Plan: Core Service Functionality

This plan outlines the steps to build out the core features within the scaffolded API, Scheduler, and Frontend services. It assumes the current state of the `core/api-scheduler-frontend-services` branch.

**Goal:** Achieve basic end-to-end functionality for creating devices, scheduling backup jobs, executing jobs via the worker, storing results, and viewing information via the API and a basic UI.

**Prerequisites:**
*   PostgreSQL database is running and accessible (`setup/setup_postgres.sh install`).
*   Redis server is running and accessible (`setup/setup_redis.sh`).
*   Python environment with dependencies installed (`poetry install`).
*   Node.js/npm environment for frontend (`cd frontend && npm install`).

### Part 1: API Implementation (Database Interaction & Basic Logic)

**Objective:** Implement CRUD operations for Devices and Jobs, handle user authentication properly, and enable job triggering.

**Files:** `netraven/api/routers/`, `netraven/api/schemas/`, `netraven/api/dependencies.py`, `netraven/api/auth.py`

1.  **Refine Schemas (`netraven/api/schemas/`)**
    *   **What:** Define Pydantic schemas for request bodies (Create/Update) and responses for `Device`, `Job`, `User`, `Log`, `Credential`, `Tag` based on the database models (`netraven/db/models/`). Use `BaseSchema` and consider `orm_mode=True` if needed.
    *   **Why:** To enforce data validation and structure for API interactions.
    *   **Example (`schemas/device.py`):**
        ```python
        from pydantic import BaseModel, Field, IPvAnyAddress
        from typing import Optional, List
        from datetime import datetime
        # from .base import BaseSchema (If you have common fields/config)

        class TagBase(BaseModel):
            name: str
            type: str

        class Tag(TagBase):
            id: int
            class Config:
                orm_mode = True # Or from_attributes = True in Pydantic v2

        class DeviceBase(BaseModel):
            hostname: str = Field(..., example="core-switch-01")
            ip_address: IPvAnyAddress = Field(..., example="192.168.1.1")
            device_type: str = Field(..., example="cisco_ios") # Match netmiko types
            # Add other fields like port, notes etc. if needed

        class DeviceCreate(DeviceBase):
            tags: Optional[List[str]] = None # Allow associating tags by name on create
            # Add credential info if creating directly

        class DeviceUpdate(BaseModel):
            hostname: Optional[str] = None
            ip_address: Optional[IPvAnyAddress] = None
            device_type: Optional[str] = None
            tags: Optional[List[str]] = None

        class Device(DeviceBase):
            id: int
            last_seen: Optional[datetime] = None
            tags: List[Tag] = []
            # Add related configs if needed
            class Config:
                orm_mode = True # Or from_attributes = True
        ```

2.  **Implement Database Dependency (`dependencies.py`)**
    *   **What:** Create a dependency function `get_db_session` that yields a SQLAlchemy session from `netraven.db.session.get_db`.
    *   **Why:** To inject database sessions into router functions easily.
    *   **Example:**
        ```python
        from sqlalchemy.orm import Session
        from netraven.db.session import get_db

        def get_db_session():
            db = next(get_db())
            try:
                yield db
            finally:
                db.close()
        ```

3.  **Implement Device CRUD (`routers/devices.py`)**
    *   **What:** Implement `list_devices`, `create_device`, `get_device`, `update_device`, `delete_device` endpoints. Use the `get_db_session` dependency. Fetch/create/update/delete `Device` model instances using the SQLAlchemy session. Use the defined Pydantic schemas for request validation (`DeviceCreate`, `DeviceUpdate`) and response formatting (`response_model=List[Device]`, `response_model=Device`). Handle potential errors (e.g., device not found -> 404).
    *   **Why:** To provide the core API functionality for managing devices.
    *   **Example (`create_device`):**
        ```python
        from sqlalchemy.orm import Session
        from fastapi import Depends, HTTPException
        from .. import schemas, models # Assuming schemas & models are structured
        from ..dependencies import get_db_session, get_current_active_user # Add auth

        # ... (router definition) ...

        @router.post("/", response_model=schemas.Device, status_code=201,
                    dependencies=[Depends(get_current_active_user)]) # Protect endpoint
        def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db_session)):
            db_device = db.query(models.Device).filter(models.Device.hostname == device.hostname).first()
            if db_device:
                raise HTTPException(status_code=400, detail="Hostname already registered")
            # Add logic to handle tags if provided in schema
            new_device = models.Device(**device.dict(exclude={"tags"})) # Adapt based on schema/model
            # Add tag handling logic here if needed
            db.add(new_device)
            db.commit()
            db.refresh(new_device)
            return new_device
        ```

4.  **Implement Job CRUD (`routers/jobs.py`)**
    *   **What:** Similar to devices, implement CRUD endpoints for `Job` resources. Use schemas `JobCreate`, `JobUpdate`, `Job`. Pay attention to scheduling fields (interval, cron string, run_at time) defined in the schemas/models.
    *   **Why:** To manage backup job definitions.

5.  **Implement User/Auth Endpoints (`routers/auth_router.py`, `routers/users.py`)**
    *   **What:**
        *   `auth_router.py`: Implement the `/auth/token` endpoint properly. It should accept username/password, query the `User` model, verify the password using `auth.verify_password`, and if valid, create a JWT using `auth.create_access_token`.
        *   `users.py`: Implement basic User CRUD (especially create user, maybe get current user `/users/me`). Ensure passwords are hashed using `auth.get_password_hash` before saving.
        *   `dependencies.py`: Update `get_current_user` to actually fetch the user object from the DB based on the username in the token payload.
    *   **Why:** To enable user login, registration, and secure API access.
    *   **Example (`/auth/token`):**
        ```python
        # In auth_router.py
        # ... imports ...
        from ..models import User

        @router.post("/token", response_model=schemas.Token)
        async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db_session)):
            user = db.query(User).filter(User.username == form_data.username).first()
            if not user or not auth.verify_password(form_data.password, user.hashed_password):
                 raise HTTPException(
                     status_code=status.HTTP_401_UNAUTHORIZED,
                     detail="Incorrect username or password",
                     headers={"WWW-Authenticate": "Bearer"},
                 )
            access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = auth.create_access_token(
                data={"sub": user.username, "role": user.role}, # Include role if available
                expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
        ```

6.  **Implement Job Trigger Endpoint (`routers/jobs.py`)**
    *   **What:** Implement the `/jobs/run/{job_id}` endpoint. Import `Queue` from `rq` and `Redis` from `redis`. Connect to Redis (using config from `load_config`). Enqueue the `netraven.scheduler.job_definitions.run_device_job` function with the `job_id` argument.
    *   **Why:** To allow manual triggering of jobs via the API.
    *   **Example:**
        ```python
        from rq import Queue
        from redis import Redis
        from ..config.loader import load_config
        from ..scheduler.job_definitions import run_device_job # Import target function

        config = load_config()
        redis_url = config.get('scheduler',{}).get('redis_url', 'redis://localhost:6379/0')
        redis_conn = Redis.from_url(redis_url)
        q = Queue(connection=redis_conn)

        @router.post("/run/{job_id}", status_code=202, dependencies=[Depends(get_current_active_user)])
        async def run_job_now(job_id: int, db: Session = Depends(get_db_session)):
            # Optional: Check if job exists in DB
            job = db.query(models.Job).filter(models.Job.id == job_id).first()
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            # Enqueue the job
            q.enqueue(run_device_job, job_id)
            return {"status": "queued", "job_id": job_id}
        ```

7.  **Implement Log Viewing Endpoint (`routers/logs.py`)**
    *   **What:** Implement the `/logs` endpoint to query `JobLog` and potentially `ConnectionLog` models based on `job_id` or `device_id` filters. Add pagination.
    *   **Why:** To allow viewing logs via the API.

8.  **Testing:** Add basic integration tests using `TestClient` for each endpoint, mocking database interactions where necessary initially, then testing against a test DB. Test authentication and authorization. Test job enqueueing (mock Redis or use a test instance).

### Part 2: Scheduler Implementation (Job Scheduling Logic)

**Objective:** Make the scheduler correctly read job definitions from the database and schedule them in RQ Scheduler.

**Files:** `netraven/scheduler/job_registration.py`, `netraven/db/models/job.py` (potentially requires fields)

1.  **Define Job Scheduling Fields:**
    *   **What:** Ensure the `Job` model (`netraven/db/models/job.py`) has fields to define the schedule (e.g., `is_enabled: bool`, `schedule_type: str` ['interval', 'cron', 'onetime'], `interval_seconds: int`, `cron_string: str`, `run_at: datetime`). Create Alembic migration if needed.
    *   **Why:** To store how and when jobs should run.

2.  **Implement `sync_jobs_from_db` (`job_registration.py`)**
    *   **What:** Replace the placeholder logic. Query the DB for enabled jobs. Iterate through jobs and based on `schedule_type`:
        *   Use `scheduler.schedule()` for recurring interval jobs (set `repeat=None` for infinite).
        *   Use `scheduler.cron()` for cron-based jobs.
        *   Use `scheduler.enqueue_at()` for one-time future jobs.
        *   Implement logic to prevent duplicate scheduling (e.g., use `job_id` in `scheduler.schedule`, check `scheduler.get_jobs()`, or use `meta` field).
    *   **Why:** To connect the database job definitions to the actual scheduling mechanism.
    *   **Example (Interval part):**
        ```python
        # In sync_jobs_from_db function
        jobs_to_schedule = db.query(Job).filter(Job.is_enabled == True).all()
        scheduled_job_ids = {job.id for job in scheduler.get_jobs()} # Get RQ job IDs

        for job in jobs_to_schedule:
            rq_job_id = f"netraven_db_job_{job.id}"
            if rq_job_id in scheduled_job_ids:
                # Potentially check if parameters (like interval) have changed
                continue # Skip if already scheduled

            if job.schedule_type == 'interval' and job.interval_seconds:
                 scheduler.schedule(
                     scheduled_time=datetime.now(timezone.utc), # Start ASAP
                     func=run_device_job,
                     args=[job.id],
                     interval=job.interval_seconds,
                     repeat=None,
                     job_id=rq_job_id,
                     meta={'db_job_id': job.id, 'schedule_type': 'interval'} # Add metadata
                 )
                 log.info("Scheduled interval job", job_id=job.id, interval=job.interval_seconds)
            # Add elif for cron, onetime
            # ... handle other types or log warning ...
        ```

3.  **Testing:** Test `sync_jobs_from_db` by mocking the DB session and the `scheduler` object. Verify that `scheduler.schedule`, `cron`, `enqueue_at` are called with the correct arguments based on mock Job data. Test duplicate prevention.

### Part 3: Frontend Implementation (Basic Views & Interactions)

**Objective:** Implement basic UI views for listing devices and jobs, triggering jobs, and viewing status/logs.

**Files:** `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/store/`, `frontend/src/router/index.js`

1.  **Implement Login Page (`pages/Login.vue`)**
    *   **What:** Connect the form submit logic (`handleLogin`) to the `authStore.login` action (which needs to be implemented in `store/auth.js` to call the `/auth/token` API endpoint using Axios). Handle success (redirect to Dashboard) and errors (show messages).
    *   **Why:** To enable user login.

2.  **Implement Auth Store Login Action (`store/auth.js`)**
    *   **What:** Create a `login` action that takes username/password, calls the API (`api.post('/auth/token', formData)`), on success calls `setAuth` with token/user info, and returns success/failure.
    *   **Why:** To centralize login logic.

3.  **Refine Router Guard (`router/index.js`)**
    *   **What:** Uncomment and use the `useAuthStore` import. Replace placeholder `isAuthenticated` and `userRole` checks with actual checks against the auth store state (`authStore.isAuthenticated`, `authStore.userRole`).
    *   **Why:** To enforce authentication and role-based access correctly.

4.  **Implement Device List Page (`pages/Devices.vue`)**
    *   **What:** On component mount (`onMounted`), call an action in a new `deviceStore` (needs creation) to fetch devices from the API (`api.get('/devices')`). Display the fetched devices in a simple table (can use a basic `v-for` initially, or create `BaseTable.vue` component later).
    *   **Why:** To display the device inventory.

5.  **Implement Job List Page (`pages/Jobs.vue`)**
    *   **What:** Similar to Devices, use `onMounted` to call an action in the `jobStore` (e.g., `fetchJobs`) to get jobs from `api.get('/jobs')`. Display in a table. Add buttons for each job to trigger (`run_job_now`) and view details/logs.
    *   **Why:** To display job definitions and allow interaction.

6.  **Implement Job Trigger (`pages/Jobs.vue` + `store/job.js`)**
    *   **What:** Add a method in `Jobs.vue` that calls a `runJobNow` action in `jobStore`. The action calls the API (`api.post(`/jobs/run/${jobId}`)`). Use the notification store (`useNotificationStore`) to show success/error messages.
    *   **Why:** To allow manual job execution from the UI.

7.  **Implement Basic Log Viewing (`pages/Logs.vue`)**
    *   **What:** Add basic filtering inputs (Job ID, Device ID). On filter change, call an action in a new `logStore` to fetch logs (`api.get('/logs', { params: filters })`). Display logs.
    *   **Why:** To provide basic log viewing capabilities.

8.  **Component Structure (`App.vue`, `layouts/`)**
    *   **What:** Update `App.vue` to include a basic layout structure (e.g., sidebar, header, main content area using `<router-view>`). Create a default layout component in `src/layouts/`. Include navigation links based on router definitions. Add a global notification display area that reads from `notificationStore`.
    *   **Why:** To provide consistent application structure and navigation.

9.  **Testing:** Basic component tests (Vue Test Utils) to ensure rendering. Mock stores and API calls. E2E tests (Playwright/Cypress) for login flow, navigating, viewing devices/jobs, triggering a job (mocking the backend job execution).
