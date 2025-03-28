# Configuration Options Reference

## Introduction

This reference document provides a comprehensive list of all configuration options available in NetRaven. It covers environment variables, configuration file settings, and their default values, helping administrators properly configure NetRaven for their specific environment.

## Configuration Methods

NetRaven can be configured using multiple methods, listed in order of precedence:

1. **Environment Variables**: Highest precedence, overrides other settings
2. **Configuration Files**: YAML or JSON format configuration files
3. **Command-Line Arguments**: For specific component services
4. **Default Values**: Applied when no configuration is specified

## Environment Variables

### Core Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_ENV` | Environment name (development, testing, production) | `production` | `NETRAVEN_ENV=development` |
| `NETRAVEN_CONFIG_PATH` | Path to configuration file | `/app/config/netraven.yml` | `NETRAVEN_CONFIG_PATH=/etc/netraven/config.yml` |
| `NETRAVEN_LOG_LEVEL` | Logging verbosity | `info` | `NETRAVEN_LOG_LEVEL=debug` |
| `NETRAVEN_SECRET_KEY` | Secret key for encryption and tokens | *Required* | `NETRAVEN_SECRET_KEY=a7c4b2e9f8d1` |
| `NETRAVEN_ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` | `NETRAVEN_ALLOWED_HOSTS=netraven.example.com,api.netraven.com` |

### Database Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_DB_ENGINE` | Database engine | `postgresql` | `NETRAVEN_DB_ENGINE=postgresql` |
| `NETRAVEN_DB_NAME` | Database name | `netraven` | `NETRAVEN_DB_NAME=netraven_prod` |
| `NETRAVEN_DB_USER` | Database username | `postgres` | `NETRAVEN_DB_USER=netraven_user` |
| `NETRAVEN_DB_PASSWORD` | Database password | *Required* | `NETRAVEN_DB_PASSWORD=securepassword` |
| `NETRAVEN_DB_HOST` | Database hostname | `localhost` | `NETRAVEN_DB_HOST=db.example.com` |
| `NETRAVEN_DB_PORT` | Database port | `5432` | `NETRAVEN_DB_PORT=5433` |
| `NETRAVEN_DB_SSL_MODE` | SSL mode for database connection | `prefer` | `NETRAVEN_DB_SSL_MODE=require` |
| `NETRAVEN_DB_CONNECTION_TIMEOUT` | Connection timeout in seconds | `30` | `NETRAVEN_DB_CONNECTION_TIMEOUT=60` |
| `NETRAVEN_DB_POOL_SIZE` | Connection pool size | `10` | `NETRAVEN_DB_POOL_SIZE=20` |
| `NETRAVEN_DB_POOL_OVERFLOW` | Max overflow connections | `20` | `NETRAVEN_DB_POOL_OVERFLOW=40` |

### API Service Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_API_HOST` | API service host | `0.0.0.0` | `NETRAVEN_API_HOST=api.netraven.local` |
| `NETRAVEN_API_PORT` | API service port | `8000` | `NETRAVEN_API_PORT=8080` |
| `NETRAVEN_API_WORKERS` | Number of API workers | `4` | `NETRAVEN_API_WORKERS=8` |
| `NETRAVEN_API_CORS_ORIGINS` | Allowed CORS origins | `http://localhost:8080` | `NETRAVEN_API_CORS_ORIGINS=https://app.example.com` |
| `NETRAVEN_API_RATE_LIMIT` | Requests per minute | `300` | `NETRAVEN_API_RATE_LIMIT=500` |
| `NETRAVEN_API_TIMEOUT` | Request timeout in seconds | `30` | `NETRAVEN_API_TIMEOUT=60` |
| `NETRAVEN_API_MAX_UPLOAD_MB` | Maximum upload size in MB | `50` | `NETRAVEN_API_MAX_UPLOAD_MB=100` |

### Gateway Service Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_GATEWAY_HOST` | Gateway service host | `0.0.0.0` | `NETRAVEN_GATEWAY_HOST=gateway.netraven.local` |
| `NETRAVEN_GATEWAY_PORT` | Gateway service port | `8001` | `NETRAVEN_GATEWAY_PORT=8081` |
| `NETRAVEN_GATEWAY_WORKERS` | Number of gateway workers | `4` | `NETRAVEN_GATEWAY_WORKERS=8` |
| `NETRAVEN_GATEWAY_TIMEOUT` | Device command timeout in seconds | `60` | `NETRAVEN_GATEWAY_TIMEOUT=120` |
| `NETRAVEN_GATEWAY_MAX_CONNECTIONS` | Maximum concurrent device connections | `20` | `NETRAVEN_GATEWAY_MAX_CONNECTIONS=50` |
| `NETRAVEN_GATEWAY_CONNECTION_RETRY` | Number of connection retries | `3` | `NETRAVEN_GATEWAY_CONNECTION_RETRY=5` |

