# NetRaven Configuration Directory

This directory contains configuration files for the NetRaven application.

## Configuration Structure

The configuration is organized into subdirectories by functional area:

- **`core/`**: Core application functionality
  - `logging.yaml`: Logging configuration
  - `backup.yaml`: Backup functionality configuration
  - `security.yaml`: Security and key management configuration

- **`web/`**: Web service configuration
  - `server.yaml`: Web server settings
  - `database.yaml`: Database connection configuration
  - `api.yaml`: API-specific configuration

- **`integrations/`**: External integrations
  - `netbox.yaml`: Netbox integration configuration
  - `git.yaml`: Git repository integration
  - `notifications.yaml`: Notification systems configuration
  - `ldap.yaml`: LDAP authentication configuration

## Main Configuration File

The main configuration file is `netraven.yaml`. This file can:

1. Include other configuration files
2. Override settings from included files
3. Define additional configuration options

An example configuration file is provided as `netraven.yaml.example`.

## Configuration Loading

NetRaven loads configuration from the following locations, in order of precedence:

1. Command-line arguments
2. Environment variables
3. `netraven.yaml` file (if present)
4. Default configuration values

## Environment Variables

Sensitive information should be provided through environment variables. Environment variables override configuration file settings.

Environment variables are referenced in YAML files using the format: `${VARIABLE_NAME}`

For example:
```yaml
database:
  password: "${DB_PASSWORD}"
```

## Docker Configuration

When running in Docker, mount a volume to `/config` and provide your configuration files there.

Example:
```bash
docker run -v ./config:/config netraven/netraven:latest
```

## Creating Custom Configurations

To create a custom configuration:

1. Copy `netraven.yaml.example` to `netraven.yaml`
2. Modify the settings as needed
3. Include only the configuration files you need to override
4. Set environment variables for sensitive information

## Legacy Configuration Files

For backward compatibility, the following legacy configuration files are still supported:

- `default.yml`: Original default configuration
- `settings.yaml`: General settings file
- `key_rotation.yaml`: Key rotation settings

These files are deprecated and will be removed in a future version. Please migrate to the new configuration structure. 