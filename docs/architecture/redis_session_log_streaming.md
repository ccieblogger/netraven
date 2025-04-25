# NetRaven Redis Session Log Streaming Specification

## Overview
NetRaven uses Redis Pub/Sub to enable real-time streaming of high-volume session logs (e.g., per-command output) for live troubleshooting and monitoring in the UI. This system complements the unified log table by providing immediate log delivery to interested consumers (such as the web UI) while ensuring all logs are persisted for audit and history.

---

## Channel Structure
- **Channel Name Format:**
  - `session-logs:{job_id}`
  - Example: `session-logs:12345`
- Each job/session has its own dedicated Redis channel for log streaming.

## Message Format
- **Type:** JSON-encoded string
- **Fields:**
  - `timestamp` (ISO8601, UTC)
  - `log_type` (e.g., 'session', 'job', etc.)
  - `level` (e.g., 'info', 'error', 'debug')
  - `job_id` (int)
  - `device_id` (int, optional)
  - `source` (string, e.g., 'worker.executor')
  - `message` (string)
  - `meta` (object, optional)
- **Example:**
```json
{
  "timestamp": "2025-04-25T23:00:00Z",
  "log_type": "session",
  "level": "info",
  "job_id": 12345,
  "device_id": 678,
  "source": "worker.executor",
  "message": "show running-config output...",
  "meta": {"command": "show running-config"}
}
```

## Publishing Logic
- The backend logger publishes each session log event to the appropriate Redis channel using:
  - `redis_client.publish(f"session-logs:{job_id}", json.dumps(log_record))`
- All session logs are also persisted to the unified log table in PostgreSQL.

## Integration Points
- **Backend:**
  - UnifiedLogger (or equivalent) is responsible for dual-write to DB and Redis.
  - Session logs are published in real-time as they are generated.
- **UI/Frontend:**
  - Subscribes to the relevant Redis channel (via backend SSE/WebSocket endpoint) to receive live log updates.
  - Displays logs in real-time for active jobs/sessions.

## Security & Performance
- Redis is deployed locally and not exposed externally.
- Only backend services publish to Redis; clients subscribe via backend API (not directly to Redis).
- High-volume logs are supported; consumers should be prepared for bursty traffic.

## Future Enhancements
- Support for additional log types or multi-job channels.
- Retention or replay of recent messages (if needed). 