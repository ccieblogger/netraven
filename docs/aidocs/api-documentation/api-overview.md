# NetRaven API Overview

## Introduction

The NetRaven API serves as the central communication layer for the platform, enabling interaction between the frontend, scheduler, gateway, and other components. It is built using **FastAPI**, a modern, fast (high-performance) web framework for building APIs with Python.

This document provides an overview of the API's structure, key endpoints, and authentication mechanisms to help developers and integrators quickly understand and utilize the API.

---

## Key Features

- **RESTful Design**: The API follows REST principles for simplicity and scalability.
- **Authentication**: Token-based authentication using JWT.
- **Modular Endpoints**: Organized by functionality (e.g., devices, jobs, configurations).
- **Asynchronous**: Built with asynchronous capabilities for high performance.
- **Extensibility**: Designed to support future features like HTTP/REST job execution.

---

## Authentication

The API uses **JWT (JSON Web Tokens)** for authentication. Clients must include a valid token in the `Authorization` header of each request:

```
Authorization: Bearer <your_token>
```

### Token Endpoints:
- **Login**: `/auth/login` - Obtain a JWT token.
- **Refresh Token**: `/auth/refresh` - Refresh an expired token.

#### Example: Obtaining an API Token

When running NetRaven in Docker, you can obtain a token using:

```bash
docker exec -it netraven-api-1 curl -L -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"NetRaven"}'
```

To store the token for subsequent API calls:

```bash
TOKEN=$(docker exec -it netraven-api-1 curl -L -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"NetRaven"}' | jq -r .access_token)

# Use the token for authenticated requests
docker exec -it netraven-api-1 curl -L -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/devices
```

Use the `access_token` in the `Authorization` header for subsequent API requests.

---

## Core Endpoints

### Devices
- **GET** `/api/devices` - List all devices.
- **POST** `/api/devices` - Add a new device.
- **PUT** `/api/devices/{id}` - Update an existing device.
- **DELETE** `/api/devices/{id}` - Remove a device.

### Jobs
- **GET** `/api/job-logs` - List all job logs.
- **POST** `/api/scheduled-jobs` - Create a new scheduled job.
- **GET** `/api/job-logs/{id}` - Get details of a specific job log.
- **DELETE** `/api/job-logs/{id}` - Delete a job log.

### Backups
- **GET** `/api/backups` - Retrieve configuration backups.
- **POST** `/api/backups` - Trigger a configuration backup.

### Users
- **GET** `/api/users` - List all users.
- **POST** `/api/users` - Create a new user.
- **GET** `/api/users/{id}` - Get user details.

### Tags
- **GET** `/api/tags` - List all tags.
- **POST** `/api/tags` - Create a new tag.

### Credentials
- **GET** `/api/credentials` - List all credentials.
- **POST** `/api/credentials` - Create a new credential.

---

## Error Handling

The API uses standard HTTP status codes to indicate success or failure:
- `200 OK` - Request succeeded.
- `201 Created` - Resource successfully created.
- `400 Bad Request` - Invalid request data.
- `401 Unauthorized` - Authentication failed or token expired.
- `404 Not Found` - Resource not found.
- `500 Internal Server Error` - Server encountered an error.

---

## Rate Limiting

To ensure fair usage, the API enforces rate limits:
- **Default**: 100 requests per minute per client.
- **Burst**: Up to 200 requests in a short burst.

---

## Documentation and Testing

The API includes interactive documentation powered by **Swagger UI** and **ReDoc**:
- **Swagger UI**: Accessible at `/docs`.
- **ReDoc**: Accessible at `/redoc`.

These tools allow developers to explore and test API endpoints directly from the browser.

---

## Testing API Endpoints

This section provides examples of how to test each API endpoint using **curl** with Docker. The examples assume you've stored your token in the `TOKEN` variable as shown in the Authentication section.

### Devices

#### List All Devices
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X GET http://localhost:8000/api/devices \
    -H "Authorization: Bearer $TOKEN"
  ```

#### Add a New Device
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X POST http://localhost:8000/api/devices \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "Device1", "ip_address": "192.168.1.1", "device_type": "cisco_ios"}'
  ```

#### Update an Existing Device
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X PUT http://localhost:8000/api/devices/1 \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "UpdatedDevice", "ip_address": "192.168.1.2"}'
  ```

#### Delete a Device
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X DELETE http://localhost:8000/api/devices/1 \
    -H "Authorization: Bearer $TOKEN"
  ```

### Jobs

#### List All Job Logs
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X GET http://localhost:8000/api/job-logs \
    -H "Authorization: Bearer $TOKEN"
  ```

#### Create a New Scheduled Job
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X POST http://localhost:8000/api/scheduled-jobs \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "Daily Backup", "schedule": "0 0 * * *", "job_type": "device_backup", "target_ids": ["1"], "enabled": true}'
  ```

#### Get Job Log Details
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X GET http://localhost:8000/api/job-logs/1 \
    -H "Authorization: Bearer $TOKEN"
  ```

#### Delete a Job Log
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X DELETE http://localhost:8000/api/job-logs/1 \
    -H "Authorization: Bearer $TOKEN"
  ```

### Backups

#### Retrieve Configuration Backups
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X GET http://localhost:8000/api/backups \
    -H "Authorization: Bearer $TOKEN"
  ```

#### Trigger a Configuration Backup
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X POST http://localhost:8000/api/devices/1/backup \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{}'
  ```

### Users

#### List All Users
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X GET http://localhost:8000/api/users \
    -H "Authorization: Bearer $TOKEN"
  ```

#### Get Current User
- **curl**:
  ```
  docker exec -it netraven-api-1 curl -L -X GET http://localhost:8000/api/users/me \
    -H "Authorization: Bearer $TOKEN"
  ```

---

## Future Enhancements

- **HTTP/REST Job Execution**: Support for executing HTTP/REST-based jobs.
- **Webhooks**: Event-driven notifications for job status updates.
- **GraphQL Support**: Optional GraphQL endpoints for advanced querying.

---

## Getting Started

1. Obtain an API token by logging in via `/auth/login`.
2. Use the token to authenticate requests to other endpoints.
3. Refer to the interactive documentation at `/docs` for detailed endpoint specifications.

For more details, see the [Architecture Documentation](../architecture/architecture-overview.md).