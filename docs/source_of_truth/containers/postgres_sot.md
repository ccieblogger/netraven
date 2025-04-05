# PostgreSQL Container: Intended State

## Overview

The PostgreSQL container serves as the central data storage component for the NetRaven system. It provides persistent, relational database storage for all components in the application stack while functioning as an integral part of the containerized deployment architecture.

## Core Purpose

This container provides a unified PostgreSQL database instance that:

1. Stores all persistent application data including device information, configurations, credentials, and system settings
2. Implements the Credential Store functionality through its schema design
3. Maintains data integrity across all services
4. Provides an ACID-compliant transaction system for all database operations
5. Serves as the single source of truth for application state

## Database Schema

The PostgreSQL schema is designed to support all NetRaven functionality with a clean, normalized structure:

### Core Tables

- **devices**: Stores network device information including hostnames, IP addresses, device types, and identifying details
- **device_configurations**: Stores the retrieved device configurations with timestamps and metadata
- **credentials**: Implements the Credential Store functionality with encrypted password storage
- **tags**: Supports the tagging system for flexible device organization
- **device_tags**: Junction table for the many-to-many relationship between devices and tags
- **credential_tags**: Junction table linking credentials to tags for intelligent credential selection
- **jobs**: Tracks scheduled and completed configuration retrieval jobs
- **job_logs**: Stores detailed logs of job execution with structured data
- **system_settings**: Stores user/admin configurable settings

### Key Relationships

- Devices have many configurations (one-to-many)
- Devices have many tags through device_tags (many-to-many)
- Credentials have many tags through credential_tags (many-to-many)
- Jobs have many log entries (one-to-many)

## Schema Initialization

The database schema is initialized through a hybrid approach:

1. **SQL Initialization Scripts**:
   - Basic PostgreSQL setup (extensions, schema creation)
   - Run automatically when the container starts

2. **SQLAlchemy Models**:
   - Define table structures, relationships, and constraints
   - All models use a single Base class for consistency
   - Tables are created by a dedicated initialization script

3. **Initialization Process**:
   - PostgreSQL container starts and runs SQL initialization script
   - API container runs Python initialization script before startup
   - Default data (e.g., tags) is created during initialization

This approach ensures a consistent schema across all deployments while maintaining flexibility for development.

## Performance Characteristics

The PostgreSQL container is configured for optimal performance in the NetRaven application context:

1. **Indexes**: Primary indexes on all ID fields, with additional indexes on:
   - Device hostnames and IP addresses
   - Configuration timestamps
   - Tag names
   - Job status and timestamps

2. **Query Optimization**:
   - Prepared statements for common queries
   - Appropriate use of joins for related data retrieval
   - Pagination for large result sets

3. **Data Types**:
   - Appropriate PostgreSQL-specific data types (UUID, JSONB for flexible data)
   - Text search capabilities for configuration content
   - Timestamp with timezone for all temporal data

## Access Patterns

The PostgreSQL container interacts with other containers through well-defined access patterns:

1. **Main Application Container**:
   - Primary consumer of database services
   - Uses SQLAlchemy ORM for database access
   - Implements connection pooling and transaction management
   - Handles all business logic data operations

2. **Scheduler Service**:
   - Access for scheduling and managing configuration retrieval jobs
   - Stores job state information and execution history
   - Uses transactional operations for job status updates

3. **Job Logging Service**:
   - Writes structured log entries for all operations
   - Implements query patterns for log retrieval
   - Uses efficient batch inserts for log entries

4. **Device Communication Service**:
   - Stores retrieved device configurations
   - Records device information and metadata
   - Updates device status and accessibility records

5. **API Gateway**:
   - Read access for serving API requests
   - Implements pagination and filtering for data retrieval
   - Uses read-only transactions when possible

6. **CLI Components**:
   - Direct database access for administration functions
   - Read operations for reporting and monitoring
   - Schema management for initial setup

7. **Key Rotation Container**:
   - Periodic access for credential re-encryption
   - Uses dedicated service account with limited privileges

## Container Configuration

The PostgreSQL container has the following configuration characteristics:

1. **Environment Variables**:
   - `POSTGRES_USER`: Database administrator username
   - `POSTGRES_PASSWORD`: Database administrator password
   - `POSTGRES_DB`: Default database name (netraven)
   - `PGDATA`: Data directory path within container

2. **Port Exposure**:
   - Port 5432 exposed only to the internal Docker network
   - No direct external access to the database

3. **Health Checks**:
   - Implements Docker health check via pg_isready
   - Includes startup delay to ensure proper initialization

## Persistence Implementation

The PostgreSQL container implements data persistence through the following mechanisms:

1. **Volume Configuration**:
   - Named Docker volume for the PostgreSQL data directory
   - Example: `postgres_data:/var/lib/postgresql/data`
   - Ensures data survives container restarts and rebuilds

2. **Backup Path**:
   - Additional volume mount for database backups
   - Example: `./backups:/backups`
   - Enables customers to perform and manage backups
   - Includes backup script for easy backup creation

3. **Initialization**:
   - Initial schema created through initialization scripts
   - Tables defined via SQLAlchemy models for consistency

## Containerization Details

The PostgreSQL container is built and configured as follows:

1. **Base Image**:
   - Official PostgreSQL Docker image (version 14 or later)
   - Alpine-based for smaller footprint

2. **Customizations**:
   - PostgreSQL configuration tuned for NetRaven's usage patterns
   - Custom initialization scripts for schema creation
   - Security hardening (minimal privileges, restricted network access)

3. **Resource Allocation**:
   - Minimum memory: 512MB
   - Recommended memory: 1GB
   - Disk space requirements depend on number of devices and retention policies

## Security Considerations

The PostgreSQL container implements the following security measures:

1. **Authentication**:
   - Password authentication for database users
   - No trust authentication allowed
   - Service-specific database users with limited privileges

2. **Encryption**:
   - Sensitive data (like credentials) stored encrypted at rest
   - Communication over TLS within the Docker network

3. **Access Controls**:
   - Fine-grained access controls through PostgreSQL roles
   - No direct external access to database ports

## Important Product Considerations

As NetRaven is a deployable product rather than a continuously running service:

1. **Fixed Schema State**: The database schema represents the exact state that should be shipped to customers. Changes should be implemented as new product releases, not as migrations applied to existing deployments.

2. **Customer Environment**: The database must initialize correctly in various customer environments without developer intervention.

3. **Resource Efficiency**: The PostgreSQL container must operate efficiently within the resource constraints of customer environments.

4. **Deployment Simplicity**: Configuration should be minimized to ensure straightforward customer deployment.

5. **Data Ownership**: All data remains in the customer environment and is not accessible to the development team.

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