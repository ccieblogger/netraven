# Unified Logger Reference Architecture & Usage Guide

## 1. Overview
The `UnifiedLogger` utility provides a centralized, configurable, and robust logging solution for the NetRaven platform. It supports logging to multiple destinations (file, stdout, Redis, and database) with per-call and config-driven control, ensuring auditability, real-time monitoring, and operational resilience.

**Key Features:**
- Config-driven, multi-destination logging
- File logging with rotation and format options
- Real-time Redis log streaming
- Database logging for job and connection logs
- Robust error handling and fallback
- Thread/process safety

---

## 2. System Architecture Diagram
```
                ┌──────────────┐
                │  NetRaven    │
                │  Components  │
                └──────┬───────┘
                       │
                       ▼
              ┌────────────────────┐
              │  UnifiedLogger     │
              └─────┬─────┬──┬────┘
                    │     │  │
        ┌───────────┘     │  └────────────┐
        ▼                 ▼               ▼
   [File Logger]   [Stdout Logger]   [Redis Logger]
        │                 │               │
        ▼                 ▼               ▼
   /data/logs/      Console/Stdout   Redis Channel
        │                                 │
        ▼                                 ▼
   [Log Rotation]                  [Real-time UI]

        └─────────────┬─────────────┘
                      ▼
                [DB Logger]
                      │
                      ▼
                PostgreSQL
```

---

## 3. Configuration

**Example YAML:**
```yaml
logging:
  file:
    enabled: true
    path: /data/logs/netraven.log
    level: INFO
    format: json
    rotation:
      when: midnight
      interval: 1
      backupCount: 7
  redis:
    enabled: true
    host: redis           # Docker Compose service name for Redis
    port: 6379
    db: 0
    password: null        # Set if your Redis requires a password
    channel_prefix: netraven-logs
  stdout:
    enabled: true
  db:
    enabled: true
```

**Environment Variable Overrides:**
```
NETRAVEN_LOGGING__FILE__ENABLED=true
NETRAVEN_LOGGING__FILE__PATH=/data/logs/netraven.log
NETRAVEN_LOGGING__FILE__LEVEL=INFO
NETRAVEN_LOGGING__FILE__FORMAT=json
NETRAVEN_LOGGING__FILE__ROTATION__WHEN=midnight
NETRAVEN_LOGGING__FILE__ROTATION__INTERVAL=1
NETRAVEN_LOGGING__FILE__ROTATION__BACKUPCOUNT=7
NETRAVEN_LOGGING__REDIS__ENABLED=true
NETRAVEN_LOGGING__REDIS__HOST=redis
NETRAVEN_LOGGING__REDIS__PORT=6379
NETRAVEN_LOGGING__REDIS__DB=0
NETRAVEN_LOGGING__REDIS__PASSWORD=yourpassword
NETRAVEN_LOGGING__REDIS__CHANNEL_PREFIX=netraven-logs
NETRAVEN_LOGGING__STDOUT__ENABLED=true
NETRAVEN_LOGGING__DB__ENABLED=true
```

**Config Options:**
- `file.enabled`: Enable/disable file logging
- `file.path`: Log file path (ensure directory is writable/mounted)
- `file.level`: Log level (DEBUG, INFO, etc.)
- `file.format`: `json` or `plain`
- `file.rotation`: Rotation policy (see Python logging docs)
- `redis.enabled`: Enable/disable Redis logging
- `redis.host`: Hostname of the Redis container (use `redis` for Docker Compose)
- `redis.port`: Redis port (default: 6379)
- `redis.db`: Redis database number (default: 0)
- `redis.password`: Password if required (default: null)
- `redis.channel_prefix`: Redis channel for log streaming
- `stdout.enabled`: Enable/disable stdout logging
- `db.enabled`: Enable/disable DB logging

---

## 4. Usage Patterns

**Import and Use the Global Logger:**
```python
from netraven.utils.unified_logger import get_unified_logger
logger = get_unified_logger()
logger.log("Backup started", level="INFO", job_id=42, device_id=7)
```

**Log to Specific Destinations:**
```python
logger.log("Critical error", level="CRITICAL", destinations=["file", "db"])
```

**Log with Context:**
```python
logger.log("Device unreachable", level="ERROR", job_id=42, device_id=7, source="worker.executor")
```

---

## 5. Integration Examples

**Replace Legacy Logging:**
- Remove direct `logging` or `structlog` calls
- Replace with `logger.log()` calls, passing context as needed

**Best Practices:**
- Always include `job_id` and `device_id` if available
- Use appropriate log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- Prefer config-driven destination selection; override per-call only for special cases

---

## 6. Error Handling & Fallbacks
- If a destination fails (e.g., Redis down), logger prints a warning and falls back to stdout
- Logging errors never crash the application
- All errors are visible in the logs or console for troubleshooting

---

## 7. Testing & Validation
- Tests are located in `tests/utils/test_unified_logger.py`
- To run tests in the container:
  ```bash
  docker exec -it netraven-api-dev bash -c "cd /app && PYTHONPATH=/app poetry run pytest tests/utils/"
  ```
- All destinations, error handling, and config options are covered by tests

---

## 8. Extending the Logger
- To add a new destination:
  - Add a handler method to `UnifiedLogger`
  - Update config parsing and the `log()` method
  - Add tests for the new destination
- Follow existing patterns for error handling and metadata

---

## 9. Troubleshooting
- **File not written:** Check file path, permissions, and Docker volume mounts
- **Redis errors:** Ensure Redis is running and accessible
- **DB errors:** Check DB connectivity and schema
- **No logs:** Check config and environment variable overrides

---

## 10. Reference & API Documentation

**UnifiedLogger Public Methods:**
- `log(message, level="INFO", destinations=None, job_id=None, device_id=None, extra=None, source=None, **kwargs)`
  - Log a message to one or more destinations with context
- `get_unified_logger()`
  - Returns the global logger instance

**Example Log Record Structure:**
```json
{
  "timestamp": "2025-04-24T03:00:00Z",
  "level": "INFO",
  "message": "Backup started",
  "job_id": 42,
  "device_id": 7,
  "source": "worker.executor",
  "extra": {}
}
```

---

For further questions, see the development log or contact the NetRaven maintainers. 