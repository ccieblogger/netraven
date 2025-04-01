# Environment Variables Reference

This document provides a comprehensive reference for all environment variables supported by NetRaven. Environment variables provide a way to configure the application without modifying configuration files, which is particularly useful in containerized environments.

## Core Environment Variables

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `NETRAVEN_ENV` | `production` | Application environment. Options: `production`, `development`, `test` |
| `NETRAVEN_CONFIG` | See below | Path to the configuration file. If not set, searches in default locations |
| `NETRAVEN_ENCRYPTION_KEY` | None | Key used for encrypting sensitive data. **Required in production** |
| `NETRAVEN_LOG_LEVEL` | `INFO` | Global logging level. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `NETRAVEN_MAX_WORKERS` | `4` | Maximum number of worker threads for background tasks |

### Configuration File Location

If `NETRAVEN_CONFIG` is not set, the system searches for configuration files in these locations (in order):

1. `./config.yml` in the current directory
2. `~/.config/netraven/config.yml` in the user's home directory
3. `/etc/netraven/config.yml` for system-wide configuration

## Web Service Environment Variables

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `NETRAVEN_WEB_HOST` | `0.0.0.0` | Host IP address for the web service |
| `NETRAVEN_WEB_PORT` | `8000` | Port number for the web service |
| `NETRAVEN_WEB_DEBUG` | `false` | Enable debug mode for the web service |
| `TOKEN_SECRET_KEY` | None | Secret key for JWT token generation. **Required in production** |
| `TOKEN_EXPIRY_HOURS` | `24` | JWT token expiry time in hours |

## Database Environment Variables

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `NETRAVEN_WEB_DATABASE_TYPE` | `sqlite` | Database type. Options: `sqlite`, `postgres`, `mysql` |
| `NETRAVEN_WEB_DATABASE_HOST` | `postgres` | Database host |
| `NETRAVEN_WEB_DATABASE_PORT` | `5432` | Database port |
| `NETRAVEN_WEB_DATABASE_NAME` | `netraven` | Database name |
| `NETRAVEN_WEB_DATABASE_USER` | `netraven` | Database username |
| `NETRAVEN_WEB_DATABASE_PASSWORD` | `netraven` | Database password |

## Storage Environment Variables

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `NETRAVEN_STORAGE_TYPE` | `local` | Backup storage type. Options: `local`, `s3` |
| `NETRAVEN_S3_BUCKET` | None | S3 bucket name for backups (when using S3 storage) |
| `NETRAVEN_S3_PREFIX` | `backups/` | Prefix path in S3 bucket |
| `NETRAVEN_LOCAL_DIR` | `data/backups` | Local directory for backups (when using local storage) |

## Logging Environment Variables

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `NETRAVEN_LOG_LEVEL` | `INFO` | Global logging level |
| `NETRAVEN_LOG_DIR` | `logs` | Directory for log files |
| `NETRAVEN_LOG_FILE` | `netraven.log` | Filename for main log file |
| `NETMIKO_PRESERVE_LOGS` | `true` | Whether to preserve Netmiko SSH session logs |

## Gateway Environment Variables

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `NETRAVEN_GATEWAY_URL` | `http://localhost:8001` | URL for the device gateway service |
| `NETRAVEN_GATEWAY_API_KEY` | None | API key for accessing the gateway service |
| `NETRAVEN_GATEWAY_TIMEOUT` | `60` | Gateway request timeout in seconds |

## Service-Specific Environment Variables

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `SCHEDULER_WORKERS` | `2` | Number of worker threads for the scheduler service |
| `KEY_ROTATION_INTERVAL_DAYS` | `90` | Interval in days between key rotation operations |
| `CONFIG_FILE` | None | Specific configuration file path for individual services |

## Docker Environment Variables

These variables are specific to Docker deployments and not used by the application directly:

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `POSTGRES_PASSWORD` | None | PostgreSQL root password (used by Docker PostgreSQL container) |
| `POSTGRES_USER` | None | PostgreSQL root username (used by Docker PostgreSQL container) |
| `POSTGRES_DB` | None | PostgreSQL default database name (used by Docker PostgreSQL container) |

## Security-Related Environment Variables

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `NETRAVEN_ENCRYPTION_KEY` | None | Key for encrypting sensitive data |
| `TOKEN_SECRET_KEY` | None | Secret key for JWT tokens |
| `SECURE_COOKIES` | `false` | Whether to set the secure flag on cookies |
| `REQUIRE_HTTPS` | `false` | Whether to require HTTPS for authentication |

## Example Docker Environment Configuration

```yaml
services:
  api:
    environment:
      - NETRAVEN_ENV=production
      - NETRAVEN_ENCRYPTION_KEY=your-secure-encryption-key
      - TOKEN_SECRET_KEY=your-secure-token-key
      - NETRAVEN_WEB_HOST=0.0.0.0
      - NETRAVEN_WEB_PORT=8000
      - NETRAVEN_WEB_DATABASE_TYPE=postgres
      - NETRAVEN_WEB_DATABASE_HOST=postgres
      - NETRAVEN_WEB_DATABASE_USER=netraven
      - NETRAVEN_WEB_DATABASE_PASSWORD=secure-password
      - NETRAVEN_LOG_LEVEL=INFO
      - REQUIRE_HTTPS=true
      - SECURE_COOKIES=true
```

## Environment Considerations

### Production Environment

In production, you should set at minimum:
- `NETRAVEN_ENV=production`
- `NETRAVEN_ENCRYPTION_KEY` (strong random value)
- `TOKEN_SECRET_KEY` (strong random value)
- Database credentials via environment variables
- `REQUIRE_HTTPS=true`
- `SECURE_COOKIES=true`

### Development Environment

In development, you might use:
- `NETRAVEN_ENV=development`
- `NETRAVEN_LOG_LEVEL=DEBUG`
- `NETRAVEN_WEB_DEBUG=true`
- Simplified database credentials for local development

### Test Environment

For automated testing:
- `NETRAVEN_ENV=test`
- In-memory or temporary storage configurations
- Short-lived token expirations

## Security Best Practices

- **Secret Values**: Never commit secret values like encryption keys and passwords to version control
- **Production Secrets**: Use a secure secrets management solution for production deployments
- **Variable Isolation**: Each container should only receive the environment variables it needs
- **Default Overrides**: Always override default passwords and keys in production environments 