# NetRaven API Specification

## Introduction
NetRaven exposes a RESTful API for managing network device configuration backups, job scheduling, user management, logging, and more. This document provides a comprehensive reference for all available API endpoints, their usage, and integration guidelines.

- **Base URL:** `http://<host>:8000/`
- **Authentication:** JWT Bearer Token (see below)
- **Content-Type:** `application/json` (unless otherwise specified)

## Authentication
All endpoints (except authentication/token) require a valid JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Obtain a token via the `/auth/token` endpoint using username and password.

---

## Endpoint Categories

- **System & Health**
- **Authentication**
- **Users**
- **Devices**
- **Tags**
- **Credentials**
- **Jobs**
- **Job Results**
- **Logs**
- **Scheduler**
- **Backups**

---

## Endpoints Inventory

### System & Health
#### `GET /health` — API health check
**Description:** Simple health check endpoint. Returns a static status to verify the API is running.

**Authentication:** None required.

**Request Example:**
```http
GET /health HTTP/1.1
Host: localhost:8000
```
**Response Example:**
```json
{
  "status": "healthy"
}
```
**Frontend Notes:**
- Use to check API liveness (e.g., for UI splash/loading screens or health indicators).

---

#### `GET /system/status` — System status overview
**Description:** Returns the health status of all core system components (API, PostgreSQL, Redis, Worker, Scheduler) and the current system time.

**Authentication:** None required.

**Request Example:**
```http
GET /system/status HTTP/1.1
Host: localhost:8000
```
**Response Example:**
```json
{
  "api": "healthy",
  "postgres": "healthy",
  "redis": "healthy",
  "worker": "healthy",
  "scheduler": "healthy",
  "system_time": "2024-06-09T12:34:56.789Z"
}
```
**Frontend Notes:**
- Use for system status dashboards.
- Each field is a string: "healthy" or "unhealthy".
- `system_time` is an ISO8601 UTC timestamp.

---

### Authentication
#### `POST /auth/token` — Obtain JWT access token
**Description:** Obtain a JWT access token for authenticated API usage. **Request must be `application/x-www-form-urlencoded`** (not JSON).

**Authentication:** None required.

**Request Example:**
```http
POST /auth/token HTTP/1.1
Host: localhost:8000
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```
**Response Example:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
**Frontend Notes:**
- Use the returned `access_token` as a Bearer token in the `Authorization` header for all subsequent requests.
- Example: `Authorization: Bearer <access_token>`
- If authentication fails, response is HTTP 401 with:
  ```json
  {
    "detail": "Incorrect username or password"
  }
  ```

---

### Users
#### `GET /users/` — List users
**Description:** List all users with pagination and optional filtering. **Admin only.**

**Authentication:** Bearer token (admin role required).

**Query Parameters:**
- `page` (int, default 1): Page number.
- `size` (int, default 20): Items per page.
- `username` (str, optional): Filter by username (partial match).
- `role` (str, optional): Filter by role (`admin` or `user`).
- `is_active` (bool, optional): Filter by active status.

**Request Example:**
```http
GET /users/?page=1&size=2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "items": [
    {
      "id": 1,
      "username": "admin",
      "role": "admin",
      "is_active": true
    },
    {
      "id": 2,
      "username": "user1",
      "role": "user",
      "is_active": true
    }
  ],
  "total": 2,
  "page": 1,
  "size": 2,
  "pages": 1
}
```
**Frontend Notes:**
- Use for user management tables.
- `items` is a list of user objects (no passwords).
- Pagination fields: `total`, `page`, `size`, `pages`.

> **NOTE:** The Users endpoint is not fully implemented. User management is incomplete, not production-ready, and subject to change. Some features and fields described below may not be available or may change in future releases.

---

#### `POST /users/` — Create user
**Description:** Create a new user. **Admin only.**

**Authentication:** Bearer token (admin role required).

