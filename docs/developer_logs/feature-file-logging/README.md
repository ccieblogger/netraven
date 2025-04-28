# Developer Log: Feature - File-Based Logging for API and Worker Containers

## Summary
This log documents the implementation of persistent file-based logging for the NetRaven API and worker containers. Logs are now written to a local host volume, with one log file per service, configurable via YAML.

## Changes Made

### Docker Compose
- Added volume mounts for:
  - `./host-logs/netraven/api:/data/logs/api` (API container)
  - `./host-logs/netraven/worker:/data/logs/worker` (Worker container)
- No changes for DB container, as DB logs are handled by Postgres or not required for app-level logging.

### Logging Configuration
- Updated `netraven/config/environments/dev.yaml` and `prod.yaml`:
  - Enabled file logging under the `logging.file` section.
  - Set default path to `/data/logs/api/api.log` (API) and noted override for worker as `/data/logs/worker/worker.log`.
  - Log rotation, format, and level are configurable.

### Host Directory Setup
- Host directories must be created before starting containers:
  ```bash
  mkdir -p ./host-logs/netraven/api
  mkdir -p ./host-logs/netraven/worker
  chmod -R 777 ./host-logs/netraven
  ```

## Validation Steps
1. Start or restart the containers:
   ```bash
   docker-compose down
   docker-compose up -d
   ```
2. Trigger log events in both API and worker services.
3. Check that logs are written to:
   - `./host-logs/netraven/api/api.log`
   - `./host-logs/netraven/worker/worker.log`

## Notes
- The log file path is interpreted inside the container. The host volume ensures persistence and accessibility.
- For the worker, override the file path via environment variable or container-specific config if needed.
- Log rotation is handled by the Python logger as configured.

## Next Steps
- Monitor log file growth and adjust rotation as needed.
- Consider central log aggregation for production if required. 