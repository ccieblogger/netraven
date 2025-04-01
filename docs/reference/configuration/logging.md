# Logging Configuration

This document provides a reference for the logging configuration settings in NetRaven.

## Logging System Overview

NetRaven's logging system provides:
- Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Multiple output destinations (console, file, JSON)
- Component-specific log files
- Rotation policies for log files
- Sensitive data filtering

## Configuration Properties

### Main Logging Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `logging.level` | String | `"INFO"` | Global logging level. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `logging.directory` | String | `"logs"` | Directory for log files |
| `logging.filename` | String | `"netraven.log"` | Filename for the main log file |
| `logging.retention_days` | Integer | `30` | Number of days to keep log files |
| `logging.session_log_retention_days` | Integer | `14` | Number of days to keep Netmiko session logs |
| `logging.use_database_logging` | Boolean | `true` | Whether to store logs in the database |
| `logging.log_to_file` | Boolean | `false` | Whether to write logs to files (in addition to other destinations) |

### Console Logging

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `logging.console.enabled` | Boolean | `true` | Whether to log to console |
| `logging.console.level` | String | `"INFO"` | Console logging level |

### File Logging

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `logging.file.enabled` | Boolean | `true` | Whether to log to file |
| `logging.file.level` | String | `"DEBUG"` | File logging level |
| `logging.file.max_size_mb` | Integer | `10` | Maximum log file size in MB before rotation |
| `logging.file.backup_count` | Integer | `5` | Number of backup log files to keep |
| `logging.file.rotation_when` | String | None | When to rotate logs. Options: `S`, `M`, `H`, `D`, `midnight`, `W0-W6` |
| `logging.file.rotation_interval` | Integer | `1` | Interval multiplier for rotation_when |

### JSON Logging

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `logging.json.enabled` | Boolean | `false` | Whether to log in JSON format |
| `logging.json.filename` | String | `"netraven.json.log"` | Filename for JSON log file |
| `logging.json.max_size_mb` | Integer | `10` | Maximum JSON log file size in MB before rotation |
| `logging.json.backup_count` | Integer | `5` | Number of backup JSON log files to keep |
| `logging.json.rotation_when` | String | None | Same options as file logging |
| `logging.json.rotation_interval` | Integer | `1` | Same as file logging |

### Component-Specific Logging

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `logging.components.enabled` | Boolean | `true` | Whether to use component-specific log files |
| `logging.components.level` | String | `"DEBUG"` | Default level for component logs |
| `logging.components.max_size_mb` | Integer | `10` | Maximum component log file size in MB |
| `logging.components.backup_count` | Integer | `5` | Number of backup component log files to keep |
| `logging.components.files.frontend` | String | `"frontend.log"` | Frontend component log filename |
| `logging.components.files.backend` | String | `"backend.log"` | Backend component log filename |
| `logging.components.files.jobs` | String | `"jobs.log"` | Jobs component log filename |
| `logging.components.files.auth` | String | `"auth.log"` | Authentication component log filename |

### Sensitive Data Filtering

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `logging.sensitive_data.redact_enabled` | Boolean | `true` | Whether to redact sensitive information from logs |

## Environment Variables

The following environment variables can be used to override logging settings:

| Environment Variable | Configuration Property | Description |
|----------------------|------------------------|-------------|
| `NETRAVEN_LOG_LEVEL` | `logging.level` | Global logging level |
| `NETRAVEN_LOG_DIR` | `logging.directory` | Directory for log files |
| `NETRAVEN_LOG_FILE` | `logging.filename` | Main log filename |
| `NETMIKO_PRESERVE_LOGS` | related to `logging.session_log_retention_days` | Whether to preserve network device session logs |

## Example Configuration

```yaml
# Logging configuration example
logging:
  level: DEBUG
  directory: /var/log/netraven
  filename: netraven.log
  retention_days: 60
  session_log_retention_days: 30
  use_database_logging: true
  log_to_file: true
  
  # Console logging
  console:
    enabled: true
    level: INFO
  
  # File logging
  file:
    enabled: true
    level: DEBUG
    max_size_mb: 20
    backup_count: 10
    rotation_when: midnight
    rotation_interval: 1
  
  # JSON logging
  json:
    enabled: true
    filename: netraven.json.log
    max_size_mb: 20
    backup_count: 5
  
  # Component-specific logging
  components:
    enabled: true
    level: DEBUG
    max_size_mb: 15
    backup_count: 3
    files:
      frontend: frontend-app.log
      backend: backend-api.log
      jobs: scheduled-jobs.log
      auth: authentication.log
  
  # Sensitive data filtering
  sensitive_data:
    redact_enabled: true
```

## Development vs. Production

In development environments:
- Higher verbosity (`DEBUG` level) is typically used
- Console logging is more important than file logging
- Smaller log file sizes and fewer backups are sufficient

In production environments:
- Lower verbosity (`INFO` or `WARNING` for console) to reduce noise
- File and JSON logging become more important
- Longer retention periods and more backup files
- Properly configured log rotation to manage disk space

## Rotation Strategies

NetRaven supports two log rotation strategies:

1. **Size-based rotation** (default): Rotates logs when they reach `max_size_mb`
2. **Time-based rotation**: Rotates logs based on a schedule

For time-based rotation, set `rotation_when` to one of:
- `S`: Seconds
- `M`: Minutes
- `H`: Hours
- `D`: Days
- `midnight`: At midnight
- `W0-W6`: Weekday (0=Monday, 6=Sunday)

The `rotation_interval` multiplies the rotation period. For example, `rotation_when: H` and `rotation_interval: 6` rotates logs every 6 hours.

## Security Considerations

- **Sensitive Data**: Ensure `sensitive_data.redact_enabled` is set to `true` in production
- **Log Access**: Restrict access to log files in production environments
- **Log Volume**: Monitor log volume to prevent disk space exhaustion
- **Personal Data**: Avoid logging personal or identifiable information

## Troubleshooting

If logs are not appearing as expected:
1. Check that the log directory exists and has appropriate permissions
2. Verify the logging level is set appropriately
3. Ensure the correct handlers are enabled
4. Check that log rotation is configured correctly 