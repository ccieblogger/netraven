# NetRaven Dashboard & Job Monitoring UI – Design Specification

## 1. Purpose

Provide a clear, actionable blueprint for redesigning the NetRaven web UI so that network‑operations users can quickly assess overall system health, monitor job execution, and investigate detailed logs in real‑time.

---

## 2. Guiding Principles

- **Job‑centric first**: surface the most important job KPIs (success, failure, duration) within 2 clicks.
- **Progressive disclosure**: start with high‑level cards → drill‑down tables → detailed views.
- **Real‑time insight**: leverage WebSocket (or Server‑Sent Events) subscribed to Redis channels for live updates without refresh.
- **Consistency**: reuse Vue components & Tailwind utility classes; dark theme as default.
- **Responsive & accessible**: WCAG‑AA colours, keyboard navigation, mobile breakpoint at ≤ 768 px.

---

## 3. Personas & Use‑Cases

| Persona             | Goals                                                                | Typical Actions                                             |
| ------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------- |
| **NetOps Engineer** | Verify nightly backups ran, troubleshoot failed reachability checks. | View dashboard → open failed job → tail logs.               |
| **NOC Operator**    | Track live credential‑check batch job.                               | Watch progress bar + live log stream, escalate on errors.   |
| **System Admin**    | Ensure platform services are healthy.                                | Glance at system‑status tile, drill into container metrics. |

---

## 4. Key Views

### 4.1 Main Dashboard *(unchanged)*

[see earlier]

### 4.2 Job List View (`/jobs`)

[see earlier]

### 4.3 Job Detail View (`/jobs/:id`)

[see earlier]

### 4.4 System Status (`/status`)

[see earlier]

### 4.5 Global Log Stream (`/logs`)

[see earlier]

---

### 4.6 **Device Management**

- **Device List** (`/devices`): searchable table (hostname, **serial**, type, mgmt‑IP, last backup, tags, ✅ reachability status).
- **Device Detail** (`/devices/:id`): overview cards (serial number, interfaces, recent jobs, config diff button), tabs: *Overview · Jobs · Backups · Logs*.
- **Add / Edit Device** (`/devices/new`, `/devices/:id/edit`): wizard‑style modal with validation, **serial number** field, tag selector & credential mapping.

### 4.7 **Tag Management**

- **Tag List** (`/tags`): name, colour swatch, #devices, actions.
- **Add / Edit Tag** (`/tags/new`, `/tags/:id/edit`): colour picker + description.

### 4.8 **Credential Vault**

- **Credential List** (`/credentials`): username, method (SSH/SNMP/API), success‑rate %, last used timestamp.
- **Add / Edit Credential** (`/credentials/new`, `/credentials/:id/edit`): secret fields with show/hide toggle, device/tag scoping.
- **Success‑Rate Stats**: small spark‑line per row + detailed modal chart (computed from logs table where `log_type = 'connection'`).

### 4.9 **User & RBAC**

- **User List** (`/users`): username, role, last login, status.
- **Add / Edit User** (`/users/new`, `/users/:id/edit`): role dropdown, password reset, token revoke.

### 4.10 **Config Backups & Diff**

- **Backups View** (`/backups`): filter by device, date; columns: device, taken‑at, size, diff‑against‑previous 🔍.
- **Config Diff View** (`/backups/:deviceId/:backupId/diff`): side‑by‑side code block with inline diff highlighting (use `vue‑diff` or Monaco diff).

---

## 5. Information Architecture

```
Dashboard
├── Jobs
│   ├── List
│   └── Detail
├── Devices
│   ├── List
│   ├── Detail
│   ├── Add
│   └── Edit
├── Tags
│   ├── List
│   ├── Add
│   └── Edit
├── Credentials
│   ├── List
│   ├── Add
│   └── Edit
├── Backups
│   ├── List
│   └── Diff
├── Users
│   ├── List
│   ├── Add
│   └── Edit
├── Logs
└── System Status
```

```
Dashboard
├── Jobs
│   ├── List
│   └── Detail
├── Devices
├── Backups
├── Logs
└── System Status
```

---

## 6. Component Library & Breakdown