**Request Example:**
```json
{
  "username": "newuser",
  "password": "secureP@ssw0rd",
  "email": "newuser@example.com",
  "full_name": "New User",
  "role": "user"
}
```
**Response Example:**
```json
{
  "id": 3,
  "username": "newuser",
  "email": "newuser@example.com",
  "full_name": "New User",
  "role": "user",
  "is_active": true
}
```
**Frontend Notes:**
- Password is only sent in the request, never returned in the response.
- If username already exists, response is HTTP 400:
  ```json
  { "detail": "Username already registered" }
  ```

---

#### `GET /users/me` — Get current user profile
**Description:** Get the currently authenticated user's profile.

**Authentication:** Bearer token (any user).

**Request Example:**
```http
GET /users/me HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "Admin User",
  "role": "admin",
  "is_active": true
}
```
**Frontend Notes:**
- Use for user profile display and session info.

---

#### `GET /users/{user_id}` — Get user by ID
**Description:** Get a user by ID. **Admin only.**

**Authentication:** Bearer token (admin role required).

**Request Example:**
```http
GET /users/2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "id": 2,
  "username": "user1",
  "email": "user1@example.com",
  "full_name": "User One",
  "role": "user",
  "is_active": true
}
```
**Frontend Notes:**
- Use for user detail views or edit forms.

---

#### `PUT /users/{user_id}` — Update user
**Description:** Update an existing user. **Admin only.**

**Authentication:** Bearer token (admin role required).

**Request Example:**
```json
{
  "email": "updated@example.com",
  "full_name": "Updated Name",
  "role": "admin",
  "is_active": false
}
```
**Response Example:**
```json
{
  "id": 2,
  "username": "user1",
  "email": "updated@example.com",
  "full_name": "Updated Name",
  "role": "admin",
  "is_active": false
}
```
**Frontend Notes:**
- Only fields provided in the request are updated.
- Password can be updated by including `"password": "newPassword"` in the request.

---

#### `DELETE /users/{user_id}` — Delete user
**Description:** Delete a user by ID. **Admin only.**

**Authentication:** Bearer token (admin role required).

