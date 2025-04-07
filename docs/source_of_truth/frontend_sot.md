## NetRaven Frontend Service: State of Technology (SOT)

### Executive Summary

This document outlines the architecture and implementation plan for the NetRaven frontend application. The UI is designed to provide an intuitive, modern dashboard experience for managing network devices, job scheduling, user permissions, and viewing configuration and log data. It is built using Vue.js and connects to the backend via the NetRaven FastAPI REST API.

The frontend should be simple to test and deploy locally, yet modular and extensible for long-term support. It will be built to support AI-assisted development.

### Core Responsibilities

- Authenticate via JWT against the backend API
- Provide CRUD interfaces for:
  - Devices and credentials
  - Device groups (tags)
  - Jobs (one-time, recurring)
  - Users and roles
- Allow job execution and job status monitoring
- Display per-device connection logs and job logs
- Show Git-based configuration diffs between job runs
- Expose real-time job status (device X succeeded, Y failed)
- Enforce user-role-based visibility

### Technology Stack

#### State Architecture Guidelines
- All global state (e.g., auth user info, selected job, user roles, device group filters) must be managed in **Pinia** stores under `/src/store`.
- Local component state (e.g., form input, modal visibility) should be handled using Vue Composition API inside each component.
- Cross-component communication (e.g., notifications, status messages) must use centralized Pinia stores or a dedicated `useNotifications()` composable.
- The `auth` store will manage JWT tokens and decode roles for access control.
- Role-based access to routes and features will be implemented using Vue Router guards + centralized role logic from Pinia.

```yaml
framework: Vue 3 (Composition API)
bundler: Vite
auth: JWT (stored in memory or localStorage)
routing: Vue Router
state_management: Pinia
design_system: TailwindCSS + Headless UI
api_client: Axios
charts: Chart.js
diff_viewer: Diff2Html
```

### State Management Scaffolding

Example Pinia stores to be created under `/src/store/`:

```js
// store/auth.js
import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null,
    user: null,
    role: null,
  }),
  actions: {
    setAuth(token, user) {
      this.token = token;
      this.user = user;
      this.role = user?.role || null;
    },
    logout() {
      this.token = null;
      this.user = null;
      this.role = null;
    }
  }
});
```

```js
// store/job.js
import { defineStore } from 'pinia';

export const useJobStore = defineStore('job', {
  state: () => ({
    selectedJob: null,
    jobResults: []
  }),
  actions: {
    setJob(job) {
      this.selectedJob = job;
    },
    setResults(results) {
      this.jobResults = results;
    }
  }
});
```

```js
// store/notifications.js
import { defineStore } from 'pinia';

export const useNotificationStore = defineStore('notifications', {
  state: () => ({ messages: [] }),
  actions: {
    addMessage(msg) {
      this.messages.push({ msg, ts: Date.now() });
    },
    clearMessages() {
      this.messages = [];
    }
  }
});
```

These stores should be preloaded in `App.vue` or main layout. Guards should pull user role from the `auth` store.

---

### Reusable UI Components

Create a shared library of reusable components inside `src/components/`:

```bash
/src/components/
├── BaseTable.vue        # Sortable, paginated table component
├── BaseModal.vue        # Reusable modal window
├── BaseForm.vue         # Form wrapper with slots for inputs
├── FormField.vue        # Label + validation wrapper
├── JobStatusTag.vue     # Displays job success/failure per device
├── DiffViewer.vue       # Git-style config difference viewer (wraps Diff2Html)
├── Toast.vue            # Notification toasts using notification store
```

These components should be registered globally or imported selectively in pages. Each should accept props for styling, data, and action callbacks.

---
```
/frontend/
├── public/
├── src/
│   ├── assets/
│   ├── components/
│   ├── layouts/
│   ├── pages/
│   │   ├── Dashboard.vue
│   │   ├── Devices.vue
│   │   ├── Jobs.vue
│   │   ├── Users.vue
│   │   └── Logs.vue
│   ├── router/
│   ├── store/
│   ├── services/        # Axios API clients
│   ├── utils/
│   └── App.vue
├── index.html
└── vite.config.js
```

### Key Screens and Components

#### Wireframe: Logs Viewer Page (Low-Fidelity)
```
+---------------------------------------------------------------+
|                          Logs Viewer                          |
+---------------------------------------------------------------+
| [Job ID: 123] [Device: core1] [▼ Select Filter]               |
+---------------------------------------------------------------+
| Timestamp            | Message                                 |
|----------------------|------------------------------------------|
| 2025-04-06 10:03:11  | Connecting to device core1...            |
| 2025-04-06 10:03:13  | Authentication successful.               |
| 2025-04-06 10:03:15  | Running 'show run'...                    |
| 2025-04-06 10:03:22  | Configuration captured (4.3 KB)          |
| 2025-04-06 10:03:23  | ✅ Job completed successfully.           |
+---------------------------------------------------------------+
```


#### Wireframe: Dashboard Page (Low-Fidelity)
```
+---------------------------------------------------------------+
|                          Dashboard                            |
+---------------------------------------------------------------+
| Total Devices: 45   | Active Jobs: 6   | Failed Jobs: 2        |
+---------------------------------------------------------------+
| Recent Jobs                                             [▶︎] |
|---------------------------------------------------------------|
| Job ID | Devices | Status   | Run Time | View                |
|--------|---------|----------|----------|----------------------|
| 120    | 12      | Success  | 1:05     | [View Monitor]       |
| 121    | 8       | Failed   | 0:50     | [View Monitor]       |
+---------------------------------------------------------------+
| Config Changes (last 7 days) | View Diffs                  |
+---------------------------------------------------------------+
```

