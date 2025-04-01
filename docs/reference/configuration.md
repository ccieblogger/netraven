# Configuration Reference

## Overview

NetRaven uses a flexible configuration system that supports multiple configuration sources, environment-specific settings, and hierarchical overrides. This document provides a comprehensive reference for the configuration system and available options.

## Configuration Files

The main configuration files used by NetRaven are:

| File | Purpose | Status |
|------|---------|--------|
| `/config.yml` | Main application configuration | Primary configuration file |
| `/config/netraven.yaml` | Alternative main configuration | Alternative to root config.yml |
| `/config/default.yml` | Default settings for backup and logging | Fallback defaults |
| `/config/key_rotation.yaml` | Key rotation and security settings | Used by key rotation service |
| `/config/settings.yaml` | Various system settings | General settings |
| `/config/credentials.yaml` | Sensitive credential information | Created locally (gitignored) |
| `/config/custom.yml` | User-specific customizations | Created locally (gitignored) |

## Configuration Loading

NetRaven loads configuration from multiple sources in the following order of precedence (highest to lowest):

1. **Environment Variables**: Override individual settings
2. **User-specified Configuration File**: Specified via command line or `NETRAVEN_CONFIG` environment variable
3. **Standard Configuration Locations**:
   - Path specified in `NETRAVEN_CONFIG` environment variable
   - `./config.yml` in the current directory
   - `~/.config/netraven/config.yml` in the user's home directory
   - `/etc/netraven/config.yml` for system-wide configuration
4. **Default Configuration Values**: Defined in `netraven/core/config.py`

## Configuration Categories

The configuration is organized into the following categories:

### Core Settings

Basic application settings including paths, encryption, and job configuration.

[View Core Settings Reference](configuration/core.md)

### Web Service Settings

Web server configuration, API settings, authentication, and database connection.

[View Web Settings Reference](configuration/web.md)

### Logging Configuration

Logging levels, formats, file locations, rotation, and sensitive data filtering.

[View Logging Settings Reference](configuration/logging.md)

### Backup Settings

Device configuration backup storage, formats, and Git integration.

[View Backup Settings Reference](configuration/backup.md)

### Security Settings

Authentication, encryption, key rotation, and other security-related settings.

[View Security Settings Reference](configuration/security.md)

### Integration Settings

Third-party integrations including Netbox, Git, and other external systems.

[View Integration Settings Reference](configuration/integrations.md)

## Environment-Specific Configuration

NetRaven supports environment-specific configuration using the `NETRAVEN_ENV` environment variable. The following environments are recognized:

- `production` (default)
- `development`
- `test`

Setting this environment variable will affect default values and behavior in various components. For test environments, a specific set of overrides (`TEST_CONFIG_OVERRIDES`) is automatically applied.

For detailed information on configuring for different environments, see the [Environment Configuration Guide](../guides/developer/environment-configuration.md).

## Environment Variables

NetRaven supports numerous environment variables for configuration override. These are particularly useful in containerized environments.

For a complete list of supported environment variables, see the [Environment Variables Reference](environment-variables.md).

## Configuration in Docker

When running NetRaven in Docker, configuration files are typically mounted as volumes. The standard Docker setup in `docker-compose.yml` maps the following configuration files:

- `./config.yml:/app/config.yml` for the main services
- `CONFIG_FILE=config/key_rotation.yaml` for the key rotation service

For more details on Docker configuration, see the [Docker Setup Guide](../guides/docker-setup.md).

## Configuration Best Practices

### Security Considerations

- Never commit sensitive information (passwords, tokens, keys) to version control
- Use environment variables for sensitive settings in production
- Consider using a secrets management solution for production environments

### Configuration Organization

- Use the main `config.yml` for application-wide settings
- Use component-specific files for detailed configuration
- Create environment-specific configuration files when needed

### Default Values

Most configuration options have sensible default values defined in the codebase. When in doubt, consult the specific component reference or check the default values in `netraven/core/config.py`.

## Debugging Configuration

If you suspect configuration issues, you can enable debug-level logging for the configuration module:

```python
import logging
logging.getLogger('netraven.core.config').setLevel(logging.DEBUG)
```

You can also dump the loaded configuration for inspection:

```python
from netraven.core.config import get_config
import json
print(json.dumps(get_config(), indent=2))
``` 