### Scheduler Service Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_SCHEDULER_HOST` | Scheduler service host | `0.0.0.0` | `NETRAVEN_SCHEDULER_HOST=scheduler.netraven.local` |
| `NETRAVEN_SCHEDULER_PORT` | Scheduler service port | `8002` | `NETRAVEN_SCHEDULER_PORT=8082` |
| `NETRAVEN_SCHEDULER_WORKERS` | Number of task workers | `4` | `NETRAVEN_SCHEDULER_WORKERS=8` |
| `NETRAVEN_SCHEDULER_MAX_RETRIES` | Maximum task retry attempts | `3` | `NETRAVEN_SCHEDULER_MAX_RETRIES=5` |
| `NETRAVEN_SCHEDULER_RETRY_DELAY` | Delay between retries in seconds | `300` | `NETRAVEN_SCHEDULER_RETRY_DELAY=600` |

### Authentication Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_AUTH_TOKEN_EXPIRY` | Token expiration time in minutes | `1440` (24 hours) | `NETRAVEN_AUTH_TOKEN_EXPIRY=720` |
| `NETRAVEN_AUTH_REFRESH_EXPIRY` | Refresh token expiration in days | `7` | `NETRAVEN_AUTH_REFRESH_EXPIRY=14` |
| `NETRAVEN_AUTH_METHODS` | Enabled authentication methods | `local` | `NETRAVEN_AUTH_METHODS=local,ldap,oauth` |
| `NETRAVEN_AUTH_PASSWORD_MIN_LENGTH` | Minimum password length | `8` | `NETRAVEN_AUTH_PASSWORD_MIN_LENGTH=12` |
| `NETRAVEN_AUTH_REQUIRE_MFA` | Require multi-factor authentication | `false` | `NETRAVEN_AUTH_REQUIRE_MFA=true` |
| `NETRAVEN_AUTH_FAILED_ATTEMPTS` | Max failed login attempts before lockout | `5` | `NETRAVEN_AUTH_FAILED_ATTEMPTS=3` |
| `NETRAVEN_AUTH_LOCKOUT_MINUTES` | Account lockout duration in minutes | `30` | `NETRAVEN_AUTH_LOCKOUT_MINUTES=60` |

### LDAP Authentication

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_LDAP_ENABLED` | Enable LDAP authentication | `false` | `NETRAVEN_LDAP_ENABLED=true` |
| `NETRAVEN_LDAP_SERVER` | LDAP server URL | `ldap://localhost:389` | `NETRAVEN_LDAP_SERVER=ldap://ldap.example.com:389` |
| `NETRAVEN_LDAP_BIND_DN` | LDAP bind DN | `cn=admin,dc=example,dc=com` | `NETRAVEN_LDAP_BIND_DN=cn=netraven,ou=service,dc=example,dc=com` |
| `NETRAVEN_LDAP_BIND_PASSWORD` | LDAP bind password | *Required if LDAP enabled* | `NETRAVEN_LDAP_BIND_PASSWORD=ldappassword` |
| `NETRAVEN_LDAP_USER_BASE` | LDAP user search base | `ou=users,dc=example,dc=com` | `NETRAVEN_LDAP_USER_BASE=ou=employees,dc=example,dc=com` |
| `NETRAVEN_LDAP_USER_FILTER` | LDAP user search filter | `(uid={username})` | `NETRAVEN_LDAP_USER_FILTER=(sAMAccountName={username})` |
| `NETRAVEN_LDAP_GROUP_BASE` | LDAP group search base | `ou=groups,dc=example,dc=com` | `NETRAVEN_LDAP_GROUP_BASE=ou=security,dc=example,dc=com` |
| `NETRAVEN_LDAP_ADMIN_GROUP` | LDAP admin group name | `netraven-admins` | `NETRAVEN_LDAP_ADMIN_GROUP=Network_Admins` |

