# NetRaven API Documentation

This document provides information about the NetRaven API endpoints, authentication methods, and usage examples.

## Authentication

NetRaven supports two authentication methods:

### 1. JWT Token Authentication

For user-based authentication, NetRaven uses JWT (JSON Web Token) authentication.

To obtain a token:

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=NetRaven"
```

Use the token in subsequent requests:

```bash
curl -X GET http://localhost:8000/api/devices \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 2. API Key Authentication

For service-to-service communication, NetRaven supports API key authentication.

Use the API key in the `X-API-Key` header:

```bash
curl -X GET http://localhost:8000/api/health \
  -H "X-API-Key: netraven-api-key"
```

The default API key is `netraven-api-key`, which can be changed in the configuration or by setting the `NETRAVEN_API_KEY` environment variable.

## API Endpoints

### Health Check

```
GET /api/health
```

Returns the health status of the API.

**Example Response:**
```json
{
  "status": "ok"
}
```

### Devices

#### List Devices

```
GET /api/devices
```

Returns a list of all devices.

**Authentication Required:** Yes (JWT Token or API Key)

**Example Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "hostname": "router1.example.com",
    "ip_address": "192.168.1.1",
    "device_type": "cisco_ios",
    "description": "Main Router",
    "is_reachable": true,
    "last_backup": "2025-03-15T14:30:00Z"
  }
]
```

#### Get Device Details

```
GET /api/devices/{device_id}
```

Returns details for a specific device.

**Authentication Required:** Yes (JWT Token or API Key)

#### Create Device

```
POST /api/devices
```

Creates a new device.

**Authentication Required:** Yes (JWT Token or API Key)

**Request Body:**
```json
{
  "hostname": "switch1.example.com",
  "ip_address": "192.168.1.2",
  "device_type": "cisco_ios",
  "description": "Main Switch",
  "port": 22,
  "username": "admin",
  "password": "password123"
}
```

### Backups

#### List Backups

```
GET /api/backups
```

Returns a list of all backups.

**Authentication Required:** Yes (JWT Token or API Key)

#### Get Backup Details

```
GET /api/backups/{backup_id}
```

Returns details for a specific backup.

**Authentication Required:** Yes (JWT Token or API Key)

#### Create Backup

```
POST /api/backups
```

Creates a new backup.

**Authentication Required:** Yes (JWT Token or API Key)

### Job Logs

#### List Job Logs

```
GET /api/job-logs
```

Returns a list of job logs with optional filtering.

**Authentication Required:** Yes (JWT Token or API Key)

**Query Parameters:**
- `device_id`: Filter by device ID
- `job_type`: Filter by job type
- `status`: Filter by status
- `start_time_from`: Filter by start time (from)
- `start_time_to`: Filter by start time (to)
- `session_id`: Filter by session ID
- `limit`: Maximum number of logs to return (default: 10)
- `offset`: Number of logs to skip (default: 0)

#### Get Job Log Details

```
GET /api/job-logs/{job_log_id}
```

Returns details for a specific job log.

**Authentication Required:** Yes (JWT Token or API Key)

#### Get Job Log Entries

```
GET /api/job-logs/{job_log_id}/entries
```

Returns entries for a specific job log.

**Authentication Required:** Yes (JWT Token or API Key)

**Query Parameters:**
- `level`: Filter by log level
- `category`: Filter by category
- `limit`: Maximum number of entries to return (default: 100)
- `offset`: Number of entries to skip (default: 0)

### Gateway

#### Get Gateway Status

```
GET /api/gateway/status
```

Returns the status of the device gateway service.

**Authentication Required:** Yes (JWT Token or API Key)

**Example Response:**
```json
{
  "status": "online",
  "version": "1.0.0",
  "uptime": "3d 2h 15m",
  "connected_devices": 5,
  "message": "Gateway is running normally"
}
```

## Recent Changes

### March 2025 Updates

1. **API Key Authentication**
   - Added support for API key authentication using the `X-API-Key` header
   - Implemented in all API endpoints for service-to-service communication

2. **Database Schema Improvements**
   - Updated the `job_data` column in the `job_logs` table to use JSONB for better performance
   - Improved error handling in database operations

3. **CORS Configuration**
   - Enhanced CORS configuration to support additional origins
   - Added `X-API-Key` to exposed headers

4. **Error Handling**
   - Improved error handling with detailed error messages
   - Added comprehensive logging for better diagnostics

## Error Handling

All API endpoints return standard HTTP status codes:

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `204 No Content`: Request succeeded with no response body
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a JSON body with details:

```json
{
  "detail": "Error message describing the issue"
}
``` 