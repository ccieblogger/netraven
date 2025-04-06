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
### Project Coding Principles:

1. Code Quality and Maintainability

    Prefer Simple Solutions: Always opt for straightforward and uncomplicated approaches to problem-solving. Simple code is easier to understand, test, and maintain.​

    Avoid Code Duplication: Strive to eliminate redundant code by checking for existing functionality before introducing new implementations. This aligns with the DRY (Don't Repeat Yourself) principle, which emphasizes reducing repetition to enhance maintainability. ​
    Wikipedia

    Refactor Large Files: Keep individual files concise, ideally under 200-300 lines of code. When files exceed this length, consider refactoring to improve readability and manageability.​

2. Change Management

    Scope of Changes: Only implement changes that are explicitly requested or directly related to the task at hand. Unnecessary modifications can introduce errors and complicate code reviews.​

    Introduce New Patterns Cautiously: When addressing bugs or issues, exhaust all options within the existing implementation before introducing new patterns or technologies. If a new approach is necessary, ensure that the old implementation is removed to prevent duplicate logic and legacy code.​
    Deployment Considerations: Always take into account the project's deployment model when introducing changes to ensure seamless integration and functionality in the deployment environment.​

    Code refactoring: Code refactoring, enhancements, or changes of any significance should be done in a git feature branch and reintroduced back into the codebase through an integration branch after all changes have been succesfully tested.

3. Resource Management

    Clean Up Temporary Resources: Remove temporary files or code when they are no longer needed to maintain a clean and efficient codebase.​

    Avoid Temporary Scripts in Files: Refrain from writing scripts directly into files, especially if they are intended for one-time or temporary use. This practice helps maintain code clarity and organization.​

4. Testing Practices

    Use Mock Data Appropriately: Employ mocking data exclusively for testing purposes. Avoid using mock or fake data in development or production environments to ensure data integrity and reliability.​

5. Communication and Collaboration

    Propose and Await Approval for Plans: When tasked with updates, enhancements, creation, or issue resolution, present a detailed plan outlining the proposed changes. Break the plan into phases to manage complexity and await approval before proceeding.​ Provide an updated plan with clear indications of progress after each succesful set of changes.

    Seek Permission Before Advancing Phases: Before moving on to the next phase of your plan, always obtain approval to ensure alignment with project goals and stakeholder expectations.​

    Version Control Practices: After successfully completing each phase, perform a git state check, commit the changes, and push them to the repository. This ensures a reliable version history and facilitates collaboration.​

    Document Processes Clearly: Without being overly verbose, provide clear explanations of your actions during coding, testing, or implementing changes. This transparency aids understanding and knowledge sharing among team members.

    Development Log: Always maintain a log of your changes, insights, and any other relavant information another developer could use to pick up where you left off to complete the current task that you are working on. Put this log in the ./aidocs/ folder in a folder named after the feature branch you are working on. If you are debugging use a similar naming convention and logging methodology.


### Testing Strategy

- **Unit Tests**: Business logic, validation, utilities
- **Integration Tests**: DB transactions, API/worker behavior
- **E2E Tests**: Simulate full workflows from API → device → Git → UI
- Test database with Alembic-migrated schemas
- Threaded jobs tested for isolation, timing, logging



---