### Storage Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_STORAGE_TYPE` | Storage backend type | `local` | `NETRAVEN_STORAGE_TYPE=s3` |
| `NETRAVEN_STORAGE_PATH` | Local storage path | `/app/data/backups` | `NETRAVEN_STORAGE_PATH=/var/lib/netraven/backups` |
| `NETRAVEN_STORAGE_RETENTION` | Backup retention count per device | `10` | `NETRAVEN_STORAGE_RETENTION=20` |
| `NETRAVEN_STORAGE_COMPRESS` | Compress backup files | `true` | `NETRAVEN_STORAGE_COMPRESS=false` |
| `NETRAVEN_STORAGE_ENCRYPT` | Encrypt backup files | `false` | `NETRAVEN_STORAGE_ENCRYPT=true` |
| `NETRAVEN_STORAGE_VERIFY` | Verify backup integrity | `true` | `NETRAVEN_STORAGE_VERIFY=true` |

### S3 Storage Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_S3_ENDPOINT` | S3 endpoint URL | `https://s3.amazonaws.com` | `NETRAVEN_S3_ENDPOINT=https://minio.example.com` |
| `NETRAVEN_S3_REGION` | S3 region | `us-east-1` | `NETRAVEN_S3_REGION=eu-west-1` |
| `NETRAVEN_S3_BUCKET` | S3 bucket name | `netraven-backups` | `NETRAVEN_S3_BUCKET=network-configs` |
| `NETRAVEN_S3_ACCESS_KEY` | S3 access key | *Required if S3 enabled* | `NETRAVEN_S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE` |
| `NETRAVEN_S3_SECRET_KEY` | S3 secret key | *Required if S3 enabled* | `NETRAVEN_S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `NETRAVEN_S3_PATH_PREFIX` | S3 object path prefix | `backups/` | `NETRAVEN_S3_PATH_PREFIX=configs/netraven/` |
| `NETRAVEN_S3_SSL_VERIFY` | Verify SSL certificates | `true` | `NETRAVEN_S3_SSL_VERIFY=false` |

### Email Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_SMTP_HOST` | SMTP server host | `localhost` | `NETRAVEN_SMTP_HOST=smtp.example.com` |
| `NETRAVEN_SMTP_PORT` | SMTP server port | `25` | `NETRAVEN_SMTP_PORT=587` |
| `NETRAVEN_SMTP_USER` | SMTP username | *None* | `NETRAVEN_SMTP_USER=notifications@example.com` |
| `NETRAVEN_SMTP_PASSWORD` | SMTP password | *None* | `NETRAVEN_SMTP_PASSWORD=mailpassword` |
| `NETRAVEN_SMTP_USE_TLS` | Use TLS for SMTP | `true` | `NETRAVEN_SMTP_USE_TLS=true` |
| `NETRAVEN_SMTP_FROM_EMAIL` | Sender email address | `netraven@example.com` | `NETRAVEN_SMTP_FROM_EMAIL=netraven@company.com` |
| `NETRAVEN_SMTP_FROM_NAME` | Sender name | `NetRaven` | `NETRAVEN_SMTP_FROM_NAME=NetRaven Monitoring` |

### Monitoring Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_MONITORING_ENABLED` | Enable metrics collection | `true` | `NETRAVEN_MONITORING_ENABLED=true` |
| `NETRAVEN_MONITORING_INTERVAL` | Metrics collection interval in seconds | `15` | `NETRAVEN_MONITORING_INTERVAL=30` |
| `NETRAVEN_MONITORING_RETENTION` | Metrics retention period in days | `30` | `NETRAVEN_MONITORING_RETENTION=60` |
| `NETRAVEN_PROMETHEUS_ENABLED` | Enable Prometheus metrics endpoints | `true` | `NETRAVEN_PROMETHEUS_ENABLED=true` |
| `NETRAVEN_MONITORING_DETAIL_LEVEL` | Monitoring detail level (basic, standard, detailed) | `standard` | `NETRAVEN_MONITORING_DETAIL_LEVEL=detailed` |

### Logging Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NETRAVEN_LOG_LEVEL` | Log level | `info` | `NETRAVEN_LOG_LEVEL=debug` |
| `NETRAVEN_LOG_FORMAT` | Log format (json, text) | `json` | `NETRAVEN_LOG_FORMAT=text` |
| `NETRAVEN_LOG_PATH` | Log file path | `/app/logs` | `NETRAVEN_LOG_PATH=/var/log/netraven` |
| `NETRAVEN_LOG_MAX_SIZE` | Maximum log file size in MB | `100` | `NETRAVEN_LOG_MAX_SIZE=200` |
| `NETRAVEN_LOG_BACKUP_COUNT` | Number of log files to keep | `10` | `NETRAVEN_LOG_BACKUP_COUNT=20` |
| `NETRAVEN_LOG_STDOUT` | Log to standard output | `true` | `NETRAVEN_LOG_STDOUT=false` |

