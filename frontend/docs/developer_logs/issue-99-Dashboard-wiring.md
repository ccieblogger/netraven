# Developer Log: issue/99-Dashboard-wiring

## Issue 99: [Enhancement] Dashboard.vue Backend Integration & Data Wiring

**Summary:**
Wire up the `Dashboard.vue` page to the backend so that all KPI cards, the RQ (Redis Queue) card, filters, search boxes, device table, status icons, and action buttons display and interact with real data from the FastAPI backend.

**Reference:** https://github.com/ccieblogger/netraven/issues/99

---

## Phase 0: Preparation & Review

### Files Reviewed
- `frontend/src/pages/Dashboard.vue`
- `frontend/src/layouts/DefaultLayout.vue`
- `frontend/src/components/DeviceTable.vue`

### Key UI Elements Requiring Backend Data
- KPI cards (API, PostgreSQL, Redis, Worker, Scheduler, RQ)
- Device table (inventory, status, actions)
- Filters and search box
- Status icons and action buttons

### API Client
- Centralized Axios API client exists at `frontend/src/services/api.js`.
- Used throughout Pinia stores and services for backend communication.

### Data Models
- No dedicated `types/` directory found. Data models/interfaces are currently implicit in store usage and component props.

### API Endpoints Used (from codebase)
- `/api/devices/` (device list)
- `/api/system/status` (system health)
- `/api/jobs/` (job list)
- `/api/logs/` (logs)
- Additional endpoints for job actions, credentials, etc.

### Observations
- Most dashboard data is already fetched via Pinia stores using the centralized API client.
- Some data (e.g., RQ status) may require additional endpoints or wiring.
- No TypeScript interfaces; consider adding for clarity in future phases.

---

## Phase 1: API Client Integration & Data Models (Progress)

### Required API Methods for Dashboard Data
- **System/Service Status (KPIs):** `/api/system/status` (exists, used in Dashboard.vue and JobsDashboard.vue)
- **Device List & Inventory:** `/api/devices/` (exists, used in device store)
- **Job List & Job Stats:** `/api/jobs/` (exists, used in job store)
- **Log Stats:** `/api/logs/` (exists, used in log store)
- **RQ/Redis Queue Status:**
  - RQ queue/job/worker status is provided as part of `/api/system/status` (see JobsDashboard.vue, RQQueuesCard.vue, WorkerStatusCard.vue)
  - No separate `/api/rq` endpoint; all RQ/Redis/worker stats are consolidated in `/api/system/status`.

### API Client Usage
- All required endpoints are already accessible via the centralized API client (`api.js`).
- Pinia stores and dashboard components use these endpoints for data fetching.
- Some dashboard cards (e.g., RQ, Redis, Worker) may need to be refactored to consume the correct fields from the `/api/system/status` response.

### Data Models
- No explicit TypeScript interfaces for dashboard data; recommend adding in `/src/types/` in a future phase for maintainability.

### Next Steps
- [ ] Refactor Dashboard.vue to wire all KPI cards (including RQ) to live data from `/api/system/status`.
- [ ] Ensure all dashboard data is loaded via Pinia stores and the centralized API client.
- [ ] (Optional) Begin defining TypeScript interfaces for dashboard data.

---

**Phase 1 progress: All required API methods for dashboard data exist and are accessible. Preparing to wire Dashboard.vue to use only live backend data for all KPIs and inventory.** 