#### Wireframe: Devices Page (Low-Fidelity)
```
+---------------------------------------------------------------+
|                        Device Manager                         |
+---------------------------------------------------------------+
| [ + Add Device ]  [ + Import from NetBox ]                    |
+---------------------------------------------------------------+
| Hostname | IP Address | Vendor | Group   | Actions            |
|----------|------------|--------|---------|---------------------|
| sw1      | 10.0.0.1   | Cisco  | Core    | [Edit] [Delete]     |
| fw2      | 10.0.1.1   | Palo   | Edge    | [Edit] [Delete]     |
+---------------------------------------------------------------+
```

#### Wireframe: Users Page (Low-Fidelity)
```
+---------------------------------------------------------------+
|                         User Admin                            |
+---------------------------------------------------------------+
| [ + Add User ]                                               |
+---------------------------------------------------------------+
| Username | Role   | Device Groups       | Actions              |
|----------|--------|---------------------|----------------------|
| admin    | admin  | all                 | [Edit] [Delete]      |
| jsmith   | user   | Core, Distribution  | [Edit] [Delete]      |
+---------------------------------------------------------------+
```

#### Wireframe: Job Monitor Page (Low-Fidelity)
```
+---------------------------------------------------------------+
|                         Job Monitor                           |
+---------------------------------------------------------------+
| Job ID: 123   | Status: Completed | Run Time: 01:23           |
+--------------------------+------------------------------------+
| Device Name              | Status     | View Log              |
+--------------------------+------------+------------------------+
| core1                    | ✅ Success | [View Log]             |
| edge2                    | ❌ Failed  | [View Log] (Timeout)   |
+--------------------------+------------+------------------------+

[ View Diff ] [ Retry Failed Devices ]
```

#### Wireframe: Job Scheduler Page (Low-Fidelity)
```
+---------------------------------------------------------------+
|                         Job Scheduler                         |
+---------------------------------------------------------------+
| [ + New Job ]                                                 |
+---------------------------------------------------------------+
| Job Name | Devices   | Type      | Schedule      | Actions    |
|----------|-----------|-----------|---------------|------------|
| Backup1  | Core      | Recurring | Daily @ 2am   | [Edit] [X] |
| Audit2   | Edge      | One-Time  | 2025-04-15    | [Edit] [X] |
+---------------------------------------------------------------+
```

#### Wireframe: Config Diff Viewer Page (Low-Fidelity)
```
+---------------------------------------------------------------+
|                     Configuration Diff                        |
+---------------------------------------------------------------+
| Device: core1         | Job ID: 123 vs 122                    |
+---------------------------------------------------------------+
| [Dropdown] Select Commit | [Compare]                         |
+---------------------------------------------------------------+
| - interface Gig0/1                                              |
| + interface Gig0/1 description Uplink to Firewall             |
|                                                                |
| - router ospf 1                                                |
| + router ospf 2                                                |
+---------------------------------------------------------------+
```

This layout includes job metadata, per-device status, log access buttons, and actions for diff viewing and retries.. It is intended to guide AI layout decisions and can be translated into a Vue component using TailwindCSS.


- **Login Page** – JWT auth, error handling
- **Dashboard** – Summary of jobs, device stats, logs
- **Device Manager** – Add/edit/delete devices and groups
- **Job Scheduler** – Create/edit jobs, assign devices or groups, view schedule
- **Job Monitor** – See job status, per-device success/failure, and logs
- **Config Diff Viewer** – View changes in device config between commits
- **User Admin** – Manage roles, assign group visibility
- **Logs Viewer** – Per-device and per-job logs, searchable

### Route Expectations
```text
GET /devices
POST /devices
GET /jobs
POST /jobs
GET /logs?job_id=123
GET /users
POST /auth/token
```

### Example API Response (Job Status)
```json
{
  "job_id": 123,
  "status": "completed",
  "results": [
    {"device": "core1", "status": "success", "log_id": 88},
    {"device": "edge2", "status": "fail", "error": "timeout", "log_id": 89}
  ]
}
```

### Dev Setup
```bash
cd frontend
npm install
npm run dev
```

### Route Guards

To enforce role-based access, the router should include guards that read from the `auth` store and redirect unauthorized users.

```js
// router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../store/auth';
import Dashboard from '../pages/Dashboard.vue';

const routes = [
  {
    path: '/dashboard',
    component: Dashboard,
    meta: { requiresAuth: true, roles: ['admin', 'user'] }
  },
  // ...other routes
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.token) {
    return next('/login');
  }
  if (to.meta.roles && !to.meta.roles.includes(auth.role)) {
    return next('/unauthorized');
  }
  next();
});

export default router;
```

### Axios API Client Setup

Centralize all API calls using Axios with JWT handling:

```js
// services/api.js
import axios from 'axios';
import { useAuthStore } from '../store/auth';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

api.interceptors.request.use((config) => {
  const auth = useAuthStore();
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`;
  }
  return config;
});

export default api;
```

### Testing Plan
- Unit tests for components (Vue Test Utils)
- Mock API integration using MSW or Axios-mock-adapter
- E2E tests with Playwright or Cypress

---
