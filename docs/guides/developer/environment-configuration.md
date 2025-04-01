# Environment Configuration Guide

This guide explains how to configure NetRaven for different environments (development, testing, production) and provides best practices for environment-specific configuration management.

## Environment Types

NetRaven recognizes the following environment types:

1. **Production** - Default environment for deployed systems
2. **Development** - Local development environment with debugging features
3. **Test** - Automated testing environment with test-specific overrides

The environment is determined by the `NETRAVEN_ENV` environment variable, which can be set to:
- `production` (default if not specified)
- `development`
- `test` or `testing`

## Setting the Environment

### Command Line

```bash
# Linux/macOS
export NETRAVEN_ENV=development

# Windows (Command Prompt)
set NETRAVEN_ENV=development

# Windows (PowerShell)
$env:NETRAVEN_ENV = "development"
```

### Docker Compose

In `docker-compose.yml` or `docker-compose.override.yml`:

```yaml
services:
  api:
    environment:
      - NETRAVEN_ENV=development
```

### Configuration Files

You can create environment-specific configuration files with naming patterns:

- `config.{environment}.yml` (e.g., `config.development.yml`)
- `config/{component}.{environment}.yml` (e.g., `config/web.development.yml`)

## Environment-Specific Behavior

### Production Environment

The production environment (`NETRAVEN_ENV=production`):

- Disables debug mode
- Uses production-level logging (typically INFO level)
- Enforces stricter security settings
- Optimizes for performance over debugging

### Development Environment

The development environment (`NETRAVEN_ENV=development`):

- Enables debugging features
- Uses development-level logging (typically DEBUG level)
- May relax certain security settings for easier development
- Provides more detailed error information

### Test Environment

The test environment (`NETRAVEN_ENV=test` or `NETRAVEN_ENV=testing`):

- Automatically applies test-specific overrides from `TEST_CONFIG_OVERRIDES`
- Sets shorter token expiration times
- Enables debug mode
- Disables file logging (logs to console only)
- Uses DEBUG log level

## Environment-Specific Configuration Files

For better organization, you can create environment-specific configuration files:

```
config/
├── default.yml           # Default settings for all environments
├── development.yml       # Development-specific overrides
├── production.yml        # Production-specific overrides
├── test.yml              # Test-specific overrides
└── components/           # Component-specific configuration
    ├── web.default.yml   # Default web settings
    ├── web.development.yml # Development web settings
    └── web.production.yml  # Production web settings
```

## Configuration Precedence

When using environment-specific configuration, the precedence order (from highest to lowest) is:

1. Environment variables
2. Command-line specified configuration file
3. Environment-specific configuration file (e.g., `config.{environment}.yml`)
4. Default configuration file (e.g., `config.yml`)
5. Default values in code

## Development Best Practices

### Local Development

For local development:

1. Create a `config.development.yml` file for your local settings
2. Set `NETRAVEN_ENV=development` in your shell or IDE
3. Add local development settings to `.gitignore` to avoid committing personal settings

Example `.gitignore` entry:
```
config.development.yml
config/development.yml
config/*.development.yml
```

### Environment Variables vs. Configuration Files

- **Environment Variables**: Better for:
  - Deployment-specific settings
  - CI/CD pipelines
  - Containerized environments
  - Secrets and credentials

- **Configuration Files**: Better for:
  - Complex configuration structures
  - Defaults and templates
  - Settings that require documentation
  - Developer-specific customizations

### Docker Development Environment

When developing with Docker:

1. Use `docker-compose.override.yml` for development-specific service settings
2. Mount local configuration files as volumes
3. Set environment variables in the Docker Compose file

Example `docker-compose.override.yml` for development:

```yaml
services:
  api:
    environment:
      - NETRAVEN_ENV=development
      - DEBUG=true
    volumes:
      - ./config.development.yml:/app/config.yml
```

## Testing Environment Configuration

For testing:

1. Set `NETRAVEN_ENV=test` in your testing setup
2. Create test-specific configuration in `config.test.yml` if needed
3. Use the built-in `TEST_CONFIG_OVERRIDES` for commonly changed test settings

NetRaven automatically applies these test overrides:

```python
TEST_CONFIG_OVERRIDES = {
    "web": {
        "authentication": {
            "token_expiration": 3600,  # Shorter expiration for tests (1 hour)
        },
        "debug": True
    },
    "logging": {
        "level": "DEBUG",
        "file": {
            "enabled": False  # Disable file logging in tests
        }
    }
}
```

## Production Environment Configuration

For production environments:

1. Use environment variables for sensitive information
2. Minimize configuration file changes between deployments
3. Validate all configuration before deployment
4. Consider using a secrets management solution

## Checking the Current Environment

To check which environment is currently active, you can use:

```python
from netraven.core.config import get_env, is_test_env

# Get the current environment
env = get_env()  # Returns 'production', 'development', or 'test'

# Check if in test environment
if is_test_env():
    # Do test-specific logic
``` 