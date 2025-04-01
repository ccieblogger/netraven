# NetRaven Documentation

Welcome to the NetRaven documentation. This documentation provides comprehensive information about the NetRaven network management platform.

## Documentation Sections

### Architecture Documentation

Architecture documentation describes the system components, their interactions, and design decisions.

- [Credential Store Architecture](architecture/credential-store.md) - Architecture of the credential management system

### Implementation Documentation

Documentation about the implementation and progress of architectural changes.

- [Documentation Reorganization](implementation/documentation-reorganization.md) - Summary of the documentation reorganization process
- [Documentation Reorganization Summary](implementation/documentation-reorganization-summary.md) - Comprehensive summary of the completed documentation reorganization
- [Credential Store SQLite Migration Plan](implementation/credential-store-sqlite-migration-plan.md) - Plan for migrating the credential store from SQLite to PostgreSQL

#### Implementation Plans

- [Architecture Redesign Plan](implementation_plans/architecture-redesign-plan.md) - Comprehensive plan for redesigning core components

#### Development Logs

- [Architecture Redesign Progress Summary](development_logs/architecture-redesign-progress-summary.md) - Summary of progress on the architecture redesign
- [Phase 1: Job Logging Service](development_logs/phase1_job_logging_service.md) - Implementation of the Job Logging Service
- [Phase 2: Scheduler Service](development_logs/phase2_scheduler_service.md) - Implementation of the Scheduler Service
- [Phase 2b: Device Communication Service](development_logs/phase2b-device_comm_service.md) - Implementation of the Device Communication Service
- [Phase 3.1: Async Support](development_logs/phase3.1-async-support.md) - Implementation of asynchronous database support

### Guides

#### Developer Guides

Developer guides provide instructions and best practices for developers working on the NetRaven codebase.

- [Credential Store Migration Guide](guides/developer/credential-store-migration.md) - Guide for migrating the credential store from SQLite to PostgreSQL
- [Frontend Development Guide](guides/developer/frontend-development.md) - Guide for developing the Vue.js frontend
- [Testing Guide](guides/developer/testing.md) - Guide for writing and running tests

#### User Guides

User guides provide end-user documentation for using the NetRaven application.

### Reference Documentation

Reference documentation provides detailed information about the NetRaven APIs, configuration options, and database schema.

- [Configuration Reference](reference/configuration.md) - Comprehensive configuration system documentation
- [Environment Variables Reference](reference/environment-variables.md) - Complete list of environment variables
- [Database Migrations](reference/database-migrations.md) - Guide to the database migration system

### Configuration Documentation

- [Core Settings](reference/configuration/core.md) - Core application configuration
- [Web Service Settings](reference/configuration/web.md) - Web server and API configuration
- [Environment Configuration Guide](guides/developer/environment-configuration.md) - Environment-specific configurations

## Getting Started

If you're new to NetRaven, here are some resources to help you get started:

1. Read the [README.md](../README.md) file in the project root for an overview of the project
2. Explore the architecture documentation to understand the system design
3. Follow the developer guides to set up your development environment

## Contributing to Documentation

We welcome contributions to the NetRaven documentation. Please refer to the [documentation standards](README.md#documentation-standards) for guidelines on creating and updating documentation. 