## Configuration File Format

NetRaven supports both YAML and JSON configuration files. Below is an example of a YAML configuration file:

```yaml
# netraven.yml
core:
  environment: production
  secret_key: your-secret-key
  allowed_hosts:
    - netraven.example.com
    - api.netraven.com

database:
  engine: postgresql
  name: netraven
  user: netraven_user
  password: secure-password
  host: db.example.com
  port: 5432
  ssl_mode: require
  connection_timeout: 30
  pool:
    size: 10
    overflow: 20

api:
  host: 0.0.0.0
  port: 8000
  workers: 4
  cors_origins:
    - https://app.example.com
  rate_limit: 300
  timeout: 30
  max_upload_mb: 50

gateway:
  host: 0.0.0.0
  port: 8001
  workers: 4
  timeout: 60
  max_connections: 20
  connection_retry: 3

scheduler:
  host: 0.0.0.0
  port: 8002
  workers: 4
  max_retries: 3
  retry_delay: 300

auth:
  token_expiry: 1440
  refresh_expiry: 7
  methods:
    - local
    - ldap
  password_min_length: 12
  require_mfa: false
  failed_attempts: 5
  lockout_minutes: 30
  
  ldap:
    enabled: true
    server: ldap://ldap.example.com:389
    bind_dn: cn=netraven,ou=service,dc=example,dc=com
    bind_password: ldap-password
    user_base: ou=employees,dc=example,dc=com
    user_filter: (sAMAccountName={username})
    group_base: ou=security,dc=example,dc=com
    admin_group: Network_Admins

storage:
  type: s3
  retention: 20
  compress: true
  encrypt: true
  verify: true
  
  s3:
    endpoint: https://s3.amazonaws.com
    region: us-east-1
    bucket: network-configs
    access_key: AKIAIOSFODNN7EXAMPLE
    secret_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    path_prefix: configs/netraven/
    ssl_verify: true

email:
  smtp_host: smtp.example.com
  smtp_port: 587
  smtp_user: notifications@example.com
  smtp_password: mail-password
  use_tls: true
  from_email: netraven@company.com
  from_name: NetRaven Monitoring

monitoring:
  enabled: true
  interval: 15
  retention: 30
  prometheus_enabled: true
  detail_level: standard

logging:
  level: info
  format: json
  path: /var/log/netraven
  max_size: 100
  backup_count: 10
  stdout: true
```

## Configuration Hierarchy and Precedence

When multiple configuration sources define the same setting, NetRaven follows this precedence order:

1. Environment variables (highest precedence)
2. Command-line arguments
3. Configuration file
4. Default values (lowest precedence)

Example precedence resolution:

```
Setting: Database host
Default value: localhost
Configuration file: db.internal.example.com
Environment variable: NETRAVEN_DB_HOST=db.prod.example.com

Final value used: db.prod.example.com (from environment variable)
```

## Sensitive Configuration

For security-sensitive configuration:

1. Avoid storing secrets in configuration files
2. Use environment variables for secrets when possible
3. If using configuration files with secrets:
   - Limit file permissions (`chmod 600 config.yml`)
   - Ensure only authorized users can access the file
   - Consider using a secrets management solution

## Configuration Validation

NetRaven validates configuration at startup. If critical configuration is missing or invalid, the service will not start.

To validate a configuration file without starting services:

```bash
netraven-admin validate-config --config-path /path/to/config.yml
```

## Dynamic Configuration

Some configuration options can be changed at runtime through the admin interface:

1. Navigate to **Settings** > **System Configuration**
2. Modify settings as needed
3. Click **Save Changes**

Settings that require a service restart will be indicated in the UI.

## Environment-Specific Configuration

It's recommended to maintain separate configuration files for different environments:

- `netraven-dev.yml` - Development
- `netraven-test.yml` - Testing
- `netraven-prod.yml` - Production

Specify the configuration file using the `NETRAVEN_CONFIG_PATH` environment variable.

## Related Documentation

- [Environment Variables Reference](./environment-variables.md)
- [Configuration File Format](./configuration-file-format.md)
- [Installation Guide](../getting-started/installation.md)
- [Security Configuration](../admin-guide/security.md) 