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
- **Config Snapshots**

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

---

## Config Snapshots API (`/configs`)

### `GET /configs/search` — Full-text search device configurations
**Description:** Search device configuration snapshots using a query string. Returns a list of matching snapshots with metadata and highlighted snippets.

**Authentication:** Bearer token required.

**Query Parameters:**
- `q` (str, required): Search query for configuration text

**Request Example:**
```http
GET /configs/search?q=interface HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
[
  {
    "id": 101,
    "device_id": 2,
    "retrieved_at": "2024-06-09T12:34:56.789Z",
    "snippet": "...interface GigabitEthernet0/1...",
    "config_metadata": {"hostname": "core-switch-02"}
  }
]
```

---

### `GET /configs/{device_id}/history` — Get version history for a device
**Description:** List all configuration snapshots for a device, ordered by retrieval time (descending).

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /configs/2/history HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
[
  {
    "id": 101,
    "device_id": 2,
    "retrieved_at": "2024-06-09T12:34:56.789Z",
    "config_metadata": {"hostname": "core-switch-02"}
  }
]
```

---

### `GET /configs/{config_id}` — Get a specific config snapshot by ID
**Description:** Retrieve a specific configuration snapshot (raw config and metadata).

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /configs/101 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "id": 101,
  "device_id": 2,
  "retrieved_at": "2024-06-09T12:34:56.789Z",
  "config_metadata": {"hostname": "core-switch-02"},
  "config_data": "interface GigabitEthernet0/1\n description Uplink\n ..."
}
```

---

### `GET /configs/diff` — Get unified diff between two config snapshots
**Description:** Return a unified diff between two config snapshots' config_data fields.

**Authentication:** Bearer token required.

**Query Parameters:**
- `config_id_a` (int, required): ID of the first config snapshot
- `config_id_b` (int, required): ID of the second config snapshot

**Request Example:**
```http
GET /configs/diff?config_id_a=101&config_id_b=102 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "config_id_a": 101,
  "config_id_b": 102,
  "diff": [
    "--- config_101",
    "+++ config_102",
    "@@ -1,3 +1,3 @@",
    "-interface GigabitEthernet0/1",
    "+interface GigabitEthernet0/2"
  ]
}
```

---

### `GET /configs/list` and `GET /configs` — List all config snapshots
**Description:** List all configuration snapshots, optionally filtered by device_id, paginated.

**Authentication:** Bearer token required.

**Query Parameters:**
- `device_id` (int, optional): Filter by device ID
- `start` (int, default 0): Offset for pagination
- `limit` (int, default 50): Max results to return

**Request Example:**
```http
GET /configs/list?device_id=2&start=0&limit=10 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
[
  {
    "id": 101,
    "device_id": 2,
    "retrieved_at": "2024-06-09T12:34:56.789Z",
    "config_metadata": {"hostname": "core-switch-02"}
  }
]
```

---

### `DELETE /configs/{config_id}` — Delete a config snapshot by ID
**Description:** Delete a specific configuration snapshot by ID.

**Authentication:** Bearer token required.

**Request Example:**
```http
DELETE /configs/101 HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{ "deleted_id": 101 }
```

---

### `POST /configs/{config_id}/restore` — Restore a config snapshot (mark as restored)
**Description:** Mark a config as restored (optionally, create a new snapshot or update device state). For now, just logs/returns the action.

**Authentication:** Bearer token required.

**Request Example:**
```http
POST /configs/101/restore HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{
  "restored_id": 101,
  "device_id": 2,
  "restored_at": "2024-06-09T12:34:56.789Z",
  "message": "Config marked as restored (no device push performed)"
}
```

---

## Backups API (`/api/backups`)

### `GET /api/backups/count` — Get the count of backup configuration files
**Description:** Retrieve the total number of backup configuration files.

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /api/backups/count HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
{ "count": 123 }
```

---

## Scheduler API (`/scheduler`)

### `GET /scheduler/jobs` — List all jobs currently scheduled in RQ Scheduler
**Description:** List all jobs currently scheduled in RQ Scheduler.

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /scheduler/jobs HTTP/1.1
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
    "scheduled_for": "2024-06-10T02:00:00.000Z",
    "next_run": "2024-06-10T02:00:00.000Z",
    "repeat": null,
    "args": [],
    "meta": {},
    "tags": [],
    "is_enabled": true,
    "is_system_job": false
  }
]
```

---

### `GET /scheduler/queue/status` — Show queue length and details of jobs currently in the queue
**Description:** Show queue length and details of jobs currently in the queue.

**Authentication:** Bearer token required.

**Request Example:**
```http
GET /scheduler/queue/status HTTP/1.1
Authorization: Bearer <access_token>
```
**Response Example:**
```json
[
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
]
```

---

## Notes on `/configs` Prefix Usage
- Endpoints for configs and backups use the `/configs` prefix (e.g., `/configs`, `/backups`).
- Most other endpoints (users, devices, jobs, tags, credentials, logs, scheduler, job-results) do **not** use the `/configs` prefix and are mounted at the root.
- This is due to legacy and migration reasons. The frontend should use the documented paths as shown above.
