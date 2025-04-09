# Development Log: feature/core-services-logic

**Date:** $(date +'%Y-%m-%d %H:%M:%S')

**Developer:** Gemini

**Branch:** feature/core-services-logic

**Goal:** Implement core API, Scheduler, and Frontend functionality based on existing SOT documents and the implementation plan outlined in the previous developer's log (`docs/developer/development_log/core-api-scheduler-frontend-services/development_log.md`), after resolving the Job-Device relationship discrepancy.

**Initial Plan:**
1.  Resolve Job-Device Relationship Discrepancy:
    *   Modify DB Schema (Job model, potentially add JobDevice association table).
    *   Update Alembic migration(s).
    *   Refactor Worker Service (`runner.py`, `dispatcher.py`, `executor.py`, tests) to handle multiple devices per job.
2.  Implement API Core Functionality (Part 1 of previous dev's plan).
3.  Implement Scheduler Core Functionality (Part 2 of previous dev's plan).
4.  Implement Frontend Core Functionality (Part 3 of previous dev's plan).
5.  Conduct thorough testing and refinement.

---

## Phase 1: Resolve Job-Device Relationship Discrepancy (Complete)

**Date:** $(date +'%Y-%m-%d %H:%M:%S')

**Goal:** Modify the system to allow a single Job to target multiple Devices via Tags, aligning the DB and worker with the overall architecture.

**Changes:**

*   **Database Models (`netraven/db/models/`)**:
    *   `tag.py`: Added `job_tags_association` table definition. Added `jobs` many-to-many relationship to `Tag` model, linked via `job_tags_association`.
    *   `job.py`: Removed `device_id` column and `device` relationship. Added `tags` many-to-many relationship, linked via `job_tags_association`. Added `name`, `description`, `is_enabled`, `schedule_type`, `interval_seconds`, `cron_string` fields based on previous developer's plan and SOT requirements for scheduler integration.
    *   `job_log.py`: Verified `device_id` ForeignKey is nullable.
*   **Alembic Migration (`alembic/versions/a3992da91329...`)**:
    *   Modified the *initial* migration script instead of creating a new one.
    *   Removed `device_id` column/FK from `jobs` table definition.
    *   Added `job_tags` association table definition.
    *   Added new columns (`name`, `description`, `is_enabled`, etc.) and indexes to `jobs` table definition.
    *   Verified `job_logs.device_id` definition reflects nullable FK.
*   **Database Schema Reset:**
    *   Troubleshot and resolved Poetry environment/dependency issues (`structlog` missing, manual `venv` conflict, outdated Poetry version).
    *   Deleted obsolete Alembic revision file (`efed1e960ea3...`).
    *   Used `dev_runner.py` to drop tables.
    *   Cleared stale DB history using `psql` (`DELETE FROM alembic_version`).
    *   Applied the modified initial migration (`a3992da91329`) using `poetry run alembic upgrade head`.
*   **Worker Service (`netraven/worker/`)**:
    *   `runner.py`: Renamed `load_device_for_job` to `load_devices_for_job`. Updated logic to load devices via `Job.tags -> Tag.devices` using `selectinload` for efficiency. Updated `run_job` to handle the list of devices, call dispatcher, and determine aggregate final status (`COMPLETED_SUCCESS`, `COMPLETED_PARTIAL_FAILURE`, `COMPLETED_FAILURE`, `COMPLETED_NO_DEVICES`). Updated job-level error logging (`log_runner_error`) to pass `device_id=None`.
    *   `log_utils.py`: No changes needed as `JobLog.device_id` was already nullable.
*   **Worker Tests (`tests/worker/test_runner_integration.py`)**:
    *   Added new fixtures (`create_test_tag`, `create_test_device`, `create_test_job_with_tags`) to manage Job-Tag-Device relationships in tests.
    *   Refactored tests for success, partial failure, and total failure scenarios involving multiple devices.
    *   Added test for the `COMPLETED_NO_DEVICES` status.
    *   Updated assertions to check aggregate job status and per-device logs.
    *   Removed obsolete single-device tests.

**Rationale:**
*   Aligns the worker and DB with the intended architecture where jobs target groups of devices (represented by Tags).
*   Consolidates DB schema changes into the initial migration script for a cleaner history, suitable for deployment.
*   Resolves environment/dependency issues encountered during the process.
*   Ensures integration tests accurately reflect the multi-device processing logic.

**Next Steps:** Proceed to Phase 2: Implement API Core Functionality.

---

## Phase 2: Implement API Core Functionality (Complete)

**Date:** $(date +'%Y-%m-%d %H:%M:%S')

**Goal:** Implement core CRUD operations and logic for the API service based on the adopted plan.

**Changes:**

*   **Dependencies:** Added FastAPI, Uvicorn, python-jose, passlib, python-multipart, redis, rq via `poetry add`.
*   **Schemas (`netraven/api/schemas/`)**: Created/updated Pydantic schemas for Base, Tag, Token, User, Credential, Device, Job, Log (JobLog, ConnectionLog). Updated BaseSchema for Pydantic v2 compatibility.
*   **Dependencies (`netraven/api/dependencies.py`)**: Implemented `get_db_session` dependency. Updated `get_current_user` and `get_current_active_user` to use DB session, return User model, and check `is_active`. Added `require_admin_role` dependency.
*   **Device Router (`netraven/api/routers/devices.py`)**: Implemented full CRUD endpoints. Added helper `get_tags_by_ids` (copied locally for now) to handle tag associations based on ID lists in create/update payloads. Included checks for duplicate hostname/IP.
*   **Tag Router (`netraven/api/routers/tags.py`)**: Created new router. Implemented full CRUD endpoints for managing tags.
*   **Credential Router (`netraven/api/routers/credentials.py`)**: Created new router. Implemented full CRUD endpoints. Uses `auth.get_password_hash` for storing passwords. Handles tag associations.
*   **Job Router (`netraven/api/routers/jobs.py`)**: Implemented full CRUD endpoints. Handles tag associations using helper. Implemented `/run/{job_id}` endpoint to enqueue job via RQ, including Redis connection setup and error handling.
*   **User Router (`netraven/api/routers/users.py`)**: Implemented full CRUD endpoints (mostly admin-protected). Added `/users/me` endpoint for users to retrieve their own info. Uses `auth.get_password_hash`.
*   **Auth Router (`netraven/api/routers/auth_router.py`)**: Implemented `/token` endpoint using `authenticate_user` helper (defined locally) and DB session. Includes check for active user. Includes user role in JWT payload.
*   **Log Router (`netraven/api/routers/logs.py`)**: Implemented `/logs` endpoint to retrieve combined JobLog and ConnectionLog entries. Supports filtering by `job_id`, `device_id`, `log_type`, and includes pagination.
*   **Main App (`netraven/api/main.py`)**: Imported and included all new routers (tags, credentials). Ensured auth router is included early.

**Rationale:**
*   Provides the core REST API endpoints required for managing all primary resources (Devices, Tags, Credentials, Jobs, Users).
*   Implements secure authentication (JWT) and basic authorization (active user check, admin role requirement on sensitive routes).
*   Enables manual job triggering via the API through RQ.
*   Allows querying of log data.
*   Builds upon the previously scaffolded structure.

**Next Steps:** Proceed to Phase 3: Implement Scheduler Core Functionality.

---

## Phase 3: Implement Scheduler Core Functionality (Complete)

**Date:** $(date +'%Y-%m-%d %H:%M:%S')

**Goal:** Implement the core logic for the RQ Scheduler service to read job definitions from the database and schedule them for execution by the worker.

**Changes:**

*   **Dependencies:** Added `rq-scheduler` via `poetry add`.
*   **Job Registration (`netraven/scheduler/job_registration.py`)**: 
    *   Implemented `sync_jobs_from_db` function.
    *   Added DB query to fetch enabled `Job` models.
    *   Implemented logic to generate predictable RQ job IDs (`generate_rq_job_id`).
    *   Added check against `scheduler.get_jobs()` to prevent duplicate scheduling based on the generated RQ job ID.
    *   Implemented scheduling logic using `scheduler.schedule()` for `interval` type jobs.
    *   Implemented scheduling logic using `scheduler.cron()` for `cron` type jobs.
    *   Implemented scheduling logic using `scheduler.enqueue_at()` for `onetime` type jobs, ensuring the scheduled time is in the future.
    *   Targeted `netraven.worker.runner.run_job` as the function to be executed by the worker.
*   **Scheduler Runner (`netraven/scheduler/scheduler_runner.py`)**:
    *   Added basic `structlog` configuration for improved console logging.
    *   Verified that the runner correctly loads config, connects to Redis, initializes the scheduler, and calls `sync_jobs_from_db` in its main loop.
*   **Testing (`tests/scheduler/test_job_registration.py`)**:
    *   Created new test file.
    *   Added unit tests for `sync_jobs_from_db` using mocked DB session and mocked RQ Scheduler instance.
    *   Tests cover scheduling of interval, cron, and one-time jobs.
    *   Tests cover skipping of disabled jobs, jobs with invalid schedule types, past one-time jobs, and jobs already present in the scheduler.

**Rationale:**
*   Connects the job definitions stored in the database (via the API) to the actual scheduling mechanism (RQ Scheduler).
*   Enables automatic execution of defined jobs based on intervals, cron expressions, or specific future times.
*   Prevents redundant job scheduling.
*   Provides basic unit test coverage for the core scheduling logic.

**Next Steps:** Proceed to Phase 4: Implement Frontend Core Functionality.

---

## Phase 4: Implement Frontend Core Functionality (Complete)

**Date:** $(date +'%Y-%m-%d %H:%M:%S')

**Goal:** Implement the basic structure and core pages for the Vue.js frontend application, including state management using Pinia stores and basic page components for Devices, Jobs, Logs, and Authentication.

**Changes:**

*   **Dependencies:** Added `pinia`, `vue-router`, `axios`, `@headlessui/vue`, `@heroicons/vue`, `tailwindcss`, `autoprefixer`, `postcss`.
*   **Project Setup:** Initialized Vue project structure using Vite. Configured Tailwind CSS.
*   **API Service (`frontend/src/services/api.js`)**: Created an Axios instance configured with the base API URL. Added interceptors to include the auth token from `localStorage` in requests and handle 401 responses by redirecting to login.
*   **Pinia Stores (`frontend/src/store/`)**:
    *   `device.js`: Implemented `useDeviceStore` with state (`devices`, `isLoading`, `error`), computed properties, and actions (`fetchDevices`, `createDevice`, `updateDevice`, `deleteDevice`) interacting with the API service. Includes placeholder logic for CRUD operations.
    *   `job.js`: Implemented `useJobStore` with state (`jobs`, `isLoading`, `error`, `runStatus`), computed properties, and actions (`fetchJobs`, `createJob`, `updateJob`, `deleteJob`, `runJobNow`) interacting with the API service. Includes placeholder logic for CRUD and manual run actions.
    *   `auth.js`: Implemented `useAuthStore` with state (`token`, `user`, `loginError`, `isLoading`), computed properties (`isAuthenticated`, `userRole`, `username`), and actions (`setAuthData`, `clearAuthData`, `fetchUserProfile`, `login`, `logout`). Handles token storage in `localStorage`, updates Axios headers, and manages login/logout flow with redirects.
    *   `log.js`: Implemented `useLogStore` with state (`logs`, `isLoading`, `error`, `filters`, `pagination`), computed properties, and actions (`fetchLogs`). The `fetchLogs` action supports dynamic filtering and pagination parameters when calling the API.
*   **Router (`frontend/src/router/index.js`)**: Configured Vue Router with routes for Home, Devices, Jobs, Logs, and Login. Implemented an `async` navigation guard (`router.beforeEach`) that:
    *   Checks `meta.requiresAuth` and `meta.requiresAdmin`.
    *   Uses the `useAuthStore`'s computed `isAuthenticated` property.
    *   Fetches the user profile (`auth.fetchUserProfile()`) if a token exists but user data is not loaded (handling page refresh scenarios).
    *   Redirects unauthenticated users to the Login page for protected routes.
    *   Redirects non-admin users trying to access admin-only routes.
*   **Layout (`frontend/src/layouts/DefaultLayout.vue`)**: Created the main application layout using Tailwind CSS. Includes a sidebar for navigation and a main content area. Displays username and a Logout button (calling `authStore.logout`) when authenticated, or a Login link otherwise.
*   **Pages (`frontend/src/pages/`)**:
    *   `Devices.vue`: Implemented the device management page. Displays a table of devices fetched from `useDeviceStore`. Includes buttons for Add, Edit, Delete (currently placeholders with `alert`). Shows loading and error states.
    *   `Jobs.vue`: Implemented the job management page. Displays a table of jobs fetched from `useJobStore`. Includes buttons for Add, Edit, Delete, and Run Now (currently placeholders with `alert`). Shows loading and error states.
    *   `Logs.vue`: Implemented the log viewing page. Displays a table of logs fetched from `useLogStore`. Includes filter inputs (Job ID, Device ID, Log Type) with Apply/Reset buttons triggering `logStore.fetchLogs`. Formats timestamps and styles log levels/types. Includes loading/error states.
    *   `Login.vue`: Implemented the login page. Provides a form bound to `username` and `password` refs. Calls `authStore.login` on submission. Displays login errors from the store and handles loading state for the button.
    *   `Home.vue`: Basic placeholder home page.
*   **Main App (`frontend/src/main.js`)**: Configured the Vue app to use Pinia and the Router. Mounts the application.
*   **Tailwind Config (`frontend/tailwind.config.js`, `frontend/postcss.config.js`, `frontend/src/index.css`)**: Configured Tailwind CSS, including necessary plugins and base styles.

**Rationale:**
*   Establishes the foundational structure of the frontend application.
*   Provides dedicated Pinia stores for managing the state of different resources (Devices, Jobs, Auth, Logs), promoting modularity and maintainability.
*   Implements core page components for viewing and interacting with the main resources.
*   Sets up secure routing with authentication checks and profile fetching on refresh.
*   Integrates the API service for data fetching and state updates.
*   Uses Tailwind CSS for consistent styling.

**Next Steps:** Proceed to Phase 5: Implement Frontend CRUD Modals and Pagination.

---

## Phase 5: Implement Frontend CRUD Modals and Pagination (Planned)

**Date:** $(date +'%Y-%m-%d %H:%M:%S')

**Goal:** Enhance the frontend by implementing interactive modal forms for creating and editing Devices, Jobs, and potentially other resources. Add pagination controls to the Logs page (and potentially Devices/Jobs pages if needed).

**Plan:**

1.  **Component Library/Strategy for Modals:**
    *   **Decision:** Utilize a library like Headless UI (already partially used) or build simple custom modal components. Headless UI is recommended for accessibility and pre-built transitions.
    *   **Action:** Create a reusable `BaseModal.vue` component using Headless UI's `Dialog` components. This modal should handle open/close state, transitions, titles, and slots for content and actions (e.g., Save/Cancel buttons).

2.  **Device CRUD Modals (`frontend/src/components/modals/`)**:
    *   **Create `DeviceFormModal.vue`:**
        *   **Props:** `isOpen` (Boolean), `deviceToEdit` (Object, optional - null for create mode).
        *   **Events:** `close`, `save` (emitting the device data).
        *   **State:** Use `ref` or `reactive` for form fields (hostname, ip_address, type, port, tags, credential_id). Handle tags potentially using a multi-select component or simple comma-separated input initially. Credential ID might need a dropdown populated from a `credentialStore` (needs creation or fetching logic).
        *   **Logic:**
            *   Initialize form fields based on `deviceToEdit` prop if in edit mode, otherwise empty/default.
            *   Implement validation (e.g., required fields, IP format).
            *   On save, validate, emit the `save` event with the form data, and close.
        *   **Integration:** Update `Devices.vue`. Add state to manage modal visibility (`isCreateModalOpen`, `isEditModalOpen`, `editingDevice`). Update `openCreateModal`, `openEditModal`, `closeModal`, and `handleSave` functions to control the modal and call the appropriate `deviceStore` actions (`createDevice`, `updateDevice`). Pass the correct props and handle events.
    *   **Create `DeleteConfirmationModal.vue` (Reusable):**
        *   **Props:** `isOpen`, `itemType` (String, e.g., "device"), `itemName` (String).
        *   **Events:** `close`, `confirm`.
        *   **Logic:** Display a confirmation message using props. Emit `confirm` event when the confirm button is clicked.
        *   **Integration:** Update `Devices.vue`. Add state (`isDeleteModalOpen`, `deletingDeviceId`). Update `confirmDelete` and `handleDeleteConfirm` to control the modal and call `deviceStore.deleteDevice`.

3.  **Job CRUD Modals (`frontend/src/components/modals/`)**:
    *   **Create `JobFormModal.vue`:**
        *   **Props:** `isOpen`, `jobToEdit`.
        *   **Events:** `close`, `save`.
        *   **State:** Form fields (`name`, `description`, `tags`, `is_enabled`, `schedule_type`, `interval_seconds`, `cron_string`). Use conditional rendering (`v-if`) to show interval/cron fields based on `schedule_type`.
        *   **Logic:** Similar to `DeviceFormModal` - initialize based on props, validate, emit `save`.
        *   **Integration:** Update `Jobs.vue` similarly to `Devices.vue` - manage modal state, implement handlers, call `jobStore` actions.
    *   **Integration:** Update `Jobs.vue` to use the reusable `DeleteConfirmationModal.vue` for delete confirmations.

4.  **Log Pagination (`frontend/src/pages/Logs.vue` and `frontend/src/store/log.js`)**:
    *   **Store Update (`log.js`):**
        *   Modify `fetchLogs` to accept `page` and `size` parameters.
        *   Update the API call to include these as query parameters (`/api/v1/logs?page=...&size=...`).
        *   Add `pagination` state (e.g., `{ currentPage: 1, totalItems: 0, itemsPerPage: 20, totalPages: 0 }`).
        *   Update the store state with pagination info returned from the API (API needs to return this - **Backend Change Required**).
    *   **Component Update (`Logs.vue`):**
        *   Add a `PaginationControls.vue` component (or integrate directly).
        *   **Props:** `currentPage`, `totalPages`, `itemsPerPage`.
        *   **Events:** `changePage`.
        *   **Display:** Show "Page X of Y", "Previous", "Next" buttons. Disable buttons appropriately (e.g., Previous on page 1).
        *   **Logic:** Emit `changePage` event with the new page number.
        *   **Integration:** Add pagination controls below the logs table. Bind props to `logStore.pagination`. Handle the `changePage` event by calling `logStore.fetchLogs` with the new page number and existing filters.

5.  **Tag/Credential Selection in Modals:**
    *   **Requirement:** Device and Job forms need to select existing Tags. Device form needs to select an existing Credential.
    *   **Action (Store):** Create `useTagStore` and `useCredentialStore` (if not already planned). Add `fetchTags` and `fetchCredentials` actions.
    *   **Action (Component):** In `DeviceFormModal` and `JobFormModal`, fetch tags/credentials (e.g., `onMounted` or when the modal opens). Populate dropdowns or multi-select components with the fetched data. Ensure the `save` event emits the selected IDs.

6.  **Refinement and Testing:**
    *   Test all CRUD operations thoroughly via the UI.
    *   Test form validation.
    *   Test pagination on the Logs page.
    *   Ensure loading and error states are handled gracefully in modals.

**Backend Considerations:**
*   The `/api/v1/logs` endpoint needs to be updated to accept `page` and `size` query parameters and return pagination metadata (total items, total pages, current page) alongside the log data.
*   The `/api/v1/devices`, `/api/v1/jobs`, `/api/v1/tags`, `/api/v1/credentials` list endpoints might also benefit from pagination if lists become long.

---

## Debugging: Worker Integration Tests (`tests/worker/test_runner_integration.py`)

**Date:** 2025-04-09

**Goal:** Resolve multiple failures in the worker integration tests that emerged after refactoring the Job-Device relationship and initial API/Scheduler implementations.

**Debugging Process & Fixes:**

1.  **Initial Failures:** Tests failed primarily due to `DetachedInstanceError` (SQLAlchemy session issues) and mock signature/return value mismatches (`ValueError`, `ProgrammingError`).
2.  **`get_db` Mocking:** Initially removed `db=db_session` from `runner.run_job` calls and patched `get_db`. This led to session errors. **Fix:** Reverted the removal of `db=db_session` in test calls to `runner.run_job`. The runner now manages the session context correctly internally, but the tests still need to provide the initial session for setup and assertions. Removed the `get_db` patching as it became unnecessary.
3.  **`commit_git` Mock Return:** Identified `ValueError` due to incorrect return tuple size from the mocked `commit_configuration_to_git`. **Fix:** Updated mock `side_effect`/`return_value` to provide a 2-tuple `(Optional[str], Optional[dict])` as per `git_writer.py`.
4.  **`run_command` Mock Return:** Identified errors related to the return type of the mocked `netmiko_driver.run_command`. **Fix:** Updated mock `side_effect` lambdas/lists to return a 3-tuple `(bool, Optional[str], Optional[dict])` matching the actual function signature and `RunResult` type.
5.  **Log Dictionary `type` Key:** Assertion errors occurred because mock log dictionaries were missing the `"type"` key. **Fix:** Added `"type": "connection"` or `"type": "job"` to the relevant mock log dictionaries returned by `run_command` and `commit_git` side effects.
6.  **SQLAlchemy `ANY` Placeholder Error:** Encountered `ProgrammingError` when using `unittest.mock.ANY` for timestamps in log dictionaries being inserted into the DB. **Fix:** Replaced `timestamp: ANY` with `timestamp: datetime.utcnow()` in mock log dictionaries.
7.  **`run_command` Mock Call Assertion:** Test failed asserting `run_command` was called with `call(device)` instead of the actual `call(device, job_id)`. **Fix:** Updated `assert_has_calls` for `run_command` to include `test_job.id`.
8.  **`ConnectionLog` Count Assertions:** Partial and total failure tests incorrectly asserted the number of connection logs (expecting 1 or 0 instead of 2, as logs are created for both success and failure attempts). **Fix:** Updated assertions in `test_run_job_partial_failure_multiple_devices` and `test_run_job_total_failure_multiple_devices` to expect `len(conn_logs) == 2`.
9.  **`commit_git` Mock `repo_path` Assertion:** Mock assertions failed because the `repo_path` argument expected (`None`, loaded dynamically in the test) differed from the actual path used (`/data/git-repo/`, loaded within the `git_writer`). **Fix:** Hardcoded the expected `repo_path` in assertions to `/data/git-repo/`.
10. **`commit_git` Mock Argument Swapping (Concurrency):** In the multi-device success test, the assertion failed because arguments (like `config_data` and `device_hostname`) were swapped between the two calls to `commit_git` due to non-deterministic thread execution order. **Fix:** Refactored `run_command` and `commit_git` mock `side_effect`s to use device-specific lambdas (helper functions) to return the correct data based on the device hostname or ID, regardless of call order. Used a set-based comparison for `commit_git` call arguments to handle the order-independent nature.
11. **`JobLog` Assertion Order (Concurrency):** The final failure occurred because assertions assumed `job_logs[0]` would always correspond to `device1`. Due to concurrency, `device2`'s log might be created first. **Fix:** Made `JobLog` assertions order-independent by checking for the presence of both `device1.id` and `device2.id` in the set of `device_id`s, and checking for the presence of both expected commit messages in the list of log messages.

**Outcome:** All 4 tests in `tests/worker/test_runner_integration.py` now pass successfully.

--- 