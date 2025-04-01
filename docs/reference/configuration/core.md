# Core Configuration Settings

This document provides a reference for core system configuration settings in NetRaven.

## Core Settings Overview

Core settings control fundamental application behavior, including:
- System paths and directories
- Base application settings
- Job and task behavior
- Process control

## Configuration Properties

### Core System Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `core.log_level` | String | `"INFO"` | Logging level for core components. Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `core.encryption_key` | String | Environment variable | Key used for encrypting sensitive data. Should be set via the `NETRAVEN_ENCRYPTION_KEY` environment variable |
| `core.backup_dir` | String | `"/app/backups"` | Directory for storing temporary backup files |
| `core.temp_dir` | String | `"/app/temp"` | Directory for temporary files |
| `core.max_workers` | Integer | `4` | Maximum number of worker threads for background tasks |
| `core.job_timeout` | Integer | `3600` | Default timeout in seconds for jobs before they are considered stalled |
| `core.retry_attempts` | Integer | `3` | Number of retry attempts for failed operations |
| `core.retry_delay` | Integer | `5` | Delay in seconds between retry attempts |

### Device Connection Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `device.connection.max_retries` | Integer | `3` | Maximum number of connection retry attempts |
| `device.connection.initial_retry_delay` | Integer | `1` | Initial delay in seconds before first retry |
| `device.connection.timeout` | Integer | `30` | Connection timeout in seconds |

### Directory Paths

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `data_directory` | String | `"data"` | Base directory for application data |
| `logging.directory` | String | `"logs"` | Directory for log files |

## Environment Variables

The following environment variables can be used to override core settings:

| Environment Variable | Configuration Property | Description |
|----------------------|------------------------|-------------|
| `NETRAVEN_ENCRYPTION_KEY` | `core.encryption_key` | Encryption key for sensitive data |
| `NETRAVEN_LOG_LEVEL` | `core.log_level` | Core component log level |
| `NETRAVEN_MAX_WORKERS` | `core.max_workers` | Maximum worker threads |
| `NETRAVEN_JOB_TIMEOUT` | `core.job_timeout` | Default job timeout in seconds |

## Example Configuration

```yaml
# Core configuration example
core:
  log_level: DEBUG
  backup_dir: /data/backups
  temp_dir: /data/temp
  max_workers: 8
  job_timeout: 7200  # 2 hours
  retry_attempts: 5
  retry_delay: 10

# Device connection settings
device:
  connection:
    max_retries: 5
    initial_retry_delay: 2
    timeout: 60
```

## Development vs. Production

In development environments (`NETRAVEN_ENV=development`), core settings are often relaxed for convenience:
- Higher log levels (DEBUG instead of INFO)
- Shorter timeouts for faster feedback
- Fewer retry attempts

In production, settings should prioritize stability and security:
- Lower log levels (INFO or WARNING)
- Appropriate timeouts based on network conditions
- More retry attempts for transient issues

## Best Practices

- **Encryption Key**: Always store the encryption key in an environment variable, never in configuration files
- **Worker Threads**: Set `max_workers` based on available system resources (typically 2× to 4× the number of CPU cores)
- **Timeout Values**: Adjust timeouts based on network conditions and device response times
- **Storage Paths**: Ensure the application has write permissions to all configured directories 