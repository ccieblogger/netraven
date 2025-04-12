## NetRaven Architecture

### Executive Summary

This document outlines the complete architecture for NetRaven, a network device configuration backup system designed for deployment in customer environments. NetRaven retrieves and stores device configurations for auditing, historical tracking, and operational assurance. The system prioritizes simplicity, testability, and maintainability, while still supporting targeted concurrency for tasks like device polling.

### System Overview

NetRaven supports:
1. Retrieval of running configuration and identifying information from network devices (primarily via SSH).
2. Storing configuration snapshots in a Git repository for version control.
3. Job scheduling for one-time or recurring configuration backups.
4. REST API access for external integrations.
5. Role-based web UI for inventory management and job monitoring.

The system is installed locally using Python-based services with PostgreSQL and Redis. The directory structure and service boundaries support future containerization but do not require it.

### Core Architectural Principles
- **Synchronous-First Design**: Synchronous services simplify development and debugging.
- **Targeted Concurrency**: Uses threads only where concurrency offers clear benefits (e.g., connecting to multiple devices).
- **Modular Design**: Isolated services for API, job scheduling, communication, and logging.
- **Detailed Logging**: Per-device and per-job logs with redacted and raw entries.
- **Secure by Default**: JWT authentication and role-based access controls.

### Core Services

#### 1. API Service (FastAPI - Sync Mode)
- Exposes REST API endpoints for all system functions.
- JWT-based authentication with role enforcement (admin/user).
- CRUD for:
  - Devices
  - Device groups (tags)
  - Jobs
  - Users and roles
- Status endpoints for job monitoring.

#### 2. Device Communication Worker
- Executes device jobs triggered by scheduler or on demand.
- Connects to network devices using **Netmiko**.
- Retrieves `show running-config` and basic facts (hostname, serial number).
- Uses `ThreadPoolExecutor` for concurrent device access (default: 5).
- Reports logs and results to database.

#### 3. Job Scheduler
- Based on **RQ + RQ Scheduler**.
- Queues and schedules jobs:
  - One-time
  - Recurring (daily, weekly, monthly)
  - With start/end window support
- Triggers device communication jobs in the background.

#### 4. PostgreSQL Database
- Stores all persistent data:
  - Devices, jobs, logs
  - Credentials (encrypted)
  - User accounts and roles
  - System configuration
- Managed with **SQLAlchemy (sync)** + **Alembic**.

#### 5. Frontend UI (Vue 3)
- Built with **Vue 3 (using Vite)** for responsive user experience.
- Integrates via REST API.
- Supports:
  - Device inventory views
  - Job creation and monitoring
  - User settings and preferences
  - Log inspection

### Device Communication
- Primary protocol: **SSH via Netmiko**
- Vendor extensibility via Netmiko platform mapping
- Device grouping (tags) determines credential selection
- Detailed logs include:
  - Start/end time
  - Auth failures
  - Unreachable device errors
  - Output with sensitive line redaction

### Authentication & Authorization
- JWT-based access for both API and UI users
- Admin and user roles
- Users can be assigned visibility to specific device groups

### Configuration Management
- Hierarchical loading:
  1. Environment variables
  2. Admin-set values from DB
  3. YAML files in `/config/`
- All components read configuration via a common loader

### Git Integration
- Config files committed to local Git repo per job
- Commit messages include timestamp, job ID, device
- Diffs and history available via Git

### Deployment

#### Traditional Deployment
NetRaven is intended to be installed and run locally using Python and system packages. Each component can be launched individually via CLI or system service manager.

- PostgreSQL and Redis are assumed to be locally installed (can later be containerized)
- System services can be managed via `systemd`, `supervisord`, or developer CLI runners
- Frontend runs with standard **Vite/Node.js** tooling

#### Containerized Deployment
NetRaven now supports containerized deployment using Docker and Docker Compose for easier setup and consistent environments:

- **Available Containers**:
  - Frontend (Vue 3 UI)
  - API (FastAPI service)
  - PostgreSQL (database)
  - Redis (queue and caching)

- **Development Environment**:
  ```bash
  # Start all services in development mode
  docker-compose up -d
  
  # Start just the API service
  ./setup/build_api_container.sh
  
  # Rebuild and start API service
  ./setup/build_api_container.sh --rebuild
  ```

- **Production Environment**:
  ```bash
  # Start all services in production mode
  docker-compose -f docker-compose.prod.yml up -d
  
  # Start just the API service in production mode
  ./setup/build_api_container.sh --env prod
  ```

- **Environment Configuration**:
  - Development: `.env.dev` file and `dev.yaml` configuration
  - Production: `.env.prod` file and `prod.yaml` configuration

### Testing Strategy
- **Unit Tests**: Business logic, validation, utilities
- **Integration Tests**: DB transactions, API/worker behavior
- **E2E Tests**: Simulate full workflows from API → device → Git → UI
- Test database with Alembic-migrated schemas
- Threaded jobs tested for isolation, timing, logging

### Directory Structure
```
/netraven/
├── api/                  # FastAPI routes and schemas
├── worker/               # Device job execution logic
├── scheduler/            # RQ + scheduling logic
├── db/                   # SQLAlchemy models and session mgmt
├── config/               # YAML and loader logic
├── frontend/             # **Vue 3** app (separate build pipeline)
├── git/                  # Git repository interface
├── tests/                # Unit, integration, and E2E tests
└── utils/                # Shared helpers
```

---

