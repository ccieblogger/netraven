# NetRaven Architecture: Intended State

## Executive Summary

This document provides a high-level overview of the intended architecture for the NetRaven system. It serves as a unified source of truth for developers to understand the target architecture state.

## System Overview

NetRaven is a specialized network device configuration backup system designed as a deployable product for customer environments. It is not a centralized service or a continuously running system managed by the development team, but rather a containerized application intended to be deployed at customer sites.

The system is designed to:
1. Communicate with network devices to retrieve running configurations and device information
2. Store retrieved configurations in a Git repository for version control and historical tracking
3. Provide API access to device configurations

The architecture follows service-oriented principles, with distinct services handling specific domains of functionality. Each customer deployment will run its own independent instance of the complete system.

## Core Architectural Principles

- **Service-Oriented Architecture**: Functionality is organized into distinct services with well-defined interfaces
- **Centralized Control Flow**: Device interactions flow through a unified scheduler service
- **Comprehensive Logging**: All operations are tracked through a centralized logging service
- **Asynchronous Operations**: The system supports asynchronous execution for improved scalability
- **Protocol Abstraction**: Device communication is abstracted to support multiple protocols
- **Database Unification**: All persistent data is stored in a single PostgreSQL database

## Core Services

### 1. Scheduler Service

The Scheduler Service serves as the central coordination point for configuration backup operations.

**Key Responsibilities**:
- Scheduling configuration retrieval jobs
- Task handler registration system
- Job state management and monitoring
- Priority-based job execution
- Exposing functionality through REST API endpoints and CLI commands

### 2. Job Logging Service

The Job Logging Service provides comprehensive logging for all configuration retrieval operations.

**Key Responsibilities**:
- Structured logging with consistent schema
- Sensitive data filtering and redaction
- Job session lifecycle management
- Cross-component logging integration
- Query capabilities for job history

### 3. Device Communication Service

The Device Communication Service handles all interactions with network devices, specifically for retrieving configurations and device information.

**Key Responsibilities**:
- Protocol abstraction (SSH, Telnet, HTTP/REST)
- Connection pooling and management
- Unified error handling
- Credential management integration
- Device-specific command handling for configuration retrieval
- Retrieval of device identifying information (serial numbers, hostnames)

### 4. Credential Store

The Credential Store is implemented as part of the database schema and provides credential management functionality through database models and services.

**Key Responsibilities**:
- Secure storage of authentication credentials
- Tag-based credential association
- Prioritized credential selection
- Success/failure tracking
- Integration with core database operations

## Tagging System

The tagging system is a fundamental organizational concept in NetRaven that enables flexible categorization of devices and association with credentials.

**Key Features**:
- Flat tag structure for device categorization (by type, location, role, etc.)
- Many-to-many relationships between devices and tags
- Tag-based credential association that allows credentials to be linked to specific device types
- Basic credential prioritization within tags (numeric priority values)
- Query capabilities for finding devices by tag
- Filtering capabilities based on tags

**Implementation**:
- Database models for tags, device-tag associations, and credential-tag associations
- REST API endpoints for tag management
- Service layer for tag operations
- UI components for tag management and assignment

The tagging system serves as a critical link between devices and credentials, enabling NetRaven to intelligently select the appropriate authentication method for each device based on its tags.

## Database Architecture

All components use a single PostgreSQL database with the following characteristics:

- Unified schema across all components (including credential storage)
- Async-compatible ORM (SQLAlchemy)
- Proper transaction management
- Migrations managed through Alembic

## Component Relationships

```
┌───────────────────┐      ┌────────────────────┐      ┌────────────────────┐
│                   │      │                    │      │                    │
│   API Gateway     │─────►│  Scheduler Service │─────►│ Device Comm Service│
│                   │      │                    │      │                    │
└───────────────────┘      └────────────────────┘      └────────────────────┘
        │                           │                          │
        │                           │                          │
        │                           ▼                          │
        │                  ┌────────────────────┐             │
        └─────────────────►│  Job Logging       │◄────────────┘
                           │  Service           │
                           │                    │
                           └────────────────────┘
                                    │
                                    ▼
                           ┌────────────────────────────────────┐
                           │                                    │
                           │              Database              │
                           │    (includes Credential Store)     │
                           │                                    │
                           └────────────────────────────────────┘
```

The Command Line Interface (CLI) components operate independently from the core services, providing administrative access through a separate interface:

```
┌────────────────────┐      ┌────────────────────────────────────┐
│                    │      │                                    │
│   CLI Components   │─────►│              Database              │
│                    │      │    (includes Credential Store)     │
└────────────────────┘      │                                    │
                            └────────────────────────────────────┘
```

## Docker and Container Deployment Architecture

NetRaven is designed as a containerized application that runs exclusively in Docker containers. This architectural decision provides consistency, isolation, and portability across development, testing, and production environments.

### Container Structure

The application is structured as a set of interconnected containers:

