# NetRaven Log Query & Filtering REST API Specification

## Overview
NetRaven provides a robust REST API for querying and filtering logs stored in the unified log table. The API supports flexible filters, pagination, and metadata endpoints, enabling both UI and external integrations to retrieve and analyze log data efficiently.

---

## Authentication
- All endpoints require JWT authentication (Bearer token in the `Authorization` header).
- Role-based access enforced for sensitive log data.

## Endpoints

### 1. List Logs
- **Path:** `/logs/`
- **Method:** `GET`
- **Query Parameters:**
  - `log_type` (str, optional)
  - `level` (str, optional)
  - `job_id` (int, optional)
  - `device_id` (int, optional)
  - `source` (str, optional)
  - `start_time` (datetime, optional, ISO8601)
  - `end_time` (datetime, optional, ISO8601)
  - `search` (str, optional, full-text search)
  - `job_type` (str, optional)
  - `page` (int, default=1)
  - `size` (int, default=20, max=100)
  - `order` (str, 'asc' or 'desc', default='desc')
- **Response:**
  - `items`: List of log entries
  - `total`: Total matching logs
  - `page`, `size`, `pages`: Pagination info

### 2. Get Single Log
- **Path:** `/logs/{log_id}`
- **Method:** `GET`
- **Response:** Log entry object

### 3. Log Types
- **Path:** `/logs/types`
- **Method:** `GET`
- **Response:** List of available log types

### 4. Log Levels
- **Path:** `/logs/levels`
- **Method:** `GET`
- **Response:** List of available log levels

### 5. Log Stats
- **Path:** `/logs/stats`
- **Method:** `GET`
- **Response:** Log statistics (total, by type, by level, last log time)

### 6. Real-Time Log Streaming
- **Path:** `/logs/stream`
- **Method:** `GET` (SSE)
- **Query Parameters:**
  - `job_id` (int, optional)
  - `device_id` (int, optional)
- **Response:** Server-Sent Events (SSE) stream of log events and keep-alive heartbeats

---

## Usage Examples

### List Logs (Filtered)
```http
GET /logs/?job_id=123&level=error&page=1&size=10 HTTP/1.1
Authorization: Bearer <token>
```

### Get Single Log
```http
GET /logs/456 HTTP/1.1
Authorization: Bearer <token>
```

### Stream Logs (SSE)
```http
GET /logs/stream?job_id=123 HTTP/1.1
Accept: text/event-stream
Authorization: Bearer <token>
```

---

## Response Structure
- Log entries include:
  - `id`, `timestamp`, `log_type`, `level`, `job_id`, `device_id`, `source`, `message`, `meta`
- SSE events:
  - `event: log` with `data: <log JSON>`
  - `: keepalive` comments every 15s

## OpenAPI Documentation
- All endpoints are documented in the OpenAPI schema (Swagger UI at `/docs`).
- Example requests and responses are available in the API docs.

## Security & Performance
- JWT required for all endpoints.
- Pagination and filtering recommended for large queries.
- SSE endpoint supports high-frequency log streaming with keep-alive. 