**Request Example:**
```http
DELETE /users/2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response:**
- HTTP 204 No Content (no body).

**Frontend Notes:**
- Use for user management delete actions.
- If user not found, response is HTTP 404:
  ```json
  { "detail": "User not found" }
  ```

---

### Devices
#### `GET /devices/` — List devices
**Description:** List all devices with pagination and optional filtering.

**Authentication:** Bearer token required.

**Query Parameters:**
- `page` (int, default 1): Page number.
- `size` (int, default 20): Items per page.
- `hostname` (str, optional): Filter by partial hostname match.
- `ip_address` (str, optional): Filter by partial IP address match.
- `device_type` (str, optional): Filter by device type (exact match).
- `tag_id` (list[int], optional): Filter by tag IDs (devices with ANY of the specified tags).

**Request Example:**
```http
GET /devices/?page=1&size=2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "items": [
    {
      "id": 1,
      "hostname": "core-switch-01",
      "ip_address": "192.168.1.1",
      "device_type": "cisco_ios",
      "description": "Core Switch in Data Center 1",
      "port": 22,
      "created_at": "2024-06-09T12:34:56.789Z",
      "last_seen": "2024-06-09T13:00:00.000Z",
      "tags": [
        { "id": 1, "name": "core-network", "type": "location" }
      ],
      "matching_credentials_count": 2,
      "last_reachability_status": "success",
      "last_reachability_timestamp": "2024-06-09T13:00:00.000Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 2,
  "pages": 1
}
```
**Frontend Notes:**
- Use for device inventory tables.
- `tags` is a list of tag objects.
- `matching_credentials_count` is the number of credentials matching this device's tags.
- `last_reachability_status` can be `success`, `failure`, or `never_checked`.

---

#### `POST /devices/` — Create device
**Description:** Create a new device.

**Authentication:** Bearer token required.

**Request Example:**
```json
{
  "hostname": "core-switch-02",
  "ip_address": "192.168.1.2",
  "device_type": "cisco_ios",
  "description": "Second core switch",
  "port": 22,
  "tags": [1]
}
```
**Response Example:**
```json
{
  "id": 2,
  "hostname": "core-switch-02",
  "ip_address": "192.168.1.2",
  "device_type": "cisco_ios",
  "description": "Second core switch",
  "port": 22,
  "created_at": "2024-06-09T12:40:00.000Z",
  "last_seen": null,
  "tags": [
    { "id": 1, "name": "core-network", "type": "location" }
  ],
  "matching_credentials_count": 1
}
```
**Frontend Notes:**
- If hostname or IP already exists, response is HTTP 400:
  ```json
  { "detail": "hostname already registered: core-switch-02" }
  ```
- Tags are optional; if omitted, the default tag is added.

---

#### `GET /devices/{device_id}` — Get device by ID
**Description:** Get a device by its ID.

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /devices/2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "id": 2,
  "hostname": "core-switch-02",
  "ip_address": "192.168.1.2",
  "device_type": "cisco_ios",
  "description": "Second core switch",
  "port": 22,
  "created_at": "2024-06-09T12:40:00.000Z",
  "last_seen": null,
  "tags": [
    { "id": 1, "name": "core-network", "type": "location" }
  ],
  "matching_credentials_count": 1
}
```
**Frontend Notes:**
- Use for device detail views or edit forms.
- If device not found, response is HTTP 404:
  ```json
  { "detail": "Device not found" }
  ```

---

#### `PUT /devices/{device_id}` — Update device
**Description:** Update an existing device.

**Authentication:** Bearer token required.

**Request Example:**
```json
{
  "description": "Updated description",
  "tags": [1, 2]
}
```
**Response Example:**
```json
{
  "id": 2,
  "hostname": "core-switch-02",
  "ip_address": "192.168.1.2",
  "device_type": "cisco_ios",
  "description": "Updated description",
  "port": 22,
  "created_at": "2024-06-09T12:40:00.000Z",
  "last_seen": null,
  "tags": [
    { "id": 1, "name": "core-network", "type": "location" },
    { "id": 2, "name": "datacenter", "type": "location" }
  ],
  "matching_credentials_count": 2
}
```
**Frontend Notes:**
- Only fields provided in the request are updated.
- If tags are set to null or empty, only the default tag is kept.
- If device not found, response is HTTP 404.

---

#### `DELETE /devices/{device_id}` — Delete device
**Description:** Delete a device by ID.

**Authentication:** Bearer token required.

**Request Example:**
```http
DELETE /devices/2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response:**
- HTTP 204 No Content (no body).

**Frontend Notes:**
- Use for device management delete actions.
- If device not found, response is HTTP 404:
  ```json
  { "detail": "Device not found" }
  ```

---

#### `GET /devices/{device_id}/credentials` — Get credentials for device
**Description:** Get all credentials that match the device's tags, ordered by priority.

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /devices/2/credentials HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "priority": 100,
    "description": "Admin credentials for core network devices",
    "is_system": false,
    "tags": [
      { "id": 1, "name": "core-network", "type": "location" }
    ]
  }
]
```
**Frontend Notes:**
- Use for credential selection in device detail views.
- Passwords are never returned in responses.
- If device not found, response is HTTP 404.

### Tags
#### `GET /tags/` — List tags
**Description:** List all tags with pagination and optional filtering.

**Authentication:** Bearer token required.

**Query Parameters:**
- `page` (int, default 1): Page number.
- `size` (int, default 20): Items per page.
- `name` (str, optional): Filter by partial tag name match.
- `type` (str, optional): Filter by tag type (exact match).

**Request Example:**
```http
GET /tags/?page=1&size=2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "items": [
    { "id": 1, "name": "core-network", "type": "location" },
    { "id": 2, "name": "datacenter", "type": "location" }
  ],
  "total": 2,
  "page": 1,
  "size": 2,
  "pages": 1
}
```
**Frontend Notes:**
- Use for tag management tables and tag selectors.

---

#### `POST /tags/` — Create tag
**Description:** Create a new tag.

**Authentication:** Bearer token required.

**Request Example:**
```json
{
  "name": "edge-router",
  "type": "role"
}
```
**Response Example:**
```json
{
  "id": 3,
  "name": "edge-router",
  "type": "role"
}
```
**Frontend Notes:**
- If tag name already exists, response is HTTP 400:
  ```json
  { "detail": "Tag name already exists" }
  ```

---

#### `GET /tags/{tag_id}` — Get tag by ID
**Description:** Get a tag by its ID.

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /tags/1 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "id": 1,
  "name": "core-network",
  "type": "location"
}
```
**Frontend Notes:**
- Use for tag detail views or edit forms.
- If tag not found, response is HTTP 404:
  ```json
  { "detail": "Tag not found" }
  ```

---

#### `PUT /tags/{tag_id}` — Update tag
**Description:** Update an existing tag.

**Authentication:** Bearer token required.

**Request Example:**
```json
{
  "name": "core-switch",
  "type": "role"
}
```
**Response Example:**
```json
{
  "id": 1,
  "name": "core-switch",
  "type": "role"
}
```
**Frontend Notes:**
- Only fields provided in the request are updated.
- If tag name already exists, response is HTTP 400.
- If tag not found, response is HTTP 404.

---

#### `DELETE /tags/{tag_id}` — Delete tag
**Description:** Delete a tag by ID.

**Authentication:** Bearer token required.

**Request Example:**
```http
DELETE /tags/1 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response:**
- HTTP 204 No Content (no body).

