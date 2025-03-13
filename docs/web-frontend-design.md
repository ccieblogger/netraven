# NetRaven Web Frontend Design Document

**Version:** 1.0  
**Date:** March 12, 2025  
**Status:** Draft  

## 1. Introduction

### 1.1 Purpose
This document outlines the design and implementation plan for the NetRaven web frontend. NetRaven is a Python-based tool for automated backup of Cisco network device configurations to multiple storage destinations, including local Git repositories and AWS S3 storage.

### 1.2 Scope
The web frontend will provide a modern, professional interface for configuring, managing, and viewing details about NetRaven's backup operations. It will include authentication, authorization, job scheduling, device inventory management, and third-party integrations.

### 1.3 Audience
This document is intended for developers, stakeholders, and future maintainers of the NetRaven project.

### 1.4 Project Goals
- Create a modern, responsive web interface for NetRaven
- Implement RBAC authentication and authorization
- Support third-party identity providers
- Provide job scheduling and parallel execution capabilities
- Manage device inventory with third-party integration
- Offer a comprehensive API for external systems
- Ensure the solution is cloud-compatible and lightweight

## 2. Architecture Overview

### 2.1 Technology Stack

#### Backend
- **Framework:** FastAPI
- **Database:** SQLAlchemy ORM with multiple backend support
- **Authentication:** JWT + OAuth2/SAML for external providers
- **Job Scheduling:** APScheduler
- **Task Queue:** Celery with Redis
- **Storage:** Pluggable backends (Local+Git, S3, Azure)

#### Frontend
- **Framework:** Vue.js
- **Styling:** Tailwind CSS
- **UI Components:** Custom components inspired by GitHub design
- **State Management:** Pinia
- **HTTP Client:** Axios

### 2.2 System Architecture Diagram

```
┌────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│                │     │                      │     │                 │
│  Web Frontend  │────▶│  NetRaven Backend   │────▶│ Storage Backends │
│  (Vue.js)      │     │  (FastAPI)          │     │ (Git, S3, etc.)  │
│                │     │                      │     │                 │
└────────────────┘     └──────────────────────┘     └─────────────────┘
                                │   ▲
                                ▼   │
                        ┌───────────────────┐
                        │                   │
                        │  Database         │
                        │  (PostgreSQL/     │
                        │   SQLite)         │
                        │                   │
                        └───────────────────┘
                                │   ▲
                                ▼   │
┌────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│                │     │                      │     │                 │
│ Authentication │◀───▶│ Job Scheduling &     │     │ External        │
│ Providers      │     │ Execution            │     │ Integrations    │
│ (AD, Local)    │     │ (APScheduler, Celery)│     │ (Netbox, etc.)  │
│                │     │                      │     │                 │
└────────────────┘     └──────────────────────┘     └─────────────────┘
                                                           │  ▲
                                                           ▼  │
                                                     ┌─────────────────┐
                                                     │                 │
                                                     │ External API    │
                                                     │ Consumers       │
                                                     │ (Zabbix, etc.)  │
                                                     │                 │
                                                     └─────────────────┘
```

### 2.3 Component Interactions

1. **User Authentication Flow**
   - User logs in through web interface
   - Authentication request sent to backend
   - Backend validates credentials against local DB or external provider
   - JWT token issued to client
   - Subsequent requests include JWT token

2. **Backup Job Execution Flow**
   - User configures backup job through web interface
   - Job configuration stored in database
   - Scheduler triggers job at configured time
   - Worker processes execute job
   - Results stored in database and files in storage backend
   - Notifications sent based on configuration

3. **Third-Party Integration Flow**
   - External system requests API key through admin interface
   - API calls made to NetRaven API endpoints
   - Authentication and authorization checked
   - Requested data or operation provided
   - Rate limiting and monitoring applied

## 3. Detailed Component Design

### 3.1 Backend Components

#### 3.1.1 API Layer
- RESTful API built with FastAPI
- Resource-based URL structure
- OpenAPI documentation
- Authentication via JWT and API keys
- Rate limiting and monitoring

#### 3.1.2 Authentication & Authorization
- Local user authentication with password hashing
- Microsoft AD integration
- Role-based access control (superadmin/user)
- API key management for third-party integrations

#### 3.1.3 Job Scheduling & Execution
- Flexible scheduling (hourly, daily, weekly, monthly)
- Parallel job execution based on system resources
- Job status tracking and history
- Error handling and retry mechanism

#### 3.1.4 Storage Management
- Abstract storage interface
- Implementations for:
  - Local filesystem with Git
  - S3-compatible storage
  - Azure Blob Storage
- Version control and diff capabilities

#### 3.1.5 Integration Adapters
- Netbox integration for device inventory
- Generic webhook support
- Notification service (email, webhooks)

### 3.2 Frontend Components