- **Main Application Container**: Contains the core NetRaven application (Python/FastAPI backend)
- **Frontend Container**: Serves the Vue.js web interface
- **Database Container**: Runs PostgreSQL for persistent storage
- **Key Rotation Container**: Handles credential encryption key rotation
- **CLI Container**: Provides command-line interface utilities for system administration

### Container Relationships

```
┌───────────────────────────────────────────────────────────┐
│                      Docker Network                        │
│                                                           │
│  ┌─────────────┐     ┌────────────┐     ┌──────────────┐  │
│  │             │     │            │     │              │  │
│  │   Frontend  │◄───►│    Main    │◄───►│   Database   │  │
│  │    (Vue)    │     │ Application│     │ (PostgreSQL) │  │
│  │             │     │            │     │              │  │
│  └─────────────┘     └────────────┘     └──────────────┘  │
│                           │                    ▲           │
│                           ▼                    │           │
│                    ┌────────────┐      ┌───────────────┐  │
│                    │    Key     │      │               │  │
│                    │  Rotation  │      │      CLI      │  │
│                    │            │      │               │  │
│                    └────────────┘      └───────────────┘  │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Development Environment

For development, the containers are orchestrated using Docker Compose with volumes mounted to enable real-time code changes without rebuilding containers:

- Source code is mounted into the main application container
- Frontend code is mounted into the frontend container
- Configuration files are mounted from the host's `/config` directory

### Important Considerations

1. **Path Resolution**: All file paths in the application must use container paths, not host paths
2. **Network Access**: Containers communicate over the Docker network with service names as hostnames
3. **Database Access**: Database connections use the database container's service name
4. **Configuration Mounting**: Configuration files are mounted from the host system into the containers
5. **Volume Persistence**: Database and backup data are persisted using Docker volumes

### Build Process

The build process is defined in the Dockerfiles located in the `/docker` directory:

- `Dockerfile.main`: Builds the main application container
- `Dockerfile.frontend`: Builds the frontend container
- Additional configuration in `docker-compose.yml`

When developing new features, **always test within the Docker environment** to ensure compatibility with the production deployment architecture.

## Git Repository Integration

A key component of NetRaven is its integration with a Git repository for storing device configurations:

- Local Git repository for configuration storage
- Automatic commit of configuration changes
- Historical tracking of configuration versions
- Diffing capabilities for change analysis
- Structured organization by device

## Configuration System

The configuration system uses a dual approach to manage application settings:

### 1. User/Admin Configurable Settings

Settings that users or administrators are likely to change are stored in the database and exposed through the web UI:

- System preferences and behavior options
- Default values for device operations
- Notification settings
- Backup scheduling defaults
- UI customization options

These settings are:
- Editable through a dedicated admin UI section
- Stored in a `system_settings` table in the database
- Cached appropriately for performance
- Protected by role-based access controls
- Accessible programmatically through a settings service

### 2. Application Configuration

All other application settings that typically don't change after deployment are stored in the `/config` directory:

- **Core Settings**: Basic application configuration
- **Web Service Settings**: Web server and API configuration 
- **Component-specific Settings**: Settings for individual services
- **Environment-specific Settings**: Configurations for different environments

Configuration files are organized within the `/config` directory as follows:
- `/config/netraven.yaml`: Main configuration file
- `/config/settings/*.yaml`: Component-specific settings
- `/config/environments/*.yaml`: Environment-specific settings

All components load their non-user-configurable settings from this central location to ensure consistency across the application. Environment variables provide runtime overrides for configuration values when needed.

### Configuration Hierarchy

Settings are loaded in the following order of precedence:
1. Environment variables (highest precedence)
2. User/admin settings from the database
3. Environment-specific configuration files
4. Component-specific configuration files
5. Main configuration file (lowest precedence)

This approach allows for flexibility in configuration while maintaining a clear separation between settings that should be user-configurable and those that are core to application function.

## Testing Methodology

NetRaven is a deployable product, not a centralized service with a permanent running instance. This distinction is important for the testing approach. Testing should validate that the product functions correctly in its intended deployment environment without introducing unnecessary complexity.

### Testing Pyramid

The testing strategy follows the testing pyramid model:

1. **Unit Tests** (base of pyramid - highest quantity)
   - Test individual functions, methods, and classes in isolation
   - Mock external dependencies as needed for isolation
   - Focus on code paths and edge cases
   - Aim for high coverage (>80%)

2. **Integration Tests** (middle of pyramid)
   - Test interactions between components
   - Test service interactions
   - Focus on component contracts and interfaces

3. **End-to-End Tests** (top of pyramid - lowest quantity)
   - Test complete user flows
   - Test through the API and UI
   - Simulate actual device interactions with mock devices
   - Focus on critical user journeys

### Testing Environment

All tests must be executed in the Docker-based environment that matches the deployment environment:

- Tests run inside the containerized environment
- Tests use the actual PostgreSQL database that is part of the Docker setup
- Database can be rebuilt and reinitialized for testing as needed
- Mock services are provided for simulating network devices

### Database Testing Approach

- **Use the standard PostgreSQL database**: All tests should use the same PostgreSQL database that the application will use in deployment
- **Avoid alternative databases**: Do not introduce other database types (like SQLite) for testing, as this can lead to inconsistencies and codebase contamination
- **Database initialization**: Create appropriate setup and teardown procedures to initialize the database to a known state before tests and clean up afterward
- **Test isolation**: Ensure tests are properly isolated through transaction management or appropriate cleanup

### Test Types and Organization

Tests are organized in the `/tests` directory with a structure that mirrors the application structure:

- `/tests/unit/`: Unit tests for isolated components
- `/tests/integration/`: Tests for component interactions
- `/tests/e2e/`: End-to-end tests for complete workflows
- `/tests/fixtures/`: Shared test fixtures and utilities

### Test-Driven Development

When developing new features or fixing bugs:

1. Write tests first that define the expected behavior
2. Implement the functionality to make the tests pass
3. Refactor the code while ensuring tests continue to pass

### Asynchronous Testing

For asynchronous components:

- Use asynchronous testing patterns
- Test both success and failure paths
- Include timeout and cancellation scenarios
- Ensure proper resource cleanup

### Mocking External Dependencies

When testing, mock only external systems that are not part of the NetRaven deployment:

- Network devices should be mocked to simulate different device types and responses
- External services should be replaced with mock implementations
- System resources like time can be virtualized for deterministic testing

Tests should use the actual implementation of internal components (database, file system within the container, etc.) whenever possible to ensure the product functions correctly in its intended deployment environment.

### Test Execution

Tests should be executed in the following contexts:

1. **Development**: Developers must run tests in the Docker environment before submitting changes
2. **Pre-Deployment**: All tests should be run and pass before packaging the product for delivery

All test code must maintain the same quality standards as application code.

## Directory Structure

The intended directory structure follows clear organization principles:

- `/netraven/core`: Core functionality and shared components
- `/netraven/core/services`: Service implementations (Job Logging, Scheduler, etc.)
- `/netraven/web`: Web interface and API components
- `/cli`: Command-line interface components and utilities
- `/cli/bin`: Command-line executable scripts
- `/config`: Configuration files
- `/docs`: Documentation organized by type
- `/scripts`: Utility scripts organized by purpose
- `/tests`: Comprehensive test suite

## Coding Principles

All developers working on the NetRaven project must adhere to the following principles:

### 1. Code Quality and Maintainability

- **Prefer Simple Solutions**: Always opt for straightforward and uncomplicated approaches to problem-solving. Simple code is easier to understand, test, and maintain.

- **Avoid Code Duplication**: Eliminate redundant code by checking for existing functionality before introducing new implementations. Follow the DRY (Don't Repeat Yourself) principle to enhance maintainability.

- **Refactor Large Files**: Keep individual files concise, ideally under 200-300 lines of code. When files exceed this length, refactor to improve readability and manageability.

### 2. Change Management

- **Scope of Changes**: Only implement changes that are explicitly requested or directly related to the task at hand. Unnecessary modifications can introduce errors and complicate code reviews.

- **Introduce New Patterns Cautiously**: When addressing bugs or issues, exhaust all options within the existing implementation before introducing new patterns or technologies. If a new approach is necessary, ensure that the old implementation is removed to prevent duplicate logic and legacy code.

- **Code Refactoring Process**: Code refactoring, enhancements, or changes of any significance should be done in a git feature branch and reintroduced back into the codebase through an integration branch after all changes have been successfully tested.

### 3. Resource Management

- **Clean Up Temporary Resources**: Remove temporary files or code when they are no longer needed to maintain a clean and efficient codebase.

- **Avoid Temporary Scripts in Files**: Refrain from writing scripts directly into files, especially if they are intended for one-time or temporary use. This practice helps maintain code clarity and organization.

### 4. Testing Practices

- **Use Mock Data Appropriately**: Employ mocking data exclusively for testing purposes. Avoid using mock or fake data in development or production environments to ensure data integrity and reliability.

- **Test Coverage**: Strive for comprehensive test coverage of new functionality, with particular attention to edge cases and error conditions.

### 5. Communication and Collaboration

- **Propose and Await Approval for Plans**: When tasked with updates, enhancements, creation, or issue resolution, present a detailed plan outlining the proposed changes. Break the plan into phases to manage complexity and await approval before proceeding.

- **Seek Permission Before Advancing Phases**: Before moving on to the next phase of your plan, always obtain approval to ensure alignment with project goals and stakeholder expectations.

- **Version Control Practices**: After successfully completing each phase, perform a git state check, commit the changes, and push them to the repository. This ensures a reliable version history and facilitates collaboration.

- **Document Processes Clearly**: Without being overly verbose, provide clear explanations of your actions during coding, testing, or implementing changes. This transparency aids understanding and knowledge sharing among team members.

- **Development Log**: Always maintain a log of your changes, insights, and any other relevant information another developer could use to pick up where you left off to complete the current task. Store this log in the `./docs/development_logs/` folder in a folder named after the feature branch you are working on. 