**Frontend Notes:**
- Use for tag management delete actions.
- If tag not found, response is HTTP 404:
  ```json
  { "detail": "Tag not found" }
  ```

### Credentials
#### `GET /credentials/` — List credentials
**Description:** List all credentials with pagination and optional filtering. Passwords are never returned.

**Authentication:** Bearer token required.

**Query Parameters:**
- `page` (int, default 1): Page number.
- `size` (int, default 20): Items per page.
- `username` (str, optional): Filter by partial username match.
- `priority` (int, optional): Filter by exact priority value.
- `tag_id` (list[int], optional): Filter by tag IDs (credentials with ANY of the specified tags).

**Request Example:**
```http
GET /credentials/?page=1&size=2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "items": [
    {
      "id": 1,
      "username": "admin",
      "priority": 100,
      "description": "Admin credentials for core network devices",
      "is_system": false,
      "tags": [
        { "id": 1, "name": "core-network", "type": "location" }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "size": 2,
  "pages": 1
}
```
**Frontend Notes:**
- Use for credential management tables.
- Passwords are never included in responses.

---

#### `POST /credentials/` — Create credential
**Description:** Create a new credential. Password is only sent in the request, never returned.

**Authentication:** Bearer token required.

**Request Example:**
```json
{
  "username": "admin",
  "password": "secureP@ssw0rd",
  "priority": 100,
  "description": "Admin credentials for core network devices",
  "tags": [1]
}
```
**Response Example:**
```json
{
  "id": 2,
  "username": "admin",
  "priority": 100,
  "description": "Admin credentials for core network devices",
  "is_system": false,
  "tags": [
    { "id": 1, "name": "core-network", "type": "location" }
  ]
}
```
**Frontend Notes:**
- Password is only sent in the request, never returned in the response.
- If tag IDs are invalid, response is HTTP 404:
  ```json
  { "detail": "Tag(s) not found: [99]" }
  ```

---