| Component       | Props                             | Description                            |          |                        |
| --------------- | --------------------------------- | -------------------------------------- | -------- | ---------------------- |
| `<KpiCard>`     | `title`, `value`, `trend`, `icon` | Reusable stat card.                    |          |                        |
| `<StatusBadge>` | `state` (success                  | fail                                   | running) | Small pill for tables. |
| `<LiveLog>`     | `source` (WS url), `filters`      | Handles WebSocket, buffer, autoscroll. |          |                        |
| `<JobTable>`    | `rows`, `onSelect`                | Paginated & sortable.                  |          |                        |
| `<SparkLine>`   | `data`                            | Tiny chart in card.                    |          |                        |

---

## 7. Navigation & Routing (Vue Router)

| Path                                | View           | Auth? |
| ----------------------------------- | -------------- | ----- |
| `/`                                 | Dashboard      | ✔     |
| `/jobs`                             | JobList        | ✔     |
| `/jobs/:id`                         | JobDetail      | ✔     |
| `/devices`                          | DeviceList     | ✔     |
| `/devices/new`                      | DeviceAdd      | ✔     |
| `/devices/:id`                      | DeviceDetail   | ✔     |
| `/devices/:id/edit`                 | DeviceEdit     | ✔     |
| `/tags`                             | TagList        | ✔     |
| `/tags/new`                         | TagAdd         | ✔     |
| `/tags/:id/edit`                    | TagEdit        | ✔     |
| `/credentials`                      | CredentialList | ✔     |
| `/credentials/new`                  | CredentialAdd  | ✔     |
| `/credentials/:id/edit`             | CredentialEdit | ✔     |
| `/users`                            | UserList       | ✔     |
| `/users/new`                        | UserAdd        | ✔     |
| `/users/:id/edit`                   | UserEdit       | ✔     |
| `/backups`                          | BackupList     | ✔     |
| `/backups/:deviceId/:backupId/diff` | ConfigDiff     | ✔     |
| `/logs`                             | LogStream      | ✔     |
| `/status`                           | Status         | ✔     |

---

## 8. Data Model & API Contracts (REST) Data Model & API Contracts (REST)

### 8.1 Jobs

`GET /api/jobs?status=failed&type=backup&limit=50`

```json
{
  "id": "f9c8…",
  "type": "device_backup",
  "devices": ["edge‑sw‑01"],
  "status": "failed",
  "started_at": "2025-04-26T19:31:24Z",
  "duration_secs": 42,
  "log_channel": "jobs:f9c8…"
}
```

### 8.2 Logs (Real‑Time & Query)
| Function | Endpoint | Notes |
|-----------|----------|-------|
| **List / filter** | `GET /logs/?job_id=&device_id=&log_type=&level=&page=&size=` | Paginates & filters per unified spec |
| **Single log** | `GET /logs/{log_id}` | Retrieve one entry |
| **Real‑time stream** | `GET /logs/stream?job_id={id}` (SSE) | Backend proxies Redis Pub/Sub (`session-logs:{job_id}`) → Server‑Sent Events. UI consumes via EventSource.
| **Meta lists** | `/logs/types`, `/logs/levels`, `/logs/stats` | Populate filters & KPI counts |

`/logs/stream` emits:
```text
: keepalive  # every 15s

event: log
data: {"timestamp":"…","level":"info", … }
```
 System Metrics

`GET /api/status`

```json
{ "api": "up", "redis": "up", "rq_workers": 3, "scheduler": "up" }
```

---

### 8.4 Log Table Schema

The unified `logs` table stores all job, device, and system log events. It is the primary source for the **Global Log Stream** and **Job Detail** views.

| Column      | Type                                             | Notes                                        |
| ----------- | ------------------------------------------------ | -------------------------------------------- |
| `id`        | `SERIAL PRIMARY KEY`                             | Unique entry identifier                      |
| `timestamp` | `TIMESTAMPTZ` (indexed)                          | UTC event time; default `now()`              |
| `log_type`  | `VARCHAR(32)` (indexed)                          | `job`, `connection`, `session`, etc.         |
| `level`     | `VARCHAR(16)` (indexed)                          | `info`, `warning`, `error`, `debug`          |
| `job_id`    | `INTEGER` (nullable, FK → `jobs.id`, indexed)    | Associates log with a job                    |
| `device_id` | `INTEGER` (nullable, FK → `devices.id`, indexed) | Associates log with a device                 |
| `source`    | `VARCHAR(64)`                                    | Service/module name (e.g. `worker.executor`) |
| `message`   | `TEXT`                                           | Human‑readable log line                      |
| `meta`      | `JSONB` (nullable)                               | Structured metadata for advanced filtering   |

