# NetRaven Dashboard & Job Monitoring UI – Design Specification

## 1. Purpose

Provide a clear, actionable blueprint for redesigning the NetRaven web UI so that network‑operations users can quickly assess platform health and manage devices efficiently.

---

## 2. Guiding Principles

- **Device-first**: surface the most important device metrics and actions with one click.
- **Progressive disclosure**: start with service status & device inventory → drill-down pages.
- **Consistency**: reuse Vue components & Tailwind utility classes.
- **Responsive & accessible**: WCAG-AA colours, keyboard navigation; mobile breakpoint at ≤ 768 px.

---

## 3. Personas & Use‑Cases

| Persona             | Goals                                           | Typical Actions                                         |
| ------------------- | ----------------------------------------------- | ------------------------------------------------------- |
| **NetOps Engineer** | Run ad‑hoc checks, view device health.          | Filter device list → click “Reachability” / “Cred‑Chk”. |
| **NOC Operator**    | Monitor service status; triage device failures. | Glance at heartbeat row → open device detail.           |
| **System Admin**    | Ensure platform services remain available.      | Watch heartbeat row; verify scheduled backups.          |

---

## 4. Key Views

### 4.1 Main Dashboard (`/`)

**Purpose**: Provide an at‑a‑glance view of **service health** and a **filterable device list** with inline actions.

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ● API  ● Redis  ● RQ Workers  ● Postgres  ● Nginx                         │
│ (service heartbeat row polls `/api/status` every 15s)                     │
├────────────────────────────────────────────────────────────────────────────┤
│ [Group ▾]  🔍 Hostname / IP search                                          │
│                                                                            │
│ Hostname        Host IP      Serial        Reachable  JobStat   Actions    │
│ edge-sw-01      10.0.0.2     JAE0938D2G8   ✅          ✅        ⟳ 🔑 📄    │
│ access-ap-17    10.0.5.17    9A2C0183GHK   ❌          ❌        ⟳ 🔑 📄    │
│ …                                                                        ▼ │
└────────────────────────────────────────────────────────────────────────────┘
```

**Pagination controls**: « Prev [1] [2] [3] … Next »

**Behaviour**

- **Service row**: dots with latency tooltip & last‑ping timestamp.
- **Group filter**: dropdown from `/api/tags`; defaults to *All*.
- **Search**: client‑side filter by hostname or IP.
- **Reachable / JobStat**: badges from latest job results.
- **Actions**:
  - ⟳ **Reachability** → `POST /api/jobs {type:"reachability",device_id}`
  - 🔑 **Credential‑check** → `POST /api/jobs {type:"credential_check",device_id}`
  - 📄 **View Configs** → navigate to `/backups?device_id=`

---

### 4.2 Jobs Dashboard (`/jobs/dashboard`)

**Purpose**: Surface high‑level job KPIs separately.

```
┌─────────┬─────────┬─────────┬───────────────┐
│  98 %   │   3     │   2     │   0:48 s      │
│ Success │ Failed  │ Running │ Avg Duration  │
└─────────┴─────────┴─────────┴───────────────┘
```

*(Click a card to open filtered Job List.)*

---

### 4.3 Job List View (`/jobs`)

Searchable table of jobs with columns: ID, Type, Devices, Status, Duration, Started. Bulk actions & link to detail.

---

### 4.4 Job Detail View (`/jobs/:id`)

Two‑column layout:

- **Left:** metadata (type, schedule, devices).
- **Right:** paginated log table via `GET /api/logs?job_id=`.

Collapsible **Result Artifacts** section with download links.

---

### 4.5 Device Management

- **Device List** (`/devices`): columns: Hostname, Host IP, Serial, Reachable, JobStat, Actions; paginated.
- **Device Detail** (`/devices/:id`): cards (serial, model, OS, tags), tabs: Overview · Jobs · Backups.
- **Add / Edit Device** (`/devices/new`, `/devices/:id/edit`): form fields: Hostname, Host IP, Serial, Tags, Credential mapping.

---

### 4.6 Tag Management

- **Tag List** (`/tags`): name, colour swatch, #devices, actions.
- **Add / Edit Tag** (`/tags/new`, `/tags/:id/edit`): colour picker + description.

---

### 4.7 Credential Vault

- **Credential List** (`/credentials`): username, method, success‑rate %, last used.
- **Add / Edit Credential** (`/credentials/new`, `/credentials/:id/edit`): secret field toggle, scope by device/tag.

---

### 4.8 User & RBAC

- **User List** (`/users`): username, role, last login, status.
- **Add / Edit User** (`/users/new`, `/users/:id/edit`): role dropdown, password reset, token revoke.

---

### 4.9 Config Backups & Diff

- **Backups View** (`/backups`): device/date filters, columns: device, timestamp, size, diff link.
- **Config Diff View** (`/backups/:deviceId/:backupId/diff`): side‑by‑side diff viewer (Monaco or Vue‑Diff).

---

## 5. Information Architecture

```
Dashboard
├── Jobs
│   ├── Dashboard
│   ├── List
│   └── Detail
├── Devices
│   ├── List
│   ├── Add
│   ├── Detail
│   └── Edit
├── Tags
│   ├── List
│   ├── Add
│   └── Edit
├── Credentials
│   ├── List
│   ├── Add
│   └── Edit
├── Users
│   ├── List
│   ├── Add
│   └── Edit
└── Backups
    ├── List
    └── Diff
