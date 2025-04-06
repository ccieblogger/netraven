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

#### 5. Frontend UI (React)

- Built with React for responsive user experience.
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

NetRaven uses a local Git repository as the versioned storage backend for device configuration files. This approach offers simplicity, traceability, and built-in change tracking with minimal infrastructure overhead.

- Each configuration snapshot is saved as a text file and committed to a local Git repository.
- Commit messages include structured metadata such as job ID, device hostname, and timestamp.
- Git provides built-in versioning, rollback, and readable diffs to show changes between snapshots.
- The Git repository is stored in a dedicated project folder (e.g., `/data/git-repo/`) and initialized on first use.
- GitPython is used to interface with the repository programmatically.

This design avoids the need for an external version control system while ensuring historical tracking and auditability of all config changes. It also complements the relational database, which stores job metadata and connection logs.

### Deployment

NetRaven uses a monorepo structure and is designed for local installation using Python with [Poetry](https://python-poetry.org/) for dependency management. All services share a unified environment and can be run individually using developer scripts.

- PostgreSQL 14 and Redis 7 are installed locally using scripts provided in the `/setup/` directory. Containerization is not required and not used by default
- Developer runner scripts for DB schema creation, job execution, and job debugging live in `/setup/`
- Each service lives under the `netraven/` namespace and is importable as `netraven.api`, `netraven.worker`, etc.
- The root `pyproject.toml` file governs dependencies across the system

```
/netraven/
├── api/          # FastAPI service
├── worker/       # Device command execution logic
├── scheduler/    # RQ-based job scheduler
├── db/           # SQLAlchemy models and session mgmt
├── config/       # YAML and env-based config
├── git/          # Git commit logic
├── frontend/     # React app (built separately)
├── setup/        # Developer runners and bootstrap scripts
├── tests/        # Tests organized by feature
├── pyproject.toml
└── poetry.lock
```

### Development Environment

It is strongly encouraged to use a python virtual environment to install and run this application.

```
python3 -m venv venv

```


### Testing Strategy

- **Unit Tests**: Business logic, validation, utilities
- **Integration Tests**: DB transactions, API/worker behavior
- **E2E Tests**: Simulate full workflows from API → device → Git → UI
- Test database with Alembic-migrated schemas
- Threaded jobs tested for isolation, timing, logging



---
