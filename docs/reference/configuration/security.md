# Security Configuration

This document provides a reference for the security configuration settings in NetRaven.

## Security System Overview

NetRaven's security system provides:
- Authentication and authorization
- Encryption for sensitive data
- Security key management and rotation
- Password policies
- Access control

## Configuration Properties

### Authentication Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `web.authentication.token_expiration` | Integer | `86400` | JWT token expiration time in seconds (default: 24 hours) |
| `web.authentication.jwt_algorithm` | String | `"HS256"` | JWT signing algorithm |
| `web.authentication.require_https` | Boolean | `false` | Whether to require HTTPS for authentication requests |
| `web.authentication.cookie_secure` | Boolean | `false` | Whether to set the secure flag on authentication cookies |
| `web.authentication.password_min_length` | Integer | `8` | Minimum password length for user accounts |

### Key Rotation Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `security.key_rotation.key_path` | String | `"data/keys"` | Directory where encryption keys are stored |
| `security.key_rotation.rotation_interval_days` | Integer | `90` | Interval in days between key rotations |
| `security.key_rotation.automatic_rotation` | Boolean | `true` | Whether to automatically rotate keys |

### Key Backup Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `security.key_rotation.backup.backup_path` | String | `"data/key_backups"` | Directory for key backups |
| `security.key_rotation.backup.auto_backup` | Boolean | `true` | Whether to automatically create backups when rotating keys |
| `security.key_rotation.backup.max_backups` | Integer | `5` | Number of key backups to keep |

### Key Rotation Task Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `tasks.key_rotation.min_age_days` | Integer | `85` | Minimum age of keys in days before rotation |
| `tasks.key_rotation.schedule.type` | String | `"weekly"` | Schedule type. Options: `daily`, `weekly`, `monthly` |
| `tasks.key_rotation.schedule.day` | String | `"monday"` | Day for weekly/monthly schedules |
| `tasks.key_rotation.schedule.time` | String | `"01:00"` | Time for scheduled rotations (HH:MM) |

### API Security Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `web.api.rate_limit.enabled` | Boolean | `true` | Whether to enable API rate limiting |
| `web.api.rate_limit.max_requests` | Integer | `100` | Maximum number of requests per time window |
| `web.api.rate_limit.window_seconds` | Integer | `60` | Time window in seconds for rate limiting |
| `web.api.require_auth` | Boolean | `true` | Whether to require authentication for API access |

### Session Security Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `web.session.idle_timeout` | Integer | `1800` | Session idle timeout in seconds (30 minutes) |
| `web.session.absolute_timeout` | Integer | `43200` | Maximum session duration in seconds (12 hours) |
| `web.session.regenerate_id` | Boolean | `true` | Whether to regenerate session IDs on authentication |

## Environment Variables

The following environment variables can be used to override security settings:

| Environment Variable | Configuration Property | Description |
|----------------------|------------------------|-------------|
| `NETRAVEN_ENCRYPTION_KEY` | Core encryption key | Key used for encrypting sensitive data |
| `TOKEN_SECRET_KEY` | Used in authentication | Secret key for JWT tokens |
| `TOKEN_EXPIRY_HOURS` | Related to `web.authentication.token_expiration` | JWT token expiry time in hours |
| `REQUIRE_HTTPS` | `web.authentication.require_https` | Whether to require HTTPS |
| `SECURE_COOKIES` | `web.authentication.cookie_secure` | Whether to set secure cookies |
| `KEY_ROTATION_INTERVAL_DAYS` | `security.key_rotation.rotation_interval_days` | Key rotation interval |

## Example Configuration

```yaml
# Security configuration example
web:
  authentication:
    token_expiration: 43200  # 12 hours
    jwt_algorithm: HS256
    require_https: true
    cookie_secure: true
    password_min_length: 12
  
  api:
    rate_limit:
      enabled: true
      max_requests: 200
      window_seconds: 60
    require_auth: true
  
  session:
    idle_timeout: 1800  # 30 minutes
    absolute_timeout: 43200  # 12 hours
    regenerate_id: true

security:
  key_rotation:
    key_path: "data/keys"
    rotation_interval_days: 90
    automatic_rotation: true
    
    backup:
      backup_path: "data/key_backups"
      auto_backup: true
      max_backups: 10

tasks:
  key_rotation:
    min_age_days: 85
    schedule:
      type: "weekly"
      day: "sunday"
      time: "02:00"
```

## Key Management System

NetRaven uses a key management system that:
- Stores encryption keys securely
- Rotates keys automatically on a schedule
- Creates backups of keys before rotation
- Manages multiple key versions

### Key Rotation Process

1. Generate a new encryption key
2. Backup the old key
3. Re-encrypt sensitive data with the new key
4. Set the new key as the active key
5. Store the old key as a previous version

## JWT Authentication

NetRaven uses JWT (JSON Web Tokens) for authentication:
- Tokens contain encoded user information and permissions
- Tokens are signed to prevent tampering
- Tokens have an expiration time
- Tokens can be validated without a database lookup

## Development vs. Production

In development environments:
- HTTPS and secure cookies may be disabled for convenience
- Shorter key rotation intervals may be used for testing
- Password policies may be relaxed

In production environments:
- HTTPS should be required (`require_https: true`)
- Secure cookies should be enabled (`cookie_secure: true`)
- Strong password policies should be enforced
- Regular key rotation should be enabled

## Security Best Practices

1. **HTTPS**: Always use HTTPS in production
2. **Environment Variables**: Store sensitive values in environment variables, not config files
3. **Key Management**: Follow proper key management procedures and rotation schedules
4. **Password Policies**: Enforce strong password policies appropriate for your organization
5. **Rate Limiting**: Enable rate limiting to prevent abuse
6. **Session Security**: Use appropriate session timeouts and regeneration policies
7. **Audit Logging**: Enable security audit logging for all sensitive operations

## Troubleshooting

Common security-related issues:

1. **JWT Token Issues**
   - Check the expiration time settings
   - Verify the secret key is properly set
   - Ensure clocks are synchronized between servers

2. **Key Rotation Problems**
   - Check key directory permissions
   - Verify backup paths exist and are writable
   - Ensure sufficient disk space for backups

3. **HTTPS Configuration**
   - If using HTTPS, ensure certificates are valid
   - When `require_https` is true, ensure HTTPS is properly configured 