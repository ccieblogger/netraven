# Integrations Configuration

This document provides a reference for the external integrations configuration settings in NetRaven.

## Integrations Overview

NetRaven can integrate with various external systems:
- Netbox for network inventory management
- Git repositories for configuration version control
- External authentication systems
- Monitoring and notification systems

## Configuration Properties

### Netbox Integration

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `netbox.url` | String | `"https://netbox.example.com"` | URL of the Netbox instance |
| `netbox.verify_ssl` | Boolean | `true` | Whether to verify SSL certificates when connecting to Netbox |
| `netbox.timeout` | Integer | `30` | Connection timeout in seconds |
| `netbox.api_token` | String | None | Netbox API token for authentication |
| `netbox.devices_query` | Object | `{}` | Query parameters for filtering devices from Netbox |
| `netbox.sync_interval` | Integer | `3600` | Interval in seconds for syncing data from Netbox |

### Git Integration

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `git.enabled` | Boolean | `false` | Whether to enable Git integration |
| `git.repo_url` | String | `""` | Git repository URL |
| `git.branch` | String | `"main"` | Git branch to use |
| `git.local_path` | String | `""` | Local path for Git repository |
| `git.ssh_key_path` | String | None | Path to SSH key for Git authentication |
| `git.username` | String | None | Username for Git authentication (HTTP) |
| `git.password` | String | None | Password for Git authentication (HTTP) |

### Device Configuration Sources

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `devices.config_source` | String | `"local"` | Source for device configurations. Options: `local` or `git` |
| `devices.local_path` | String | `"data/configs"` | Path to local device configurations |

### External Authentication

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `auth.external.enabled` | Boolean | `false` | Whether to enable external authentication |
| `auth.external.type` | String | `"ldap"` | External authentication type. Options: `ldap`, `oauth`, `saml` |
| `auth.external.auto_create_users` | Boolean | `true` | Whether to automatically create users from external auth |
| `auth.external.default_role` | String | `"viewer"` | Default role for auto-created users |

### LDAP Authentication

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `auth.ldap.server` | String | None | LDAP server address |
| `auth.ldap.port` | Integer | `389` | LDAP server port |
| `auth.ldap.use_ssl` | Boolean | `false` | Whether to use SSL for LDAP connection |
| `auth.ldap.bind_dn` | String | None | Bind DN for LDAP authentication |
| `auth.ldap.bind_password` | String | None | Bind password for LDAP authentication |
| `auth.ldap.search_base` | String | None | Base DN for LDAP search |
| `auth.ldap.user_filter` | String | `"(uid={username})"` | LDAP filter for user search |
| `auth.ldap.group_filter` | String | `"(cn=netraven*)"` | LDAP filter for group search |
| `auth.ldap.attr_username` | String | `"uid"` | LDAP attribute for username |
| `auth.ldap.attr_email` | String | `"mail"` | LDAP attribute for email |
| `auth.ldap.attr_name` | String | `"cn"` | LDAP attribute for full name |

### Notification Systems

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `notifications.enabled` | Boolean | `true` | Whether to enable notifications |
| `notifications.methods` | List | `["email"]` | Notification methods to use |
| `notifications.events` | List | `["backup_failed", "device_unreachable"]` | Events that trigger notifications |

### Email Notifications

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `notifications.email.server` | String | `"localhost"` | SMTP server address |
| `notifications.email.port` | Integer | `25` | SMTP server port |
| `notifications.email.use_tls` | Boolean | `false` | Whether to use TLS for SMTP connection |
| `notifications.email.username` | String | None | SMTP authentication username |
| `notifications.email.password` | String | None | SMTP authentication password |
| `notifications.email.from_address` | String | `"netraven@example.com"` | From address for notification emails |
| `notifications.email.subject_prefix` | String | `"[NetRaven] "` | Prefix for email subject lines |

### Webhook Notifications

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `notifications.webhook.url` | String | None | Webhook URL for notifications |
| `notifications.webhook.headers` | Object | `{}` | Custom headers for webhook requests |
| `notifications.webhook.method` | String | `"POST"` | HTTP method for webhook requests |
| `notifications.webhook.timeout` | Integer | `10` | Webhook request timeout in seconds |

## Environment Variables

The following environment variables can be used to override integration settings:

| Environment Variable | Configuration Property | Description |
|----------------------|------------------------|-------------|
| `NETBOX_URL` | `netbox.url` | Netbox instance URL |
| `NETBOX_API_TOKEN` | `netbox.api_token` | Netbox API token |
| `GIT_REPO_URL` | `git.repo_url` | Git repository URL |
| `LDAP_SERVER` | `auth.ldap.server` | LDAP server address |
| `LDAP_BIND_DN` | `auth.ldap.bind_dn` | LDAP bind DN |
| `LDAP_BIND_PASSWORD` | `auth.ldap.bind_password` | LDAP bind password |
| `SMTP_SERVER` | `notifications.email.server` | SMTP server address |
| `SMTP_USERNAME` | `notifications.email.username` | SMTP username |
| `SMTP_PASSWORD` | `notifications.email.password` | SMTP password |
| `WEBHOOK_URL` | `notifications.webhook.url` | Webhook URL |

## Example Configuration

```yaml
# External integrations configuration example

# Netbox integration
netbox:
  url: "https://netbox.example.org"
  verify_ssl: true
  timeout: 30
  api_token: ${NETBOX_API_TOKEN}  # Set via environment variable
  devices_query:
    status: "active"
    site: "main-datacenter"
  sync_interval: 7200  # Every 2 hours

# Git integration
git:
  enabled: true
  repo_url: "git@github.com:example/network-configs.git"
  branch: "main"
  local_path: "/var/netraven/git-repo"
  ssh_key_path: "/var/netraven/keys/git-deploy-key"

# Device configuration source
devices:
  config_source: "git"
  local_path: "data/configs"

# External authentication
auth:
  external:
    enabled: true
    type: "ldap"
    auto_create_users: true
    default_role: "operator"
  
  # LDAP configuration
  ldap:
    server: "ldap.example.org"
    port: 636
    use_ssl: true
    bind_dn: "cn=netraven,ou=service-accounts,dc=example,dc=org"
    bind_password: ${LDAP_BIND_PASSWORD}  # Set via environment variable
    search_base: "ou=users,dc=example,dc=org"
    user_filter: "(uid={username})"
    group_filter: "(cn=network-*)"
    attr_username: "uid"
    attr_email: "mail"
    attr_name: "displayName"

# Notification systems
notifications:
  enabled: true
  methods:
    - email
    - webhook
  events:
    - backup_failed
    - device_unreachable
    - config_changed
    - job_failed
  
  # Email notifications
  email:
    server: "smtp.example.org"
    port: 587
    use_tls: true
    username: "notifications@example.org"
    password: ${SMTP_PASSWORD}  # Set via environment variable
    from_address: "netraven@example.org"
    subject_prefix: "[NetRaven Alert] "
  
  # Webhook notifications
  webhook:
    url: "https://alerts.example.org/incoming/netraven"
    headers:
      X-API-Key: ${WEBHOOK_API_KEY}  # Set via environment variable
    method: "POST"
    timeout: 5
```

## Integration Descriptions

### Netbox Integration

Netbox integration allows NetRaven to:
- Discover network devices from Netbox inventory
- Import device metadata and attributes
- Keep device information synchronized
- Use Netbox as the source of truth for network inventory

### Git Integration

Git integration provides:
- Version control for device configurations
- History tracking of configuration changes
- Collaboration capabilities for team members
- Integration with existing Git workflows

### External Authentication

External authentication offers:
- Single sign-on (SSO) capabilities
- Integration with corporate identity systems
- Centralized user management
- Role-based access control

### Notification Systems

Notification systems enable:
- Alerting on important system events
- Integration with existing monitoring systems
- Customizable notification triggers
- Multiple delivery methods

## Security Considerations

- **API Tokens**: Store sensitive tokens like Netbox API tokens in environment variables
- **Git Credentials**: Use SSH keys with proper permissions for Git authentication
- **LDAP Bind Credentials**: Use a dedicated service account with minimal permissions
- **SMTP Authentication**: Use TLS and proper authentication for email notifications
- **Webhook Security**: Use HTTPS and API keys for webhook endpoints

## Best Practices

1. **Configuration**: Use environment variables for sensitive integration credentials
2. **Testing**: Test integrations before enabling them in production
3. **Monitoring**: Monitor integration health and connectivity
4. **Failover**: Implement fallback mechanisms for critical integrations
5. **Documentation**: Document integration points and dependencies 