```

---

## 6. Component Library & Breakdown

| Component       | Props                        | Description                  |            |               |
| --------------- | ---------------------------- | ---------------------------- | ---------- | ------------- |
| `<ServiceDot>`  | `service`,`status`,`latency` | Status dot with tooltip.     |            |               |
| `<DeviceTable>` | `rows`,`onAction`            | Paginated device table.      |            |               |
| `<KpiCard>`     | `title`,`value`,`trend`      | Reusable stat card.          |            |               |
| `<Badge>`       | `type`(\`success             | fail                         | running\`) | Status badge. |
| `<DiffViewer>`  | `oldConfig`,`newConfig`      | Side‑by‑side diff component. |            |               |

---

## 7. Navigation & Routing (Vue Router)

| Path                                | View               | Auth? |
| ----------------------------------- | ------------------ | ----- |
| `/`                                 | **Dashboard**      | ✔     |
| `/jobs/dashboard`                   | **JobsDashboard**  | ✔     |
| `/jobs`                             | **JobList**        | ✔     |
| `/jobs/:id`                         | **JobDetail**      | ✔     |
| `/devices`                          | **DeviceList**     | ✔     |
| `/devices/new`                      | **DeviceAdd**      | ✔     |
| `/devices/:id`                      | **DeviceDetail**   | ✔     |
| `/devices/:id/edit`                 | **DeviceEdit**     | ✔     |
| `/tags`                             | **TagList**        | ✔     |
| `/tags/new`                         | **TagAdd**         | ✔     |
| `/tags/:id/edit`                    | **TagEdit**        | ✔     |
| `/credentials`                      | **CredentialList** | ✔     |
| `/credentials/new`                  | **CredentialAdd**  | ✔     |
| `/credentials/:id/edit`             | **CredentialEdit** | ✔     |
| `/users`                            | **UserList**       | ✔     |
| `/users/new`                        | **UserAdd**        | ✔     |
| `/users/:id/edit`                   | **UserEdit**       | ✔     |
| `/backups`                          | **BackupList**     | ✔     |
| `/backups/:deviceId/:backupId/diff` | **ConfigDiff**     | ✔     |

---

## 8. Data Model & API Contracts (REST)

### 8.1 Devices

`GET /api/devices?page=&size=&tag=&reachable=` and pagination parameters.

### 8.2 Tags

CRUD endpoints: `/api/tags`

### 8.3 Credentials

CRUD endpoints: `/api/credentials` (includes `success_rate`).

### 8.4 Users

CRUD endpoints: `/api/users` (admin only).

### 8.5 Backups

- `GET /api/backups?device_id=&from=&to=`
- `GET /api/backups/{id}/diff?against={prevId}`

---

## 9. State Management

**Pinia** stores:

- `serviceStore` (status dots)
- `deviceStore` (list/detail)
- `jobStore` (dashboard/list)
- `backupStore` (list/diff)
- `credentialStore`, `tagStore`, `userStore`

---

## 10. Event Flow

1. **Dashboard** → fetch `/api/status` + `/api/devices`.
2. **JobsDashboard** → fetch KPI stats.
3. **DeviceList** → inline job actions & refresh row.
4. **Detail pages** → fetch entity data.

---

## 11. Accessibility & Responsiveness

This UI has been built with accessibility and responsive design baked in, leveraging existing components:

- **ARIA & semantics**

  - Buttons and icon-only controls (e.g., in `<NavBar>`, `<PaginationControls>`, `<NotificationToast>`) include `aria-label` or `aria-haspopup` attributes.
  - `<ResourceFilter>` uses native `<select>` elements with `<label>` wrappers for screen-reader compatibility.
  - Modals (`<BaseModal>`, `<DeviceFormModal>`, etc.) trap focus as implemented by Headless UI’s `Dialog` component.

- **Keyboard navigation**

  - `<LiveLog>` stream table and `<BaseTable>` support row focus and keyboard arrow-key navigation.
  - `<PaginationControls>` expose prev/next links and page numbers as accessible buttons.

- **Color contrast & feedback**

  - Status badges (`<Badge>`) and `ServiceDot` colors meet WCAG AA for foreground/text ratios.
  - Toast notifications (`<NotificationToast>`) announce success/error via `role="alert"`.

- **Responsive breakpoints**

  - Tables collapse to stacked cards at `sm` (≤640px) using Tailwind’s `block sm:table` pattern in `<BaseTable>`.
  - Sidebar navigation (`<NavBar>`) toggles to hamburger menu at `md` (≤768px).
  - Forms and modals are fluid width (`w-full max-w-md`) to adapt to mobile screens.

- **Testing & linting**

  - Integrated `eslint-plugin-jsx-a11y` and Tailwind’s `@tailwindcss/forms` plugin ensure form elements are accessible.
  - Cypress Axe tests validate each route scores ≥ 90 for common accessibility violations.

---

## 12. Tech Stack & Libraries Tech Stack & Libraries

This UI uses the following core dependencies (from `frontend/package.json`):

| Concern   | Library                       | Version  | Notes                      |
| --------- | ----------------------------- | -------- | -------------------------- |
| Framework | `vue`                         | ^3.5.13  | Composition API            |
| Router    | `vue-router`                  | ^4.5.0   | Declarative routing        |
| State     | `pinia`                       | ^3.0.1   | Store modules              |
| HTTP      | `axios`                       | ^1.8.4   | Promise-based client       |
| Styling   | `tailwindcss`                 | ^3.3.5   | Utility-first CSS          |
| Forms     | `@tailwindcss/forms`          | ^0.5.7   | Styled form elements       |
| UI Prims  | `@headlessui/vue`             | ^1.7.23  | Accessible primitives      |
| Icons     | `@heroicons/vue`              | ^2.2.0   | SVG icons                  |
| Charts    | `chart.js`                    | ^4.4.8   | KPI visualizations         |
| Dates     | `dayjs`                       | ^1.11.13 | Date utilities             |
| Diff      | `diff2html`                   | ^3.4.51  | Config diff HTML rendering |
| Build     | `vite` & `@vitejs/plugin-vue` | ^5.0.0   | Dev server & build         |

---

## 13. Future Enhancements

1. **Global Log Stream** – real-time viewer via SSE.
2. **Alert rules** – push notifications on failure.

\--- Future Enhancements

1. **Global Log Stream** – real-time viewer via SSE.
2. **Alert rules** – push notifications on failure.

\--- Future Enhancements

1. **Global Log Stream** – real-time viewer via SSE.
2. **Alert rules** – push notifications on failure.

---

## 14. Refactor‑First Migration Approach

*(strategy unchanged)*

© 2025 NetRaven – Internal Design Document

