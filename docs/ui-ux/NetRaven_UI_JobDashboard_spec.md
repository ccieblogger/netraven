# NetRaven Job Status Dashboard — Implementation Spec (Aligned with NetRaven Architecture)

---

## Tech Stack Overview

- **Frontend:** Vue 3 (Vite, Pinia, TailwindCSS, PrimeVue)
- **Backend:** FastAPI (Python), REST API, JWT Auth
- **Database:** PostgreSQL (SQLAlchemy, Alembic)
- **Job Scheduling:** Redis + RQ + RQ Scheduler
- **Worker:** Python, Netmiko (for device comms)
- **Logging:** Unified log table in PostgreSQL
- **Version Control:** GitPython (local repo for config snapshots)

---

## Project Coding Principles

- **Simple Solutions:** Prefer straightforward, maintainable code.
- **DRY Principle:** Avoid code duplication; reuse existing logic.
- **File Size:** Refactor files >300 lines for readability.
- **Change Scope:** Only change what's required for the task.
- **Legacy Removal:** Remove old logic if new patterns are introduced.
- **Deployment Awareness:** Ensure changes fit deployment model.
- **Resource Cleanup:** Remove temp files/scripts after use.
- **Testing:** Use mock data for UI/dev, not in production.
- **Branching:** Work in feature branches, merge via PR after testing.
- **Documentation:** Log all changes in `/docs/developer_logs/` or GitHub issues.

---

## 1. Page Structure (with NetRaven Alignment)

```
┌───────────────────────────────────────────────────────────────────────┐
│ Breadcrumbs: Home / Dashboard / Job Status           [⟳ Refresh]    │
│  (use <PageHeader> or .page-header bg-body text-heading)             │
├───────────────────────────────────────────────────────────────────────┤
│                     Job Status Dashboard (H1)  (text-heading)        │
├───────────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────────────────┐ │
│ │  Summary Cards Grid (Total, Running, Succeeded, Failed)           │ │
│ │  (bg-card, text-body, text-primary/success/warning/danger)        │ │
│ └───────────────────────────────────────────────────────────────────┘ │
├───────────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────────────────┐ │
│ │  <TabView class="bg-card p-6 rounded-lg shadow">                  │ │
│ │  ├── Tab: Job Runs (DataTable, filterable)                        │ │
│ │  ├── Tab: Unified Logs (DataTable, filterable, log type/level)    │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Sources & API Endpoints

- **Jobs:** `/jobs/`, `/jobs/status` (list, status, details)
- **Logs:** `/logs/` (filterable by job_id, device_id, log_type, level, etc.)
- **Log Types/Levels:** `/logs/types`, `/logs/levels`
- **Live Log Stream:** `/logs/stream` (for real-time updates)
- **Auth:** `/api/auth/token` (JWT, required for all endpoints)

---

## 3. Component & Styling Breakdown

| Section            | PrimeVue Component              | NetRaven Classes/Notes                                                                                 |
| ------------------ | ------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Page Header**    | `<PageHeader>`                  | `bg-body text-heading px-6 py-4 flex items-center justify-between`                                     |
| **Refresh Button** | `<Button icon="pi pi-refresh">` | `btn-outline btn-primary`                                                                              |
| **Summary Cards**  | `<Card>` + `<Tag>`              | `bg-card p-4 rounded-lg shadow text-body text-primary/success/warning/danger`                         |
| **Tabs Wrapper**   | `<TabView>`                     | `bg-card p-6 rounded-lg shadow`                                                                       |
| **Filters Bar**    | `Dropdown`, `InputText`,        | `flex flex-wrap items-center gap-4 mb-4 px-6` (bind to Pinia store, map to API query params)          |
|                    | `MultiSelect`, `Calendar`,      |                                                                                                        |
|                    | `Button`                        |                                                                                                        |
| **DataTable**      | `<DataTable>` + `<Column>`      | `overflow-x-auto px-6 bg-card rounded-lg shadow`                                                      |
| **Status Tag**     | `<Tag>`                         | Use `severity` prop, map to job/log status                                                            |
| **Action Buttons** | `<Button icon="pi pi-search">`  | `btn-text btn-icon`                                                                                    |

---

## 4. State Management & Data Flow

- **Pinia Stores:**
  - `jobs` (list, status, filters)
  - `logs` (list, filters, types, levels)
  - `auth` (JWT token, user info)
- **On Page Load:** Fetch summary stats, jobs, logs (mock data first, then real API)
- **On Filter Change:** Re-query API endpoints with filter params
- **On Refresh:** Re-fetch all data
- **Live Updates:** Optionally use `/logs/stream` for real-time log updates

---

## 5. Security & Auth

- All API calls require Bearer token (JWT)
- Role-based UI: Only show data/actions permitted by user's role

---

## 6. Implementation Plan (Phased, Multi-Stream)

### Work Stream 1: UI/UX & Mock Data (Look & Feel)
- **Goal:** Build the full dashboard UI using mock data for jobs/logs.
- **Tasks:**
  - Scaffold `JobDashboard.vue` and subcomponents (`JobSummaryCards.vue`, `JobRunsTable.vue`, `UnifiedLogsTable.vue`, `JobFiltersBar.vue`).
  - Implement PrimeVue DataTable, TabView, Cards, Filters, and Theming.
  - Use Pinia stores with mock data for jobs/logs.
  - Ensure all filters, tabs, and summary cards update UI state from mock data.
  - Style using Tailwind and project theme tokens.
- **Deliverable:** Fully interactive dashboard with mock data, ready for review.

### Work Stream 2: API Integration & Real Data
- **Goal:** Wire up dashboard to backend REST API endpoints.
- **Tasks:**
  - Replace mock data in Pinia stores with real API calls (Axios/Fetch).
  - Implement JWT auth (retrieve/store token, attach to requests).
  - Map filter controls to API query params.
  - Handle pagination, sorting, error states.
  - Add support for live log stream (`/logs/stream`) if required.
- **Deliverable:** Dashboard displays real job/log data from backend, with full filtering and live updates.

### Work Stream 3: Testing & Documentation
- **Goal:** Ensure quality, maintainability, and handoff readiness.
- **Tasks:**
  - Write unit tests for all components (mock data).
  - Write integration tests for API-connected components.
  - Add E2E tests for user workflows (filters, refresh, live updates).
  - Document all component props, store actions, and API usage.
  - Maintain a developer log in `/docs/developer_logs/feature-branch-name/`.
- **Deliverable:** Tested, documented dashboard ready for merge and deployment.

---

## 7. Developer Handoff Checklist

- [ ] Feature branch created for JobDashboard
- [ ] All components scaffolded and styled
- [ ] Pinia stores set up with mock data
- [ ] API integration complete
- [ ] All filters, tables, and cards functional
- [ ] Unit, integration, and E2E tests written
- [ ] Developer log and README updated
- [ ] PR submitted for review

---

## 8. Notes for Developers

- Use only mock data until UI is approved.
- Follow project coding principles and theming conventions.
- Document all changes and decisions in the developer log.
- Coordinate with other work streams to avoid merge conflicts.
- Ask for clarification if any API or UI detail is unclear.

---

# End of Spec
