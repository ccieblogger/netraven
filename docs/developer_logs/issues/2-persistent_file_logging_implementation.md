# Persistent File Logging Implementation Plan for NetRaven

## Background

By default, NetRaven logs are written to stdout/stderr, which are captured by Docker and accessible via `docker logs`. For production and troubleshooting, it is often desirable to persist logs to a file on a mounted volume, making them accessible outside the container and ensuring they survive container restarts.

This document outlines the steps to implement optional persistent file logging in NetRaven, configurable via environment variables or YAML config, and suitable for containerized deployments.

---

## Requirements

- **Python logging** must support writing to both stdout and a file (if configured).
- **Log file path** should be configurable via environment variable and/or YAML config.
- **Docker containers** must be able to write logs to a mounted host volume.
- **Default behavior** should remain logging to stdout only unless file logging is explicitly enabled.
- **No breaking changes** to existing logging or deployment workflows.

---

## Implementation Steps

### 1. Update Configuration

- Add a `file` option to the `logging` section in environment YAMLs (e.g., `config/environments/dev.yaml`, `prod.yaml`).
- Support overriding this via the `NETRAVEN_LOGGING__FILE` environment variable.

**Example YAML:**
```yaml
logging:
  level: INFO
  file: "/var/log/netraven/worker.log"  # Set to null or remove to disable file logging
```

### 2. Update Logging Setup in Code

- Refactor the logging setup in main entry points (e.g., `runner.py`, `dispatcher.py`) or centralize in a utility (recommended).
- Read the log file path from config/env.
- If set, add a `FileHandler` to the logger in addition to the default `StreamHandler` (stdout).

**Example Python Snippet:**
```python
import logging
import os
from netraven.config.loader import load_config

config = load_config()
log_level = config.get('logging', {}).get('level', 'INFO')
log_file = config.get('logging', {}).get('file') or os.getenv('NETRAVEN_LOGGING__FILE')

handlers = [logging.StreamHandler()]
if log_file:
    handlers.append(logging.FileHandler(log_file, mode='a'))

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)
log = logging.getLogger(__name__)
```

- **Tip:** Centralize this logic in a `log_utils.py` function (e.g., `setup_logging()`) and call it from all main modules.

### 3. Update Docker Compose or Deployment

- Mount a host directory as a volume in the container for log persistence.
- Set the log file path via environment variable or config.

**Example Docker Compose Service:**
```yaml
services:
  netraven-worker:
    image: netraven/worker:latest
    volumes:
      - ./host-logs/netraven:/var/log/netraven
    environment:
      - NETRAVEN_LOGGING__FILE=/var/log/netraven/worker.log
```

- Ensure the container user has write permissions to the mounted directory.

### 4. Documentation

- Document the new logging options in the developer and deployment docs.
- Provide examples for enabling/disabling file logging and for mounting volumes.

### 5. Testing & Validation

- **Unit Test:** Start the service with and without the file logging option. Confirm logs appear in both stdout and the file when enabled.
- **Integration Test:** Deploy with Docker Compose, mount a host volume, and verify logs are written to the host.
- **Permissions Test:** Ensure the container can write to the mounted directory.
- **Fallback Test:** Confirm that if the file path is invalid or unwritable, the service still logs to stdout and emits a warning.

### 6. Rollback Instructions

- To disable file logging, remove the `file` entry from the config or unset the `NETRAVEN_LOGGING__FILE` environment variable.
- Remove or comment out the volume mount in Docker Compose to revert to stdout-only logging.
- No code rollback is needed if the implementation is non-breaking.

---

## Example: Enabling File Logging in Development

1. Create a directory on your host for logs:
   ```bash
   mkdir -p ./host-logs/netraven
   chmod 777 ./host-logs/netraven  # Or set appropriate permissions
   ```
2. Update your `docker-compose.yaml` as shown above.
3. Set the environment variable or config option for the log file path.
4. Start the container and verify logs are written to both stdout and `./host-logs/netraven/worker.log` on the host.

---

## Notes & Best Practices

- **Log Rotation:** Consider using a log rotation tool (e.g., `logrotate`) on the host to manage file size.
- **Security:** Ensure log files do not contain sensitive information, or restrict access to the log directory.
- **Centralization:** For production, consider shipping logs to a central log aggregator (e.g., ELK, Loki, etc.) using a sidecar or host agent.

---

## References
- [Python logging documentation](https://docs.python.org/3/library/logging.html)
- [Docker volumes documentation](https://docs.docker.com/storage/volumes/)
- [Docker Compose environment variables](https://docs.docker.com/compose/environment-variables/) 