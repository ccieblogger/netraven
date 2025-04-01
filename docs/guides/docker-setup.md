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

### Environment Variables

You can customize the application behavior by setting environment variables in the `docker-compose.yml` file or creating a `.env` file in the `docker` directory.

Common environment variables:

- **NETRAVEN_ENV**: Environment (prod, test, dev)
- **TOKEN_SECRET_KEY**: Secret key for JWT tokens
- **TOKEN_EXPIRY_HOURS**: JWT token expiry time
- **NETMIKO_PRESERVE_LOGS**: Whether to preserve network device session logs

### Configuration Files

NetRaven uses YAML configuration files:

- **config.yml**: Main configuration file
- **config/key_rotation.yaml**: Key rotation configuration

## Volume Data

Data is persisted in Docker volumes:

- **postgres-data**: Database files
- **api-data**: API service data
- **key_data**: Encryption keys
- **token_data**: Authentication tokens
- **logs_data**: Application logs
- **netraven_netmiko_logs**: Network device session logs

## Development with Docker

For development, the `docker-compose.override.yml` file provides development-specific settings:

- Mounts source code directories for live code editing
- Sets environment variables for testing
- Configures services for development mode

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

For more details, see the [Docker README](../../docker/README.md). 