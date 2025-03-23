# NetRaven Architecture Overview

## Introduction

This document provides a high-level overview of the NetRaven architecture, describing the system's components, their relationships, and the design principles that guide the project. This is intended for developers and system administrators who need to understand how NetRaven is structured internally.

## System Architecture

NetRaven follows a microservices architecture pattern, consisting of several containerized services that work together to provide network automation functionality. The system is designed to be scalable, maintainable, and deployable in various environments.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────────┐   │
│  │ Frontend│    │  API    │    │ Device  │    │   Scheduler     │   │
│  │  (Vue)  │◄──►│ Service │◄──►│ Gateway │    │                 │   │
│  └─────────┘    └─────────┘    └─────────┘    └─────────────────┘   │
│       ▲              ▲              ▲                  ▲            │
│       │              │              │                  │            │
│       └──────────────┼──────────────┼──────────────────┘            │
│                      │              │                               │
│                      ▼              │                               │
│               ┌─────────────┐       │                               │
│               │  Database   │       │                               │
│               │ (PostgreSQL)│       │                               │
│               └─────────────┘       │                               │
│                                     ▼                               │
│                               ┌─────────────┐                       │
│                               │   Network   │                       │
│                               │   Devices   │                       │
│                               └─────────────┘                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Components

### Frontend

- **Technology**: Vue.js with Vuetify
- **Purpose**: Provides the user interface for interacting with NetRaven
- **Key Features**:
  - Dashboard for system overview
  - Device management interface
  - Configuration backup viewer and comparison tool
  - User management interface
  - System settings and configuration

### API Service

- **Technology**: FastAPI (Python)
- **Purpose**: Provides RESTful API endpoints for all system functions
- **Key Features**:
  - Authentication and authorization
  - CRUD operations for devices, backups, users, and other entities
  - Database interaction
  - Business logic implementation
  - Event dispatch to other services

### Device Gateway

- **Technology**: Python
- **Purpose**: Handles direct communication with network devices
- **Key Features**:
  - Implements various connection protocols (SSH, NETCONF, REST)
  - Adapts to different device types (Cisco, Juniper, Arista, etc.)
  - Manages connection pooling and retry logic
  - Handles device-specific command syntax
  - Processes and normalizes device responses

### Scheduler

- **Technology**: Python with APScheduler
- **Purpose**: Manages scheduled tasks such as regular backups
- **Key Features**:
  - Configurable backup schedules
  - Task prioritization and queuing
  - Failure handling and retries
  - Notification generation for task results

### Database

- **Technology**: PostgreSQL
- **Purpose**: Persistent storage for all system data
- **Key Schemas**:
  - Users and authentication
  - Devices and credentials
  - Backup metadata
  - Schedules and tasks
  - System settings

## Data Flow

### Authentication Flow

1. User submits credentials via the Frontend
2. Frontend sends authentication request to API Service
3. API Service validates credentials against the database
4. If valid, API Service generates JWT token and returns it to Frontend
5. Frontend stores token and includes it in subsequent requests

### Device Backup Flow

1. Backup is triggered (manually or by scheduler)
2. API Service receives backup request
3. API Service requests device information from database
4. API Service sends backup job to Device Gateway
5. Device Gateway connects to the network device
6. Device Gateway retrieves configuration
7. Device Gateway sends configuration back to API Service
8. API Service stores the backup in the configured storage backend
9. API Service updates backup metadata in the database
10. API Service notifies Frontend of backup completion

## Design Principles

NetRaven's architecture is guided by the following principles:

### 1. Separation of Concerns

Each component has a specific responsibility and doesn't overlap with others:
- Frontend: User interaction
- API Service: Business logic and coordination
- Device Gateway: Network device communication
- Scheduler: Time-based operations
- Database: Persistent storage

### 2. Loose Coupling

Components communicate through well-defined interfaces, typically RESTful APIs:
- Changes to one component shouldn't require changes to others
- Components can be developed, tested, and deployed independently

### 3. Statelessness

API services are designed to be stateless:
- No client-specific state stored in the services
- State is maintained in the database or passed in requests
- Allows for horizontal scaling of services

### 4. Security by Design

Security is built into the architecture:
- Authentication required for all API endpoints
- Role-based access control for authorization
- Credential encryption in storage and transit
- Audit logging for security-relevant events

### 5. Observability

The system is designed to be observable:
- Comprehensive logging across all components
- Performance metrics collection
- Tracing for request flows
- Health check endpoints for monitoring

## Technology Stack

### Backend

- **Language**: Python 3.10+
- **Web Framework**: FastAPI
- **Database ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)
- **Task Scheduling**: APScheduler
- **Network Automation**: Netmiko, NAPALM, Nornir

### Frontend

- **Framework**: Vue.js 3
- **UI Library**: Vuetify
- **State Management**: Vuex
- **HTTP Client**: Axios
- **Visualization**: D3.js, Chart.js

### Infrastructure

- **Containerization**: Docker
- **Orchestration**: Docker Compose (development), Kubernetes (production)
- **Database**: PostgreSQL
- **Storage**: Local filesystem or S3-compatible object storage
- **CI/CD**: GitHub Actions

## Deployment Architecture

NetRaven supports multiple deployment models:

### Development Deployment

- Single-host deployment using Docker Compose
- All services on one machine
- Local PostgreSQL database
- Local file storage for backups

### Production Deployment

- Kubernetes-based deployment
- Horizontally scalable services
- External PostgreSQL database (managed service)
- S3-compatible object storage for backups
- Load balancing for API and Frontend services

## Extension Points

NetRaven is designed to be extensible. Key extension points include:

### Device Type Adapters

- Located in `core/adapters/`
- Implement the `DeviceAdapter` interface
- Allow support for additional device types

### Storage Backends

- Located in `core/storage/`
- Implement the `StorageBackend` interface
- Enable alternative backup storage options

### Authentication Providers

- Located in `web/auth/`
- Implement the `AuthProvider` interface
- Support additional authentication methods (LDAP, SAML, etc.)

## Future Architecture Directions

Planned architectural enhancements include:

1. **Event-Driven Architecture**: Implementing message queues for asynchronous operations
2. **GraphQL API**: Adding GraphQL support for more efficient data retrieval
3. **Real-Time Updates**: WebSocket support for live updates to the Frontend
4. **Distributed Tracing**: Implementing OpenTelemetry for enhanced observability
5. **Multi-Tenancy**: Supporting multiple isolated organizations within one installation

## Related Documentation

- [API Reference](./api-reference.md)
- [Database Schema](./database-schema.md)
- [Development Environment Setup](./development-setup.md)
- [Contributing Guide](./contributing.md) 