#### `GET /credentials/{credential_id}` — Get credential by ID
**Description:** Get a credential by its ID. Password is never returned.

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /credentials/2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "id": 2,
  "username": "admin",
  "priority": 100,
  "description": "Admin credentials for core network devices",
  "is_system": false,
  "tags": [
    { "id": 1, "name": "core-network", "type": "location" }
  ]
}
```
**Frontend Notes:**
- Use for credential detail views or edit forms.
- If credential not found, response is HTTP 404:
  ```json
  { "detail": "Credential not found" }
  ```

---

#### `PUT /credentials/{credential_id}` — Update credential
**Description:** Update an existing credential. Password can be updated by including it in the request.

**Authentication:** Bearer token required.

**Request Example:**
```json
{
  "priority": 200,
  "description": "Updated description"
}
```
**Response Example:**
```json
{
  "id": 2,
  "username": "admin",
  "priority": 200,
  "description": "Updated description",
  "is_system": false,
  "tags": [
    { "id": 1, "name": "core-network", "type": "location" }
  ]
}
```
**Frontend Notes:**
- Only fields provided in the request are updated.
- If credential not found, response is HTTP 404.

---

#### `DELETE /credentials/{credential_id}` — Delete credential
**Description:** Delete a credential by ID. System credentials cannot be deleted.

**Authentication:** Bearer token required.

**Request Example:**
```http
DELETE /credentials/2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response:**
- HTTP 204 No Content (no body).

**Frontend Notes:**
- Use for credential management delete actions.
- If credential not found, response is HTTP 404:
  ```json
  { "detail": "Credential not found" }
  ```
- If credential is a system credential, response is HTTP 403:
  ```json
  { "detail": "System credentials cannot be deleted" }
  ```

### Jobs
#### `GET /jobs/` — List jobs
**Description:** List all jobs with pagination and optional filtering.

**Authentication:** Bearer token required.

**Query Parameters:**
- `page` (int, default 1): Page number.
- `size` (int, default 20): Items per page.
- `name` (str, optional): Filter by partial job name match.
- `status` (str, optional): Filter by job status (e.g., "pending", "running").
- `is_enabled` (bool, optional): Filter by enabled/disabled state.
- `schedule_type` (str, optional): Filter by schedule type (interval, cron, onetime).
- `tag_id` (list[int], optional): Filter by tag IDs (jobs with ANY of the specified tags).

**Request Example:**
```http
GET /jobs/?page=1&size=2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Backup Core Routers Daily",
      "description": "Daily backup of all core routers at 2am",
      "is_enabled": true,
      "schedule_type": "cron",
      "interval_seconds": null,
      "cron_string": "0 2 * * *",
      "scheduled_for": null,
      "job_type": "backup",
      "status": "pending",
      "started_at": null,
      "completed_at": null,
      "tags": [
        { "id": 1, "name": "core-network", "type": "location" }
      ],
      "device_id": null,
      "is_system_job": false
    }
  ],
  "total": 1,
  "page": 1,
  "size": 2,
  "pages": 1
}
```
**Frontend Notes:**
- Use for job management tables.
- `tags` is a list of tag objects.
- `status` can be `pending`, `running`, `completed`, `failed`.

---

#### `POST /jobs/` — Create job
**Description:** Create a new job.

**Authentication:** Bearer token required.

**Request Example:**
```json
{
  "name": "Backup Core Routers Daily",
  "description": "Daily backup of all core routers at 2am",
  "is_enabled": true,
  "schedule_type": "cron",
  "cron_string": "0 2 * * *",
  "job_type": "backup",
  "tags": [1]
}
```
**Response Example:**
```json
{
  "id": 2,
  "name": "Backup Core Routers Daily",
  "description": "Daily backup of all core routers at 2am",
  "is_enabled": true,
  "schedule_type": "cron",
  "interval_seconds": null,
  "cron_string": "0 2 * * *",
  "scheduled_for": null,
  "job_type": "backup",
  "status": "pending",
  "started_at": null,
  "completed_at": null,
  "tags": [
    { "id": 1, "name": "core-network", "type": "location" }
  ],
  "device_id": null,
  "is_system_job": false
}
```
**Frontend Notes:**
- If job name already exists, response is HTTP 400:
  ```json
  { "detail": "Job name already exists" }
  ```