#### 3.2.1 Core UI Components
- Navigation and layout
- Dashboard with metrics
- Data tables and filters
- Forms and validation
- Notifications and alerts

#### 3.2.2 Main Application Screens
- Dashboard
- Device inventory
- Backup job management
- Backup file browser
- User management
- System configuration
- API key management

#### 3.2.3 State Management
- Authentication state
- Application configuration
- Form handling
- Data caching

## 4. Database Design

### 4.1 Main Entities

#### 4.1.1 Users
- User authentication and authorization information
- Role assignments
- Activity tracking

#### 4.1.2 Devices
- Network device inventory
- Connection information
- Metadata (serial, hostname, etc.)
- Integration mappings (Netbox IDs, etc.)

#### 4.1.3 Backup Jobs
- Job configuration
- Schedule information
- Status and history
- Related devices

#### 4.1.4 Backup Files
- Metadata about backup files
- Storage location information
- Version tracking
- Related devices and jobs

#### 4.1.5 API Keys
- Third-party integration keys
- Permission scopes
- Usage tracking

### 4.2 Entity Relationships

```
User (1) --- (*) APIKey
Device (1) --- (*) BackupJob
Device (1) --- (*) BackupFile
BackupJob (1) --- (*) BackupFile
```

## 5. API Design

### 5.1 Authentication Endpoints
- POST /api/auth/login
- POST /api/auth/logout
- POST /api/auth/refresh

### 5.2 User Management Endpoints
- GET/POST /api/users
- GET/PUT/DELETE /api/users/{id}

### 5.3 Device Endpoints
- GET/POST /api/devices
- GET/PUT/DELETE /api/devices/{id}
- GET /api/devices/{id}/backups

### 5.4 Job Endpoints
- GET/POST /api/jobs
- GET/PUT/DELETE /api/jobs/{id}
- POST /api/jobs/{id}/run
- GET /api/jobs/{id}/status

### 5.5 Backup File Endpoints
- GET /api/backups
- GET /api/backups/{id}
- GET /api/backups/{id}/download
- GET /api/backups/{id}/diff/{other_id}

### 5.6 API Key Management
- GET/POST /api/keys
- GET/DELETE /api/keys/{id}

