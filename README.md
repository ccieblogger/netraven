# NetRaven

A Python-based tool for automated backup of Cisco network device configurations to multiple storage destinations.

## Description

This tool securely connects to Cisco network devices (routers, switches, firewalls, and WLCs), retrieves their running configurations, and backs them up to various storage destinations. It currently supports local file storage with Git integration for version control and AWS S3 remote storage for cloud backup.

## Project Structure

The project is organized into the following components:

```
netraven/
├── core/                      # Core functionality
│   ├── device_comm.py         # Device communication
│   ├── storage.py             # Storage backends (Local, S3)
│   └── ...                    # Other core modules
├── web/                       # Web interface
│   ├── backend/               # FastAPI backend
│   │   ├── app/               # Application code
│   │   │   ├── api/           # API endpoints
│   │   │   ├── core/          # Backend core modules
│   │   │   ├── db/            # Database models
│   │   │   ├── schemas/       # Pydantic schemas
│   │   │   └── storage/       # Storage adapters
│   │   └── ...                # Backend files
│   └── frontend/              # Vue.js frontend
│       ├── src/               # Frontend source
│       └── ...                # Frontend files
```

## Environment Setup

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Node.js and npm (if developing frontend without Docker)

### Setting Up Your Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/netraven.git
   cd netraven
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

### Running the Application

#### Using Docker Compose (Recommended)

The easiest way to run the complete NetRaven environment is using Docker Compose:

To start the application:

```bash
# Start all services
docker compose up

# Or to run in the background
docker compose up -d
```

#### Testing Authentication

For testing authentication, we provide a script to create an admin user:

```bash
# Run from the project root
python3 scripts/create_admin.py [username] [password] [email]
```

By default, this creates a user with:
- Username: admin
- Password: adminpass123
- Email: admin@example.com

You can then use these credentials to log in through the frontend interface.

#### Manual Setup (Alternative)

If you prefer not to use Docker, you can:

1. Start the API server:
   ```bash
   # Make sure you're in the virtual environment
   source venv/bin/activate
   
   # Install dependencies if needed
   pip install -e .
   
   # Start the FastAPI server
   uvicorn netraven.web:app --reload --port 8000
   ```

2. Start the frontend (in a separate terminal):
   ```bash
   # Navigate to the frontend directory
   cd netraven/web/frontend
   
   # Install dependencies
   npm install
   
   # Start the development server
   npm run serve
   ```

### Accessing the Application

Once running, you can access:
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- API OpenAPI Spec: http://localhost:8000/openapi.json

## Components

### Core

The core package provides the fundamental functionality for:
- Connecting to network devices
- Retrieving configurations
- Storing backups in various backends (local filesystem, S3)

### Web Interface

The web interface provides:
- REST API for managing devices, jobs, and backups
- User authentication and authorization
- Scheduled backup jobs
- Modern UI for configuration and monitoring

## Features

- **Device Management**: Add, edit, and organize network devices
- **Configuration Backup**: Automated backup of device configurations
- **Scheduled Jobs**: Schedule recurring backup and command execution tasks
- **Job Logging**: Comprehensive logging of all operations
- **Tag-based Organization**: Organize devices with tags and tag rules
- **Device Gateway**: Secure gateway for device communication with metrics collection

## Architecture

NetRaven consists of several components:

1. **Web API**: FastAPI-based REST API for device management and job control
2. **Scheduler**: Background service for executing scheduled jobs
3. **Device Gateway**: Secure gateway for device communication
4. **Frontend**: Vue.js-based web interface
5. **Database**: PostgreSQL database for storing device information, backups, and logs

## Gateway Integration

NetRaven includes a Device Gateway service that provides a secure way to communicate with network devices. The gateway offers several benefits:

- **Centralized Access**: All device connections go through a single point, simplifying security management
- **Metrics Collection**: Comprehensive metrics on device connections, commands, and errors
- **Secure API**: JWT-based authentication for secure access
- **Scheduler Integration**: Seamless integration with the job scheduling system

### Gateway Configuration

The gateway can be configured in the `config.yml` file:

```yaml
gateway:
  url: http://localhost:8001
  api_key: your-api-key-here
  use_by_default: false
  connect_timeout: 30
  command_timeout: 60
  max_retries: 3
  retry_delay: 5
```

### Using the Gateway

To use the gateway for device operations:

1. Ensure the gateway service is running
2. Set `use_by_default: true` in the config or use the `--use-gateway` flag with the scheduler
3. Monitor gateway metrics through the web interface at `/gateway`

### Gateway API

The gateway provides the following API endpoints:

- `/health`: Health check endpoint
- `/status`: Gateway status information
- `/metrics`: Detailed metrics about gateway operations
- `/check-device`: Check device connectivity
- `/connect`: Connect to a device
- `/execute`: Execute a command on a device
- `/backup`: Backup device configuration

## Logging System

NetRaven includes a sophisticated logging system with the following features:

### Component-Specific Logging
- **Frontend Logs**: Dedicated log files for frontend-related events (`logs/frontend.log`)
- **Backend Logs**: API and backend server logs (`logs/backend.log`)
- **Authentication Logs**: Security-related authentication events (`logs/auth.log`)
- **Jobs Logs**: Scheduled backup tasks and operations (`logs/jobs.log`)
- **Main Application Log**: Comprehensive log of all activities (`logs/netraven.log`)

### Log Rotation
NetRaven supports two types of log rotation:

1. **Size-based Rotation** (Default)
   - Logs rotate when they reach a specified size (default: 10MB)
   - Configurable number of backup files to keep (default: 5)

2. **Time-based Rotation**
   - Rotate logs based on time intervals (hourly, daily, midnight, weekly)
   - Configurable in `config.yml` by setting `rotation_when` and `rotation_interval`
   - Example for daily rotation at midnight:
     ```yaml
     logging:
       file:
         rotation_when: midnight
         rotation_interval: 1
     ```

### Advanced Features
- **JSON Structured Logging**: Optional JSON-formatted logs for integration with log analysis tools
- **Sensitive Data Redaction**: Automatic redaction of passwords and other sensitive information
- **Configurable Log Levels**: Different verbosity levels for console and file outputs

### Testing Log Rotation

To test and demonstrate log rotation, you can use the included script:
```bash
# Test time-based rotation (rotates logs every minute)
python scripts/test_time_rotation.py
```

## Requirements

- Python 3.10+
- Required Python packages (see requirements.txt)
- Git (for local version control)
- AWS credentials (for S3 storage)

## Production Deployment Preparation

Before deploying NetRaven to production, ensure you complete the following checklist:

### Backend Preparation
1. **Update Configuration**: Set production-appropriate values in configuration files
2. **Database Migrations**: Ensure all migrations are applied
3. **Security Review**: Validate that JWT secret keys and other sensitive information are securely managed

### Frontend Preparation
1. **Resolve Linting Issues**: 
   - Run ESLint and fix any issues:
   ```bash
   cd netraven/web/frontend
   npm run lint -- --fix
   ```
   
2. **Update Configuration**:
   - Modify `vue.config.js` to enable appropriate settings
   - Set API endpoint URLs in the environment configuration

3. **Build and Test**:
   - Perform a local production build:
   ```bash
   npm run build
   ```
   - Verify the build outputs in the `dist` directory

For more detailed frontend deployment instructions, see the [Frontend README](netraven/web/frontend/README.md#linting-and-production-preparation).

## Documentation

NetRaven includes comprehensive documentation to help you get started, understand the system architecture, and troubleshoot issues:

- [Project Specifications](docs/project-specs.md): Detailed project goals and requirements
- [Device Communication](docs/device_communication.md): How NetRaven communicates with network devices
- [Logging System](docs/logging.md): Information about the logging infrastructure
- [Web Frontend Design](docs/web-frontend-design.md): Frontend architecture and component design
- [Troubleshooting Guide](docs/troubleshooting.md): Solutions for common issues, authentication setup, and verification steps

## License

MIT

## Default Admin Credentials

When NetRaven is first installed, a default admin user is created with the following credentials:

- **Username**: admin
- **Password**: NetRaven

For security reasons, we strongly recommend changing this password after your first login.

## Emergency Password Reset

If you lose access to the admin account, an emergency password reset script is provided:

```bash
python scripts/reset_admin_password.py
```

This will reset the admin password back to the default "NetRaven". This script should only be used as an emergency measure to regain access to the system.

**Security Note**: This script should be kept secure and only accessible to authorized personnel. After using it, immediately change the admin password.

## Database Migrations

NetRaven uses Alembic for database migrations. Migrations are automatically run when the application containers start up.

### Running Migrations

Migrations are handled automatically when you start the application with Docker Compose:

```bash
docker-compose up
```

The API container will run the migrations before starting the API service.

### Creating New Migrations

To create a new migration:

1. Make changes to the SQLAlchemy models in the application
2. Generate a new migration script:

```bash
# From the project root
docker-compose exec api alembic -c netraven/web/migrations/alembic.ini revision --autogenerate -m "Description of changes"
```

3. Review the generated migration script in `netraven/web/migrations/versions/`

For more details, see the [migrations README](netraven/web/migrations/README.md).

## Authentication

NetRaven supports two authentication methods:

### JWT Token Authentication

For user-based authentication, NetRaven uses JWT (JSON Web Token) authentication. This is primarily used for the web interface and API access by users.

To obtain a token:

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=NetRaven"
```

### API Key Authentication

For service-to-service communication, NetRaven supports API key authentication. This is useful for integrating with other systems or for automated scripts.

Use the API key in the `X-API-Key` header:

```bash
curl -X GET http://localhost:8000/api/health \
  -H "X-API-Key: netraven-api-key"
```

The default API key is `netraven-api-key`, which can be changed in the configuration or by setting the `NETRAVEN_API_KEY` environment variable in the `docker-compose.yml` file.

For more detailed API documentation, see [API Documentation](docs/api.md).
