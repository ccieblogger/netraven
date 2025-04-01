# NetRaven Docker Configuration

This directory contains all Docker-related files for the NetRaven application, including Dockerfiles for each service and Docker Compose configurations.

## Dockerfiles

The following Dockerfiles define the container images for each service:

- **Dockerfile.main**: Main application container
- **Dockerfile.api**: Backend API service container
- **Dockerfile.gateway**: Device Gateway service container
- **key-rotation.Dockerfile**: Key rotation service container

## Docker Compose Configuration

The Docker Compose configuration files define the multi-container deployment:

- **docker-compose.yml**: Main Docker Compose configuration with all services
- **docker-compose.override.yml**: Override configuration for development/testing

## Docker Services

### API Service

The API service (`Dockerfile.api`) provides the primary backend functionality:

- REST API endpoints for all application features
- Database interaction
- Authentication and authorization
- Scheduled job management

### Device Gateway

The Device Gateway service (`Dockerfile.gateway`) handles network device interactions:

- Secure communication with network devices
- Command execution and configuration retrieval
- Credential management and encryption
- Device session pooling and management

### Frontend

The Frontend service (defined in `docker-compose.yml`) provides the user interface:

- Vue.js-based SPA
- Responsive design for desktop and mobile access
- API integration
- User authentication flow

### Scheduler

The Scheduler service (defined in `docker-compose.yml`) manages background tasks:

- Scheduled backup jobs
- Key rotation
- Maintenance operations
- Alert and notification delivery

### Key Rotation

The Key Rotation service (`key-rotation.Dockerfile`) manages encryption keys:

- Automatic key rotation
- Secure key storage
- Encryption key management

## Running with Docker Compose

To start the entire application stack:

```bash
cd docker
docker-compose up -d
```

To start a specific service:

```bash
cd docker
docker-compose up -d api
```

To view logs:

```bash
cd docker
docker-compose logs -f
```

## Volumes

The Docker Compose configuration defines several volumes for persistent data:

- **postgres-data**: PostgreSQL database files
- **logs_data**: Application logs
- **token_data**: Authentication tokens
- **api-data**: API service data
- **key_data**: Encryption keys
- **netraven_netmiko_logs**: Network device session logs

## Networks

All services are connected through the `netraven-network` bridge network.

## Environment Variables

Key environment variables that can be configured:

- **NETRAVEN_ENV**: Environment (prod, test, dev)
- **TOKEN_SECRET_KEY**: Secret key for JWT tokens
- **TOKEN_EXPIRY_HOURS**: JWT token expiry time
- **NETMIKO_PRESERVE_LOGS**: Whether to preserve network device session logs 