- Either `tags` or `device_id` must be provided (not both).

---

#### `GET /jobs/{job_id}` — Get job by ID
**Description:** Get a job by its ID.

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /jobs/2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "id": 2,
  "name": "Backup Core Routers Daily",
  "description": "Daily backup of all core routers at 2am",
  "is_enabled": true,
  "schedule_type": "cron",
  "interval_seconds": null,
  "cron_string": "0 2 * * *",
  "scheduled_for": null,
  "job_type": "backup",
  "status": "pending",
  "started_at": null,
  "completed_at": null,
  "tags": [
    { "id": 1, "name": "core-network", "type": "location" }
  ],
  "device_id": null,
  "is_system_job": false
}
```
**Frontend Notes:**
- Use for job detail views or edit forms.
- If job not found, response is HTTP 404:
  ```json
  { "detail": "Job not found" }
  ```

---

#### `PUT /jobs/{job_id}` — Update job
**Description:** Update an existing job.

**Authentication:** Bearer token required.

**Request Example:**
```json
{
  "description": "Updated description",
  "is_enabled": false
}
```
**Response Example:**
```json
{
  "id": 2,
  "name": "Backup Core Routers Daily",
  "description": "Updated description",
  "is_enabled": false,
  "schedule_type": "cron",
  "interval_seconds": null,
  "cron_string": "0 2 * * *",
  "scheduled_for": null,
  "job_type": "backup",
  "status": "pending",
  "started_at": null,
  "completed_at": null,
  "tags": [
    { "id": 1, "name": "core-network", "type": "location" }
  ],
  "device_id": null,
  "is_system_job": false
}
```
**Frontend Notes:**
- Only fields provided in the request are updated.
- If job not found, response is HTTP 404.
- System jobs cannot be updated (HTTP 403).

---

#### `DELETE /jobs/{job_id}` — Delete job
**Description:** Delete a job by ID. System jobs cannot be deleted.

**Authentication:** Bearer token (admin role required).

**Request Example:**
```http
DELETE /jobs/2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response:**
- HTTP 204 No Content (no body).

**Frontend Notes:**
- Use for job management delete actions.
- If job not found, response is HTTP 404:
  ```json
  { "detail": "Job not found" }
  ```
- If job is a system job, response is HTTP 403:
  ```json
  { "detail": "System jobs cannot be deleted." }
  ```

---

#### `POST /jobs/run/{job_id}` — Trigger job run
**Description:** Trigger immediate execution of a job. Returns immediately with acceptance message and queue info.

**Authentication:** Bearer token required.

**Request Example:**
```http
POST /jobs/run/2 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "message": "Job triggered successfully",
  "job_id": 2,
  "job_name": "Backup Core Routers Daily",
  "queue_job_id": "rq:job:1234567890abcdef"
}
```
**Frontend Notes:**
- Use for manual job execution from the UI.
- If job not found, response is HTTP 404.
- If Redis queue is unavailable, response is HTTP 503.

---