**Indexes**

- `idx_logs_job_id` on `job_id`
- `idx_logs_device_id` on `device_id`
- `idx_logs_log_type` on `log_type`
- `idx_logs_level` on `level`
- `idx_logs_timestamp` on `timestamp`

The UI should leverage these indexes when constructing API queries—for example, filtering by `job_id` plus `level` enables sub‑second look‑ups even on millions of rows.

## 9. State Management

Use **Pinia** store with modules:

- `jobsStore` (list, currentJob, stats)
- `statusStore` (services, workers)
- `logStore` (buffers, filters)

---

## 10. Event Flow
1. Dashboard mounts → parallel fetch KPI (`/logs/stats`) + system status.
2. Subscribe to `jobs:events` channel (Redis‑backed SSE/WebSocket) for KPI counters.
3. On **JobDetail** open → create `EventSource('/logs/stream?job_id=123')` to stream live session logs; close on unmount.
4. Persisted logs displayed via paginated `GET /logs/?job_id=123` when scrolling back.

---

## 11. Accessibility & Responsiveness

- Use `<button aria‑label>` on icon buttons.
- High‑contrast colour vars: `--success: #10B981`, `--error: #EF4444`, ensured AA contrast on dark bg.
- Collapse sidebar on ≤ 1024 px; stacked card layout ≤ 768 px.

---

## 12. Tech Stack & Libraries

| Concern   | Choice                                   |
| --------- | ---------------------------------------- |
| Framework | **Vue 3 (Composition API)**              |
| Styling   | **TailwindCSS** + headlessui for dialogs |
| Charts    | **Apache ECharts** (lazy‑loaded)         |
| WebSocket | `@vueuse/core` `useWebSocket`            |
| Tables    | `vue‑table‑dynamic` or AG‑Grid CE        |

---

## 13. Future Enhancements

1. **Role‑based dashboards** (RBAC pins widgets).
2. **Alert rules** – push notification on job failure.
3. **Custom Job Types** – plug‑in UI config wizard.
4. **Theming** – light vs dark toggle.

---

## 14. Refactor‑First Migration Approach

Instead of rebuilding from scratch, we can evolve the existing Vue application. Please gather the following so we can map old → new:

| Area                       | What to Share                              | Why It Matters                                            |
| -------------------------- | ------------------------------------------ | --------------------------------------------------------- |
| **Project Repo**           | Git URL or ZIP; highlight `src/` structure | Determines current component hierarchy & build tooling    |
| **Vue & Library Versions** | `package.json`                             | Confirms compatibility (Vue 2 vs 3, Vuex vs Pinia, etc.)  |
| **Router Map**             | `router/index.*`                           | Lets us align new routes with existing guards & auth flow |
| **State Store Modules**    | Vuex/Pinia folder                          | Shows where job/log data is fetched & stored              |
| **Auth Flow**              | Login view, token refresh logic            | Critical to preserve SSO/JWT/OAuth behaviour              |
| **API Service Layer**      | Axios/Fetch wrappers                       | Identify endpoints to adjust for new log schema           |
| **Current Log Components** | Components consuming old log payload       | Pin‑point what breaks with schema change                  |
| **CSS/Theme Tokens**       | Tailwind config or SCSS vars               | Ensure visual consistency after tweaks                    |
| **Build & Deployment**     | Dockerfile / CI config                     | So refactor fits existing pipeline                        |

### Migration Steps

1. **Schema Adapter**: introduce a thin normaliser that maps new `logs` rows → old component props, letting UI run unmodified while refactor proceeds.
2. **Incremental Component Upgrade**: start with LogStream & JobDetail, swap in new Pinia stores & WebSocket subscription.
3. **Feature Flags**: ship refactored pages behind toggle for staged rollout.
4. **End‑to‑End Tests**: add Cypress workflows covering critical paths before changes.

Provide the artifacts above (or representative snippets), and we’ll draft a detailed refactor plan plus code‑level examples.

---

© 2025 NetRaven – Internal Design Document

