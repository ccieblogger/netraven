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

## Development Environment

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Node.js and npm (if developing frontend without Docker)

### Setting Up Development Environment

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

```bash
# From the project root directory
docker compose up
```

This will:
- Build and start both the backend API and frontend containers
- Mount the appropriate volumes for development
- Expose the backend on port 8000 and frontend on port 8080
- Enable hot-reloading for both services

You can also use the included development script which performs some additional checks:

```bash
# Make the script executable if needed
chmod +x dev.sh

# Run the development script
./dev.sh
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

- Secure retrieval of device configurations
- Multiple storage destinations:
  - Local file storage with Git integration for version control
  - AWS S3 remote storage
- Comprehensive logging system
- Configurable backup schedules
- Secure credential management

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
   - The development environment has ESLint disabled to simplify development
   - Before building for production, enable linting and fix all issues:
   ```bash
   cd netraven/web/frontend
   npm run lint -- --fix
   ```
   
2. **Update Configuration**:
   - Modify `vue.config.js` to enable appropriate production settings
   - Set API endpoint URLs for the production environment

3. **Build and Test**:
   - Perform a local production build:
   ```bash
   npm run build
   ```
   - Verify the build outputs in the `dist` directory

For more detailed frontend deployment instructions, see the [Frontend README](netraven/web/frontend/README.md#linting-and-production-preparation).

## License

MIT