### 5.7 System Configuration
- GET/PUT /api/config/*

## 6. Implementation Plan

### 6.1 Phase 1: Core Infrastructure (4-6 weeks)

**Goal:** Establish the foundational elements that everything else will build upon.

**Deliverables:**
1. **Project Setup & Configuration**
   - Project structure setup
   - Development environment configuration (Docker, WSL compatibility)
   - Dependency management
   - CI/CD pipeline basics

2. **Basic Backend Implementation**
   - FastAPI application scaffold
   - Database models and migrations
   - Core business logic for backup management
   - Basic API endpoints

3. **Authentication Foundation**
   - Local user authentication
   - Simple role-based authorization (superadmin/user)
   - JWT token implementation

4. **Storage Integration**
   - Local filesystem + Git integration
   - Abstract storage interface for future implementations

**Key Milestones:**
- Working API with basic authentication
- Ability to store and retrieve basic configuration files
- Initial test coverage for core functionality

### 6.2 Phase 2: UI Development (6-8 weeks)

**Goal:** Build a user-friendly interface that follows GitHub-inspired design principles.

**Deliverables:**
1. **Frontend Foundation**
   - Vue.js application setup
   - Tailwind CSS integration
   - Component library setup
   - API client services

2. **Core UI Components**
   - Navigation and layout components
   - Dashboard with basic metrics
   - Device inventory management screens
   - Backup job configuration interface
   - Backup file browser

3. **User Management Interface**
   - User creation/editing
   - Role assignment
   - Profile management

4. **System Settings UI**
   - Application configuration screens
   - Storage backend settings

**Key Milestones:**
- Functional UI with all core screens
- Integration with backend APIs
- Responsive design for various screen sizes

### 6.3 Phase 3: Advanced Features (6-8 weeks)

**Goal:** Implement more sophisticated capabilities to enhance functionality.

**Deliverables:**
1. **Job Scheduling System**
   - Flexible job scheduling (hourly, daily, weekly, monthly)
   - Parallel job execution
   - Job monitoring and management
   - Logging and error handling

2. **External Authentication**
   - Microsoft AD integration
   - OAuth2 support for other identity providers

3. **Notification System**
   - Email notifications for job status
   - Configurable notification rules
   - Webhook support for external systems

4. **Advanced Storage Options**
   - S3-compatible storage integration
   - Azure Blob Storage integration
   - Storage migration utilities

**Key Milestones:**
- Complete job scheduling system
- Multiple authentication methods
- Comprehensive notification capabilities

### 6.4 Phase 4: Integration & API Layer (4-6 weeks)

**Goal:** Create a robust API layer for third-party integrations and implement Netbox integration.

**Deliverables:**
1. **Generic API Infrastructure**
   - Comprehensive REST API endpoints
   - API key management system
   - OpenAPI documentation
   - Rate limiting and security measures

2. **Netbox Integration**
   - Device inventory synchronization
   - Metadata mapping configuration
   - Scheduled sync processes

3. **Integration Examples**
   - Zabbix integration example
   - General integration documentation
   - Example clients in Python and other languages

4. **API Management UI**
   - API key creation and management interface
   - Usage monitoring
   - Permission configuration

**Key Milestones:**
- Fully documented REST API
- Working Netbox integration
- Example third-party integration with Zabbix

### 6.5 Phase 5: Refinement & Optimization (4 weeks)

**Goal:** Polish the application, optimize performance, and prepare for production deployment.

**Deliverables:**
1. **Performance Optimization**
   - Application profiling and bottleneck identification
   - Database query optimization
   - Frontend optimization (bundle size, lazy loading)

2. **Deployment Packages**
   - Docker production deployment
   - Cloud deployment templates (AWS, Azure)
   - Installation documentation

3. **Advanced Monitoring**
   - Application health monitoring
   - Performance metrics collection
   - Alerting integration

4. **User Documentation**
   - Administrator guide
   - User guide
   - API documentation

**Key Milestones:**
- Production-ready application
- Comprehensive documentation
- Deployment templates for various environments

## 7. Development Environment

### 7.1 Directory Structure

```
netraven/
├── backend/                       # FastAPI backend
│   ├── app/
│   │   ├── api/                   # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── devices.py
│   │   │   ├── jobs.py
│   │   │   └── routes.py          # API router registration
│   │   ├── core/                  # Core functionality
│   │   │   ├── config.py          # Application configuration
│   │   │   ├── security.py        # Authentication & security
│   │   │   └── logging.py         # Logging setup
│   │   ├── db/                    # Database models & operations
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── crud.py            # Database operations
│   │   │   └── database.py        # Database connection
│   │   ├── schemas/               # Pydantic schemas
│   │   │   ├── device.py
│   │   │   ├── job.py
│   │   │   └── user.py
│   │   ├── storage/               # Storage backends
│   │   │   ├── base.py            # Abstract interface
│   │   │   ├── local.py           # Local filesystem
│   │   │   └── git.py             # Git integration
│   │   └── main.py                # Application entry point
│   ├── tests/                     # Test directory
│   ├── alembic/                   # Database migrations
│   ├── Dockerfile                 # Backend container
│   └── requirements.txt           # Python dependencies
├── frontend/                      # Vue.js frontend (minimal for now)
│   ├── src/
│   │   └── App.vue                # Basic app shell
│   ├── package.json               # JavaScript dependencies
│   └── Dockerfile                 # Frontend container
├── docker-compose.yml             # Development environment
├── .gitignore                     # Git ignore file
└── README.md                      # Project documentation
```

### 7.2 Development Setup

#### 7.2.1 Prerequisites
- Docker and Docker Compose
- Node.js and npm
- Python 3.10+
- Git

#### 7.2.2 Development Workflow
1. Local development with Docker Compose
2. Unit and integration testing
3. CI/CD pipeline for automated testing and deployment

## 8. Deployment Options

### 8.1 Docker Deployment
- Docker Compose for simple deployment
- Docker Swarm for scaled deployments
- Container health checks and auto-restart

### 8.2 Cloud Deployment
- AWS Elastic Beanstalk
- Azure App Service
- Kubernetes for larger deployments

### 8.3 Hybrid Deployment
- Frontend in cloud CDN
- Backend on-premises or in cloud
- Database according to organizational preferences

## 9. Security Considerations

### 9.1 Authentication Security
- Password policies and hashing
- Session management
- JWT token security

### 9.2 API Security
- API key rotation
- Rate limiting
- Input validation

### 9.3 Data Security
- Encryption in transit (HTTPS)
- Secure credential storage
- Sensitive data handling

### 9.4 Infrastructure Security
- Network isolation
- Least privilege principle
- Regular updates and patching

## 10. Monitoring and Maintenance

### 10.1 Application Monitoring
- Error tracking
- Performance metrics
- Resource utilization

### 10.2 Backup Job Monitoring
- Success/failure tracking
- Duration and resource usage
- Error logs and diagnostics

### 10.3 Maintenance Procedures
- Database maintenance
- Backup and restore
- Version upgrades

## 11. Appendix

### 11.1 Example UI Mockups

Dashboard mockup will be added here.

### 11.2 Example API Responses

Example API response will be added here.

### 11.3 Glossary

- **RBAC**: Role-Based Access Control
- **JWT**: JSON Web Token
- **API**: Application Programming Interface
- **CI/CD**: Continuous Integration/Continuous Deployment

## 12. Revision History

| Version | Date | Description | Author |
|---------|------|-------------|--------|
| 1.0 | 2025-03-12 | Initial design document | Claude | 