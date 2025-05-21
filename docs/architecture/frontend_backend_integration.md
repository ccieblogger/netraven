# Frontend–Backend Integration Guide for NetRaven

## Purpose
This document provides clear, step-by-step guidance for frontend developers on how to wire up UI/UX components to backend API endpoints in NetRaven. It covers best practices, common patterns, and examples for creating new or updating existing frontend routes and API calls.

---

## 1a. NGINX Proxying and the `/api` Prefix

All frontend API requests are routed through an NGINX reverse proxy, which is responsible for forwarding requests from the frontend to the backend FastAPI service. This is a critical part of the NetRaven deployment model and has several implications for frontend-backend integration:

- **Always use the `/api` prefix** for all backend API calls from the frontend. NGINX is configured to route requests with this prefix to the FastAPI backend container.
- **Do not use absolute backend URLs** (e.g., `http://localhost:8000/devices`). Instead, use relative paths like `/api/devices` so that requests are properly proxied in all environments (dev, prod, containerized).
- **CORS and Auth:** NGINX handles CORS headers and ensures that cookies, JWT tokens, and credentials are forwarded correctly. If you encounter CORS errors, check both the NGINX config and FastAPI CORS settings.
- **Troubleshooting:**
  - If you get 404 errors for API calls, ensure the `/api` prefix is present in your request path.
  - If authentication fails, verify that the JWT token is being sent and that NGINX is not stripping auth headers.
  - For local development, ensure the frontend and backend containers are both running and that NGINX is accessible at the expected port.

**Summary:**
> All API calls from the frontend must use the `/api` prefix and go through NGINX. Never call the backend service directly or bypass the proxy.

---

## 1. Overview: How the Frontend Talks to the Backend

- **All API calls are made via a centralized Axios client in `frontend/src/services/api.js`.**
- **All API requests are routed through Nginx and must use the `/api` prefix.**
- **JWT authentication is required for all protected endpoints.**
- **Pinia stores and service modules encapsulate most API logic.**
- **Device objects now include the following fields (added 2025):**
  - `serial_number`, `model`, `source`, `notes`, `last_updated`, `updated_by`
  - See the [API spec](./netraven_api_spec.md#devices) for details and usage.

---

## 2. Adding or Updating API Calls in the Frontend

### Step 1: Use the Centralized API Client
- Import the `api` instance from `frontend/src/services/api.js`.
- The client automatically attaches the JWT token and handles `/api` prefixing.

```js
import api from '../services/api';

// Example: Fetch devices
const response = await api.get('/devices/');
```

### Step 2: Add Service Functions (Recommended)
- For reusable logic, add functions to a service file (e.g., `frontend/src/services/devices.js`).
- Example:

```js
// devices.js
import api from './api';
export function fetchDevices() {
  return api.get('/devices/');
}
```

### Step 3: Use in Pinia Stores or Components
- Call service functions from Pinia stores or directly in components as needed.
- Example (in a store):

```js
import { fetchDevices } from '../services/devices';

export const useDeviceStore = defineStore('device', {
  actions: {
    async loadDevices() {
      this.devices = await fetchDevices();
    }
  }
});
```

---

## 3. Creating New Frontend Routes That Interact with the Backend

- Define new routes in `frontend/src/router/index.js`.
- Create a corresponding page/component in `frontend/src/pages/`.
- Use Pinia stores or service functions to fetch data from the backend.
- Example route:

```js
{
  path: '/devices',
  name: 'Devices',
  component: Devices,
  meta: { requiresAuth: true, roles: ['admin', 'user'] }
}
```

---

## 4. Authentication & Error Handling

- The API client automatically attaches the JWT token from localStorage.
- 401 errors trigger a logout and redirect to the login page.
- Handle errors in your store/component logic and provide user feedback.

---

## 5. Common Pitfalls & Tips

- **Always use the `/api` prefix for backend endpoints.**
- **Do not hardcode the backend URL; use relative paths.**
- **Do not bypass the centralized API client.**
- **Check the API spec in `docs/architecture/netraven_api_spec.md` for endpoint details.**
- **Use service modules to avoid code duplication.**

---

## 6. Example: Adding a New API Call

Suppose you want to add a button to trigger a job run from the UI:

1. Add a function in a service module:
   ```js
   // jobs.js
   import api from './api';
   export function runJob(jobId) {
     return api.post(`/jobs/run/${jobId}`);
   }
   ```
2. Call this function from your component or store action:
   ```js
   import { runJob } from '../services/jobs';
   // ...
   await runJob(selectedJobId);
   ```
3. Handle success/error and update UI as needed.

---

## 7. Reference: Where to Find Things

- **API client:** `frontend/src/services/api.js`
- **Service modules:** `frontend/src/services/`
- **Pinia stores:** `frontend/src/store/`
- **Router config:** `frontend/src/router/index.js`
- **API spec:** `docs/architecture/netraven_api_spec.md`

---

## 8. Further Reading
- See `docs/architecture/netraven_api_spec.md` for endpoint details and request/response formats.
- See developer logs in `docs/developer_logs/` for real-world integration examples.

---

## 9. FAQ

**Q: How do I add a new API endpoint?**
A: Add a function in a service module, use it in your store/component, and ensure the backend endpoint is documented in the API spec.

**Q: How do I handle authentication?**
A: The API client handles JWT tokens automatically. Use the login/logout actions in the auth store.

**Q: What if I get a 401 error?**
A: The client will log out the user and redirect to login. Check your token and login flow.

---

_Last updated: 2025-05-17_
