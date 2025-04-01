# Backup Configuration

This document provides a reference for the backup configuration settings in NetRaven.

## Backup System Overview

NetRaven's backup system provides:
- Network device configuration backup storage
- Multiple storage backends (local filesystem, S3)
- Git integration for version control
- Configurable backup formats and naming

## Configuration Properties

### Main Backup Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `backup.storage.type` | String | `"local"` | Storage backend type. Options: `local`, `s3` |
| `backup.format` | String | `"{host}_config.txt"` | Filename format for backups. Variables: `{host}`, `{date}`, `{time}` |

### Local Storage Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `backup.storage.local.directory` | String | `"data/backups"` | Local directory for storing backups |

### S3 Storage Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `backup.storage.s3.bucket` | String | `""` | AWS S3 bucket name |
| `backup.storage.s3.prefix` | String | `"backups/"` | Prefix path within the S3 bucket |
| `backup.storage.s3.region` | String | `"us-east-1"` | AWS region for the S3 bucket |
| `backup.storage.s3.access_key` | String | None | AWS access key (better set with environment variables) |
| `backup.storage.s3.secret_key` | String | None | AWS secret key (better set with environment variables) |

### Git Integration Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `backup.git.enabled` | Boolean | `false` | Whether to use Git for version control of backups |
| `backup.git.repo_url` | String | `null` | Git repository URL. Set to enable Git backup |
| `backup.git.branch` | String | `"main"` | Git branch to use |
| `backup.git.commit_message` | String | `"Updated configuration for {host}"` | Commit message format |
| `backup.git.author_name` | String | `"NetRaven"` | Git commit author name |
| `backup.git.author_email` | String | `"netraven@example.com"` | Git commit author email |

### Backup Schedule Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `backup.schedule.enabled` | Boolean | `true` | Whether to run scheduled backups |
| `backup.schedule.cron` | String | `"0 0 * * *"` | Cron expression for backup schedule (daily at midnight) |
| `backup.schedule.concurrent_jobs` | Integer | `3` | Maximum number of concurrent backup jobs |

### Device Selection Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `backup.devices.include_tags` | List | `[]` | Device tags to include in backups (empty = all) |
| `backup.devices.exclude_tags` | List | `[]` | Device tags to exclude from backups |

## Environment Variables

The following environment variables can be used to override backup settings:

| Environment Variable | Configuration Property | Description |
|----------------------|------------------------|-------------|
| `NETRAVEN_STORAGE_TYPE` | `backup.storage.type` | Storage backend type |
| `NETRAVEN_S3_BUCKET` | `backup.storage.s3.bucket` | S3 bucket name |
| `NETRAVEN_S3_PREFIX` | `backup.storage.s3.prefix` | S3 bucket prefix |
| `NETRAVEN_LOCAL_DIR` | `backup.storage.local.directory` | Local backup directory |
| `AWS_ACCESS_KEY_ID` | `backup.storage.s3.access_key` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | `backup.storage.s3.secret_key` | AWS secret key |
| `AWS_REGION` | `backup.storage.s3.region` | AWS region |

## Example Configuration

```yaml
# Backup configuration example
backup:
  # Storage backend settings
  storage:
    type: s3
    
    # Local storage settings (used if type = local)
    local:
      directory: /var/netraven/backups
    
    # S3 storage settings (used if type = s3)
    s3:
      bucket: network-device-backups
      prefix: configs/
      region: us-west-2
      # Access and secret keys should be set via environment variables
  
  # Filename format
  format: "{host}_{date}_{time}.cfg"
  
  # Git integration
  git:
    enabled: true
    repo_url: https://github.com/example/network-configs.git
    branch: main
    commit_message: "Backup for {host} at {date} {time}"
    author_name: "NetRaven Backup System"
    author_email: "backups@example.com"
  
  # Backup scheduling
  schedule:
    enabled: true
    cron: "0 0 * * *"  # Daily at midnight
    concurrent_jobs: 5
  
  # Device selection
  devices:
    include_tags:
      - production
      - core-network
    exclude_tags:
      - test
      - development
```

## Storage Options

### Local Storage

Local storage saves backups to the local filesystem. This is simple but has limitations:
- Limited by local disk space
- No built-in redundancy
- Requires separate backup of the backup files
- Simple to configure and use

### S3 Storage

Amazon S3 storage provides cloud-based storage with:
- High durability and availability
- Virtually unlimited storage
- Built-in redundancy
- Access controls and encryption
- Additional cost

## Git Integration

Git integration adds version control to your backups:
- Track changes over time
- See who made changes and when
- Roll back to previous configurations
- Collaborate with team members
- Requires Git to be installed on the system

## Security Considerations

- **Credentials**: Never store AWS credentials in configuration files. Use environment variables or instance profiles.
- **Encryption**: Consider enabling encryption for backups, especially on S3
- **Access Control**: Restrict access to backup storage to authorized personnel only
- **Audit Logging**: Enable audit logging to track access to backup files

## Best Practices

1. **Regular Backups**: Configure scheduled backups at appropriate intervals
2. **Retention Policy**: Implement a retention policy to manage backup storage
3. **Versioning**: Enable versioning in S3 or use Git integration for change tracking
4. **Testing**: Regularly test backup restoration to ensure backups are usable
5. **Monitoring**: Monitor backup jobs and storage usage 