#### `GET /jobs/status` — Get job/queue/worker status
**Description:** Get status of Redis, RQ queues, and workers for dashboard cards. Does NOT include system-wide health.

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /jobs/status HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "redis_uptime": 12345,
  "redis_memory": 10485760,
  "redis_last_heartbeat": null,
  "rq_queues": [
    {
      "name": "default",
      "job_count": 1,
      "oldest_job_ts": "2024-06-09T14:00:00.000Z",
      "jobs": [
        {
          "job_id": "rq:job:1234567890abcdef",
          "enqueued_at": "2024-06-09T14:00:00.000Z",
          "func_name": "run_worker_job",
          "args": [2],
          "meta": {}
        }
      ]
    }
  ],
  "workers": [
    {
      "id": "worker-1",
      "status": "idle",
      "jobs_in_progress": 0
    }
  ]
}
```
**Frontend Notes:**
- Use for job/queue/worker dashboard widgets.
- `rq_queues` and `workers` are lists of objects with detailed status.

---

#### `GET /jobs/{job_id}/devices` — Get per-device job results

> **DEPRECATED**: This endpoint is deprecated and will be removed in a future release. Use `/job-results/?job_id=...` for canonical per-device job status. This endpoint currently returns per-device job logs (from the `logs` table, not `job_results`) and is maintained for legacy UI compatibility only.

**Description:** Get job results for each device targeted by a job.

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /jobs/2/devices HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
[
  {
    "device_id": 1,
    "device_name": "core-switch-01",
    "device_ip": "192.168.1.1",
    "log": {
      "id": 123,
      "timestamp": "2024-06-09T14:05:00.000Z",
      "log_type": "job",
      "level": "info",
      "job_id": 2,
      "device_id": 1,
      "source": "worker.executor",
      "message": "Job completed successfully",
      "meta": {}
    }
  }
]
```
**Frontend Notes:**
- Use for job result tables and device status displays.
- Each entry includes device info and the associated log.

---

#### `GET /jobs/scheduled` — List scheduled jobs
**Description:** List all enabled jobs with a schedule (interval/cron/onetime), including next run time.

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /jobs/scheduled HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
[
  {
    "id": 1,
    "name": "Backup Core Routers Daily",
    "job_type": "backup",
    "description": "Daily backup of all core routers at 2am",
    "schedule_type": "cron",
    "interval_seconds": null,
    "cron_string": "0 2 * * *",
    "scheduled_for": null,
    "next_run": "2024-06-10T02:00:00.000Z",
    "tags": [
      { "id": 1, "name": "core-network", "type": "location" }
    ],
    "is_enabled": true,
    "is_system_job": false
  }
]
```
**Frontend Notes:**
- Use for job scheduling dashboards and next-run indicators.
- `next_run` is the calculated next scheduled execution time.

# ---

## Job Results, Logs, and Per-Device Status: Canonical Sources and Redundancy

NetRaven stores per-device job status and logs in two places:
- **Job Results Table (`job_results`)**: Canonical, structured per-device job outcome (status, details, timestamps). Exposed via `/job-results/`.
- **Unified Logs Table (`logs`)**: Canonical, unstructured event log (job, connection, system, etc.). Exposed via `/logs/`.

### Endpoint Relationships
- `/job-results/`: Canonical for per-device job outcomes. Use for reporting, analytics, and device/job status dashboards.
- `/jobs/{job_id}/devices`: **DEPRECATED**. Use `/job-results/?job_id=...` for canonical per-device job status. This endpoint is maintained for legacy UI compatibility only and will be removed after migration.
- `/logs/`: Canonical for all log events, including job, connection, and system logs. Use for log tables, filtering, and streaming.
- `/job-logs/`: **REMOVED**. This endpoint is not implemented in the backend and should not be referenced in frontend or documentation. Use `/logs/` for all log/event queries.

### Data Flow Diagram

```
[Job Execution]
   ├─► [job_results] (per-device outcome)
   └─► [logs] (event log: job, connection, etc.)

[API Endpoints]
   ├─► /job-results/ (from job_results)
   ├─► /logs/ (from logs)
   └─► /jobs/{job_id}/devices (from logs, legacy)
```

### Migration Notes
- `/jobs/{job_id}/devices` is deprecated. All consumers should migrate to `/job-results/?job_id=...` for per-device job status.
- `/job-logs/` is not implemented and should be removed from all documentation and frontend code. Use `/logs/` for all log/event queries.
- **Canonical Data Sources:**
    - `/job-results/` is the only source for per-device job status.
    - `/logs/` is the canonical source for event/audit logs.

---

# Credentials, and Jobs will be documented next in the same detailed format. 