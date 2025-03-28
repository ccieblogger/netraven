# NetRaven Installation Guide

## Introduction

This guide provides step-by-step instructions for installing and running the NetRaven network management platform.

## Purpose

By following this guide, you will be able to:
- Set up NetRaven in a Docker environment (recommended)
- Configure the database
- Create an admin user
- Alternatively, install NetRaven manually

## Prerequisites

Before proceeding, ensure you have:

- **Git** (for cloning the repository)
- **Docker** and **Docker Compose** (for containerized installation)
- **Python 3.10+** (for manual installation only)

## Docker Installation (Recommended)

NetRaven is designed to be run as a containerized application, which simplifies deployment and ensures consistency across environments.

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/netraven.git
cd netraven
```

### Step 2: Start the Application

```bash
docker compose up -d
```

> **Note**: The `-d` flag runs containers in the background. Omit it if you want to see the logs in your terminal.

### Step 3: Access the Application

Once the containers are running, you can access:

- **Frontend UI**: [http://localhost:8080](http://localhost:8080)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### Container Architecture

The Docker Compose setup includes the following services:

| Service | Description | Port |
|---------|-------------|------|
| Frontend | Vue.js web application | 8080 |
| API | FastAPI backend service | 8000 |
| Gateway | Device communication service | 8001 |
| PostgreSQL | Database for persistent storage | 5432 |
| Scheduler | Background job service | - |

## Database Configuration

### Default Configuration

By default, NetRaven uses PostgreSQL with the following configuration:

- **Database name**: netraven
- **Username**: netraven
- **Password**: netraven
- **Port**: 5432 (mapped to host)
- **Data storage**: Docker volume `postgres-data`

No additional configuration is needed when using the default Docker Compose setup.

### Using an External Database

To connect to an external PostgreSQL database:

1. Update the `config.yml` file:

```yaml
web:
  database:
    type: postgres
    postgres:
      host: your_postgres_host
      port: 5432
      database: your_database_name
      user: your_username
      password: your_password
```

2. If using Docker, update the environment variables in `docker-compose.yml`:

```yaml
environment:
  - DATABASE_URL=postgresql://your_username:your_password@your_postgres_host:5432/your_database_name
```

### Database Migrations

The application automatically applies database migrations on startup. To manually check the database:

```bash
# Check database connection and view schema
python3 scripts/db_check.py

# Initialize database tables if needed
python3 scripts/db_check.py --init
```

## Creating an Admin User

After installation, you need to create an admin user to access the system:

```bash
# Using Docker
docker exec -it netraven-api-1 python scripts/create_admin.py

# Without Docker (from project root)
python scripts/create_admin.py
```

This creates a user with default credentials:
- **Username**: admin
- **Password**: adminpass123
- **Email**: admin@example.com

To customize the admin user:

```bash
docker exec -it netraven-api-1 python scripts/create_admin.py my_username my_password my_email@example.com
```

## Manual Installation

If you prefer not to use Docker, follow these steps for a manual installation:

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/netraven.git
cd netraven
```

### Step 2: Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -e .
```

### Step 4: Start the Backend API

```bash
uvicorn netraven.web:app --reload --port 8000
```

### Step 5: Start the Frontend (in a separate terminal)

```bash
cd netraven/web/frontend
npm install
npm run serve
```

## Troubleshooting

### Docker Issues

- **WSL Path Errors**: When using WSL, ensure you're using Linux paths, not Windows UNC paths
- **Permission Issues**: Docker containers run as user 1001 - ensure your host directories have appropriate permissions
- **Port Conflicts**: If ports 8000 or 8080 are in use, modify the port mappings in docker-compose.yml
- **Missing Dependencies**: For missing modules, install them in the container:
  ```bash
  docker exec -it netraven-api-1 pip install <package-name>
  ```

### Frontend Issues

- **ESLint Errors**: Run `npm run lint -- --fix` to address linting issues
- **Node Module Issues**: Try deleting node_modules and running `npm install` again
- **Login Issues**: Check the API URL configuration in the environment variables

### Backend Issues

- **Database Connection**: Ensure database credentials are correct in config.yml
- **API Errors**: Check logs with `docker logs netraven-api-1`

## Next Steps

After installation:

- Follow the [Quick Start Guide](./quick-start.md) to set up your first device
- Configure [Initial Setup](./initial-setup.md) for production use
- Explore the [User Guide](../user-guide/) for detailed usage instructions

## Related Documentation

- [Deployment Guide](../deployment/docker-deployment.md)
- [Configuration Reference](../reference/configuration-options.md)
- [Troubleshooting Guide](../deployment/troubleshooting.md) 