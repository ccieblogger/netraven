# Docker Setup Guide

NetRaven is designed to run as a set of Docker containers managed by Docker Compose. This guide explains how to use the Docker setup.

## Docker Directory Structure

All Docker-related files are located in the `/docker` directory:

```
docker/
├── Dockerfile.main            # Main application Dockerfile
├── Dockerfile.api             # API service Dockerfile
├── Dockerfile.gateway         # Device Gateway Dockerfile
├── key-rotation.Dockerfile    # Key rotation service Dockerfile
├── docker-compose.yml         # Main Docker Compose configuration
├── docker-compose.override.yml # Development/test overrides
├── nginx/                     # Nginx configuration for web server
└── README.md                  # Docker documentation
```

## Services

The Docker Compose setup includes the following services:

- **postgres**: PostgreSQL database
- **api**: Backend API service
- **scheduler**: Job scheduler service
- **device_gateway**: Device connectivity service
- **frontend**: Web UI
- **nginx**: Web server and reverse proxy
- **key-rotation**: Encryption key rotation service

## Running the Application

### Starting All Services

To start the entire application stack:

```bash
cd docker
docker-compose up -d
```

The `-d` flag runs the containers in detached mode (background).

### Starting Specific Services

To start only specific services:

```bash
cd docker
docker-compose up -d api device_gateway
```

### Viewing Logs

To view logs from all services:

```bash
cd docker
docker-compose logs -f
```

To view logs from a specific service:

```bash
cd docker
docker-compose logs -f api
```

### Stopping Services

To stop all services:

```bash
cd docker
docker-compose down
```

To stop and remove volumes (caution: this will delete data):

```bash
cd docker
docker-compose down -v
```

## Configuration

NetRaven's Docker setup provides flexible configuration options through both configuration files and environment variables.

### Configuration Files

NetRaven uses YAML configuration files that are mounted into the containers:

| File | Purpose | Container Mount Point |
|------|---------|----------------------|
| `config.yml` | Main application configuration | `/app/config.yml` |
| `config/key_rotation.yaml` | Key rotation service configuration | Set via `CONFIG_FILE` env var |

The standard Docker Compose setup includes these volume mappings:

```yaml
volumes:
  - ./config.yml:/app/config.yml
```

### Environment Variables

You can customize the application behavior by setting environment variables in the `docker-compose.yml` file or creating a `.env` file in the `docker` directory.

#### Key Environment Variables

| Environment Variable | Purpose | Default |
|----------------------|---------|---------|
| `NETRAVEN_ENV` | Environment (production, development, test) | `production` |
| `NETRAVEN_ENCRYPTION_KEY` | Key for encrypting sensitive data | None (Required) |
| `TOKEN_SECRET_KEY` | Secret key for JWT tokens | None (Required) |
| `NETRAVEN_WEB_DATABASE_TYPE` | Database type | `postgres` |
| `NETRAVEN_WEB_DATABASE_HOST` | Database hostname | `postgres` |
| `NETRAVEN_LOG_LEVEL` | Logging level | `INFO` |

For a comprehensive list of all supported environment variables, see the [Environment Variables Reference](../../reference/environment-variables.md).

### Configuration Precedence

Configuration values are applied in the following order (highest precedence first):

1. Environment variables specified in Docker Compose
2. Config file mounted as a volume
3. Default values in code

### Environment-Specific Configuration

For development and testing environments:

1. Set `NETRAVEN_ENV=development` or `NETRAVEN_ENV=test` in your environment variables
2. Create an environment-specific configuration file (e.g., `config.development.yml`)
3. Use `docker-compose.override.yml` for development-specific settings

For more details on environment-specific configuration, see the [Environment Configuration Guide](../developer/environment-configuration.md).

## Volume Data

Data is persisted in Docker volumes:

- **postgres-data**: Database files
- **api-data**: API service data
- **key_data**: Encryption keys
- **token_data**: Authentication tokens
- **logs_data**: Application logs
- **netraven_netmiko_logs**: Network device session logs

### Volume Backup and Restore

To backup volumes:

```bash
docker volume create backup_volume
docker run --rm -v postgres-data:/source -v backup_volume:/backup alpine tar -czf /backup/postgres-data.tar.gz -C /source .
```

To restore volumes:

```bash
docker run --rm -v backup_volume:/backup -v postgres-data:/target alpine sh -c "cd /target && tar -xzf /backup/postgres-data.tar.gz"
```

## Development with Docker

For development, the `docker-compose.override.yml` file provides development-specific settings:

- Mounts source code directories for live code editing
- Sets environment variables for testing
- Configures services for development mode

### Hot-Reload Development

For hot-reload development:

```yaml
# docker-compose.override.yml
services:
  api:
    volumes:
      - ../netraven:/app/netraven
    environment:
      - NETRAVEN_ENV=development
      - NETRAVEN_WEB_DEBUG=true
```

## Rebuilding Containers

After making changes to Dockerfiles or dependencies, rebuild the containers:

```bash
cd docker
docker-compose build
```

To rebuild a specific service:

```bash
cd docker
docker-compose build api
```

## Accessing Services

- **Frontend**: http://localhost:80 or http://localhost
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Device Gateway**: http://localhost:8001

## Common Issues

### Database Connection Issues

If the API service cannot connect to the database:

1. Check if the PostgreSQL container is running:
   ```bash
   docker-compose ps postgres
   ```

2. Verify database logs:
   ```bash
   docker-compose logs postgres
   ```

### Permission Issues

If you encounter permission issues with mounted volumes:

1. Check the permissions on the host directories
2. Ensure the container user has access to the mounted volumes

### Container Health Check Failures

If containers fail health checks:

1. Check service logs for errors
2. Verify container network connectivity
3. Ensure required services are running

### Configuration Issues

If you experience configuration-related issues:

1. Verify your configuration file is correctly mounted
2. Check environment variables are correctly set
3. Ensure configuration values are appropriate for the environment
4. Look for configuration errors in the service logs

For more details on configuration options, see the [Configuration Reference](../../reference/configuration.md).

For more details on Docker setup, see the [Docker README](../../docker/README.md). 