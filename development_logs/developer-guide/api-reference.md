# NetRaven API Reference

## Introduction

NetRaven provides a comprehensive REST API that allows developers to integrate with and extend the platform. This document provides detailed information about the available endpoints, authentication methods, and example requests and responses.

## Base URL

All API endpoints are relative to the base URL of your NetRaven installation:

```
http://your-netraven-server:8000/api
```

For example, the devices endpoint would be:

```
http://your-netraven-server:8000/api/devices
```

## Authentication

The API supports two authentication methods:

### JWT Authentication

For user-based access, use JWT token authentication:

1. Obtain a token by sending a POST request to `/api/auth/token` with your credentials
2. Include the token in the `Authorization` header of subsequent requests

Example:

```bash
# Obtain token
curl -X POST http://your-netraven-server:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password"

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

# Use token
curl -X GET http://your-netraven-server:8000/api/devices \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### API Key Authentication

For service-to-service communication, use API key authentication:

```bash
curl -X GET http://your-netraven-server:8000/api/health \
  -H "X-API-Key: your-api-key"
```

## API Endpoints

### Devices

#### List Devices

```
GET /api/devices
```

Returns a list of all devices.

**Parameters:**

| Name     | Type    | Description                         |
|----------|---------|-------------------------------------|
| limit    | integer | Maximum number of results (default: 100) |
| offset   | integer | Result offset for pagination (default: 0) |
| tag      | string  | Filter by tag name                  |

**Response:**

```json
[
  {
    "id": "f8e7d6c5-b4a3-2c1d-0e9f-8g7h6i5j4k3l",
    "hostname": "core-router-01",
    "ip_address": "192.168.1.1",
    "device_type": "cisco_ios",
    "description": "Core Router",
    "last_backup_at": "2023-05-15T08:30:00Z",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-05-15T08:30:00Z"
  },
  ...
]
```

#### Get Device

```
GET /api/devices/{device_id}
```

Returns details for a specific device.

**Parameters:**

| Name      | Type   | Description                         |
|-----------|--------|-------------------------------------|
| device_id | string | The ID of the device to retrieve    |

**Response:**

```json
{
  "id": "f8e7d6c5-b4a3-2c1d-0e9f-8g7h6i5j4k3l",
  "hostname": "core-router-01",
  "ip_address": "192.168.1.1",
  "device_type": "cisco_ios",
  "description": "Core Router",
  "last_backup_at": "2023-05-15T08:30:00Z",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-05-15T08:30:00Z",
  "tags": [
    {
      "id": "a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6",
      "name": "core",
      "color": "#FF5733"
    }
  ]
}
```

#### Create Device

```
POST /api/devices
```

Creates a new device.

**Request Body:**

```json
{
  "hostname": "core-router-01",
  "ip_address": "192.168.1.1",
  "device_type": "cisco_ios",
  "description": "Core Router",
  "username": "admin",
  "password": "password"
}
```

**Response:**

```json
{
  "id": "f8e7d6c5-b4a3-2c1d-0e9f-8g7h6i5j4k3l",
  "hostname": "core-router-01",
  "ip_address": "192.168.1.1",
  "device_type": "cisco_ios",
  "description": "Core Router",
  "created_at": "2023-05-15T08:30:00Z",
  "updated_at": "2023-05-15T08:30:00Z"
}
```

## API Client Libraries

NetRaven provides client libraries for common programming languages to simplify API integration:

- [Python Client](https://github.com/yourusername/netraven-python-client)
- [JavaScript Client](https://github.com/yourusername/netraven-js-client)

## Error Handling

The API uses standard HTTP status codes to indicate success or failure:

- 200: Success
- 201: Resource created
- 400: Bad request
- 401: Unauthorized
- 403: Forbidden
- 404: Resource not found
- 500: Server error

Error responses include a JSON body with details:

```json
{
  "detail": "Error message describing the issue"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. The current limits are:

- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated requests

Rate limit headers are included in all responses:

- `X-RateLimit-Limit`: Total requests allowed in the period
- `X-RateLimit-Remaining`: Requests remaining in the period
- `X-RateLimit-Reset`: Time when the rate limit will reset (Unix timestamp)

## Pagination

List endpoints support pagination with the following parameters:

- `limit`: Maximum number of results (default: 100, max: 1000)
- `offset`: Result offset for pagination (default: 0)

Pagination metadata is included in the response headers:

- `X-Total-Count`: Total number of results
- `X-Page-Count`: Total number of pages
- `X-Page`: Current page number
- `X-Per-Page`: Number of results per page

## Related Documentation

- [API Standardization](./api-standardization.md)
- [Authentication](../admin-guide/security.md)
- [Development Workflow](./development-workflow.md) 