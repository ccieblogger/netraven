# NetRaven Architecture Redesign: Scheduling, Job Logging, and Device Communication

## Executive Summary

This document outlines a comprehensive plan to redesign and improve three core components of the NetRaven system:
1. **Scheduler Service** - Centralizing all device interactions
2. **Job Logging Service** - Creating a unified logging system for operations
3. **Device Communication Service** - Enhancing and standardizing device interactions

The redesign aims to improve system reliability, maintainability, and scalability while reducing code duplication and complexity.

## Current Architecture Assessment

Based on code review, NetRaven currently has several interconnected but not fully centralized components:

1. **Device Communication** - Implemented in `DeviceConnector` and `JobDeviceConnector` classes with significant duplication
2. **Job Tracking** - Scattered across multiple components with inconsistent implementation
3. **Scheduling** - Not fully centralized; device communication can be initiated from multiple places
4. **Error Handling** - Complex and duplicated across components

## Goals and Requirements

1. **Centralized Device Communication**
   - All device interactions must flow through the Scheduler Service
   - Create a single point of control for all device operations

2. **Comprehensive Job Logging**
   - Track the full lifecycle of jobs and tasks
   - Filter sensitive information automatically
   - Provide structured and searchable log data

3. **Enhanced Device Communication**
   - Implement connection pooling for improved performance
   - Create a unified error handling model
   - Support additional protocols beyond SSH
   - Improve testability and reduce duplication

## Proposed Architecture

### Component Diagram

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
        └─────────────────►│                    │◄────────────┘
                           │  Job Logging       │
                           │  Service           │
                           │                    │
                           └────────────────────┘
                                    │
                                    ▼
                           ┌────────────────────┐
                           │                    │
                           │     Database       │
                           │                    │
                           └────────────────────┘
```

### Workflow Diagram

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐     ┌──────────┐
│          │     │          │     │          │     │            │     │          │
│  Client  │────►│   API    │────►│Scheduler │────►│Device Comm │────►│ Network  │
│          │     │          │     │          │     │            │     │ Device   │
└──────────┘     └──────────┘     └──────────┘     └────────────┘     └──────────┘
                                      │                  │
                                      │                  │
                                      ▼                  ▼
                                 ┌────────────────────────────┐
                                 │                            │
                                 │      Job Logging Service   │
                                 │                            │
                                 └────────────────────────────┘
                                              │
                                              ▼
                                 ┌────────────────────────────┐
                                 │                            │
                                 │         Database           │
                                 │                            │
                                 └────────────────────────────┘
```

## Key Components

### 1. Job Logging Service

A centralized service responsible for collecting, processing, and storing all job-related log events.

**Core Classes and Functions:**
- `JobLogEntry` - Structured representation of a log entry
- `JobLoggingService` - Main service interface for logging operations
- `SensitiveDataFilter` - Component to identify and redact sensitive information

**Key Features:**
- Structured logging with consistent schema
- Automated filtering of sensitive data (passwords, keys)
- Support for different log levels and categories
- Query capabilities for job history and status

### 2. Scheduler Service

The central coordination point for all device-related operations, ensuring consistent execution and tracking.

**Core Classes and Functions:**
- `Job` - Representation of a scheduled task
- `JobStatus` - Enumeration of possible job states
- `SchedulerService` - Main service interface for job operations
- `JobQueue` - Priority-based job queue implementation

**Key Features:**
- Single entry point for all device interactions
- Job state management (queued, running, completed, failed)
- Scheduling with various timing options
- Integration with Job Logging Service

### 3. Device Communication Service

A redesigned service for device interactions with improved architecture and capabilities.

**Core Classes and Functions:**
- `DeviceError` - Unified error representation
- `DeviceTypeManager` - Handles device type detection
- `DeviceProtocolAdapter` - Interface for different connection protocols
- `DeviceConnectionManager` - Handles connection pooling and reuse
- `DeviceCommunicationService` - Main service interface for device operations

**Key Features:**
- Unified error handling model
- Protocol abstraction (SSH, Telnet, HTTP/REST)
- Connection pooling for improved performance
- Integration with credential management system

## Integration with Existing Systems

### Authentication System Integration

The redesigned components will leverage the existing authentication system:

- **API Gateway**: Will continue to validate all API requests against the authentication system
- **Scheduler Service**: Will verify user permissions before scheduling or modifying jobs
- **Job Logging Service**: Will inherit user context from authenticated requests for auditing
- **Device Communication Service**: Will use authenticated contexts when accessing device credentials

Authentication flows will be preserved with these enhancements:
- Role-based access control for job operations
- Audit trails capturing which users initiated which jobs
- Permission verification for accessing job logs

### Application Logging System Integration

The Job Logging Service will complement rather than replace the application logging system:

- **Operational Events**: Will be logged to both systems with appropriate context
- **Exception Handling**: Application exceptions will be logged to the application logging system while job-specific failures will additionally be recorded in job logs
- **Correlation IDs**: Will link application logs with job logs for comprehensive traceability
- **Log Levels**: Will be synchronized between systems to maintain consistent visibility

### Credential System Integration

The Device Communication Service will integrate tightly with the existing credential management system:

- **Credential Retrieval**: Will use the credential store API to obtain device credentials
- **Success/Failure Tracking**: Will update credential statistics based on connection outcomes
- **Smart Credential Selection**: Will leverage credential prioritization mechanisms
- **Secure Handling**: Will follow established patterns for secure credential usage

## Implementation Strategy

### Phase 1: Core Architecture Refactoring (8-10 weeks)

1. **Create Job Logging Service** (3 weeks)
   - Define structured log schema
   - Implement sensitive data filtering
   - Create storage and query interfaces

2. **Refactor Scheduler Service** (3 weeks)
   - Centralize all device interaction through scheduler
   - Implement job state management
   - Create interfaces with Device Communication Service

3. **Refactor Device Communication Service** (4 weeks)
   - Implement unified error model
   - Eliminate duplication between DeviceConnector implementations
   - Extract device type detection to separate class
   - Add integration with Job Logging Service

### Phase 2: Enhanced Features (6-8 weeks)

1. **Implement Connection Pooling** (2 weeks)
   - Add connection reuse capabilities
   - Implement connection lifecycle management

2. **Add Protocol Abstraction** (3 weeks)
   - Create protocol adapters
   - Add support for additional protocols

3. **Enhance Scheduler Capabilities** (3 weeks)
   - Add job dependencies
   - Implement advanced scheduling options
   - Add job prioritization

### Phase 3: Advanced Improvements (4-6 weeks)

1. **Add Async Support** (2 weeks)
   - Implement async versions of key operations
   - Optimize for high concurrency

2. **Enhance Command Templating** (2 weeks)
   - Create command template system
   - Add output parsing capabilities

3. **Implement Advanced Error Recovery** (2 weeks)
   - Add automatic retry strategies
   - Implement circuit breaker patterns

## Technical Implementation Details

### API & Interface Specifications

#### REST API Contracts
All service APIs will follow REST principles and be documented using OpenAPI 3.0:
- **Scheduler Service API**: `/api/v1/jobs/` for job management operations
- **Job Logging Service API**: `/api/v1/logs/` for log retrieval and management
- **Device Communication Service API**: `/api/v1/devices/communication/` for device operations

An example OpenAPI specification excerpt for the Scheduler Service:
```yaml
paths:
  /api/v1/jobs:
    post:
      summary: Create a new job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/JobCreate'
      responses:
        '201':
          description: Job created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Job'
```

#### Inter-Service Communication
- **Primary Pattern**: REST over HTTP for synchronous operations
- **Event Communication**: For asynchronous workflows, we'll use RabbitMQ message queues
- **Message Formats**: All messages will use JSON with standardized envelope format:
  ```json
  {
    "metadata": {
      "correlation_id": "uuid-string",
      "timestamp": "ISO-datetime",
      "source": "service-name"
    },
    "payload": { /* operation-specific data */ }
  }
  ```

### Asynchronous & Concurrency Considerations

#### Async Implementation Strategy
- **Framework**: FastAPI for async HTTP endpoints
- **Worker Framework**: Celery for background task processing
- **Libraries**: Python's asyncio for core async operations
- **Transition Approach**: 
  1. Initial implementation with synchronous methods
  2. Add async equivalents with `_async` suffix
  3. Default to async implementation when mature

#### Connection Pool Configuration
```python
# Connection Pool Configuration
CONNECTION_POOL_CONFIG = {
    "max_pool_size": 50,
    "min_idle": 5,
    "max_idle_time_sec": 300,
    "connection_timeout_sec": 30,
    "keep_alive_interval_sec": 60,
    "per_host_limit": 5
}
```

### Error Handling & Resilience

#### Error Propagation Standards
- **HTTP Error Codes**: Follow standard REST error codes (400-599)
- **Error Response Format**:
  ```json
  {
    "error": {
      "code": "ERROR_CODE",
      "message": "Human-readable message",
      "details": { /* additional context */ },
      "correlation_id": "uuid-for-tracing"
    }
  }
  ```
- **Logging**: All errors must be logged with correlation ID and stacktrace

#### Retry Policies
Standard retry configuration applied consistently across services:
```python
# Standard Retry Configuration
RETRY_CONFIG = {
    "max_attempts": 3,
    "initial_backoff_ms": 500,
    "max_backoff_ms": 10000,
    "backoff_multiplier": 2.0,
    "retry_codes": [
        "UNAVAILABLE", "ABORTED", "DEADLINE_EXCEEDED"
    ]
}
```

### Testing Strategy

#### Test Levels
1. **Unit Tests**: Minimum 80% code coverage for all components
2. **Integration Tests**: Service to service, focusing on API contracts
3. **System Tests**: End-to-end operational flows
4. **Performance Tests**: Connection pooling, concurrency, and throughput

#### Mocking Strategy
- Use pytest-mock for unit test mocking
- Dedicated mock servers for device simulation
- Sample test structure:
  ```python
  def test_device_connection_retry(mock_device_server):
      # Given a device that will fail authentication once then succeed
      mock_device_server.configure(auth_failures=1, then_succeed=True)
      
      # When connecting to the device
      result = device_comm_service.connect_to_device("device-001")
      
      # Then connection succeeds after retry
      assert result.success is True
      assert result.attempts == 2
  ```

### Containerization & Deployment

#### Container Guidelines
Each service will have a standardized Dockerfile structure:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Configuration Management
- Environment-specific configs in `.env` files (not committed to source control)
- Kubernetes ConfigMaps for non-sensitive configuration
- Kubernetes Secrets for sensitive data
- Centralized configuration validation at startup

### Security Implementation

#### Authentication Flow
1. API Gateway validates JWT tokens from auth service
2. Internal service communication uses service account tokens
3. Token format: JWTs with role-based access claims
4. Token validation at service boundaries using shared library

#### Credential Storage
- Credentials encrypted at rest using AES-256
- Key rotation support with versioned keys
- Credentials never logged, even in debug mode
- In-memory cache with short TTL for performance

### Documentation Requirements

#### Code Documentation Standards
- Docstrings for all public methods (Google style)
- Architecture decision records (ADRs) for significant choices
- README in each component directory
- Interface definitions in separate files with full documentation

#### Living Documentation
- OpenAPI specs auto-generated from code
- Sequence diagrams for key workflows
- Component dependency graphs maintained with code

## Source Control and Release Strategy

### Branching Strategy

NetRaven will adopt a Git Flow branching strategy to support the architecture redesign implementation:

```
┌─────────── hotfix/x.y.z ───────┐
│                                 ▼
main ───────────────────────────────────────────────────────────►
 ▲                               ▲
 │                               │
 │                       release/x.y.0
 │                               ▲
 │                               │
develop ─────────────────────────┴───────────────────────────────►
 ▲       ▲        ▲
 │       │        │
 │       │        └── feature/device-comm-service
 │       └────────── feature/job-logging-service
 └─────────────────── feature/scheduler-service
```

**Core Branches:**
- **`main`**: Production code; always in a deployable state
- **`develop`**: Integration branch for completed features
- **`feature/*`**: Individual feature development branches
- **`release/*`**: Release candidate branches for testing and finalization
- **`hotfix/*`**: Emergency fixes for production issues

### Branch Naming Conventions

```
feature/[phase]-[component]-[description]
release/0.x.0
hotfix/0.x.y
```

Examples:
- `feature/phase1-job-logging-schema`
- `feature/phase1-scheduler-api`
- `release/0.2.0`
- `hotfix/0.1.1-credential-timeout-fix`

### Versioning Strategy

Starting from the current pre-release version of v0.0.1, we will progress through development milestones:

1. **Phase 1 Completion**: v0.1.0 (alpha/beta releases as needed)
2. **Phase 2 Completion**: v0.2.0 (alpha/beta releases as needed)
3. **Phase 3 Completion**: v0.3.0 (alpha/beta releases as needed)
4. **Production Release**: v1.0.0

**Pre-release tags** will follow the format: `v0.x.0-alpha.1`, `v0.x.0-beta.1`, etc.
**Release candidates** will use: `v0.x.0-rc.1`, `v0.x.0-rc.2`, etc.

### Development Workflow

1. **Feature Development**:
   - Create feature branch from `develop`
   - Implement and test feature
   - Submit PR/MR for code review
   - Merge to `develop` when approved

2. **Release Preparation**:
   - Create `release/0.x.0` branch from `develop` at phase completion
   - Perform integration testing
   - Fix any release-blocking issues directly in release branch
   - Update version numbers and documentation

3. **Release Finalization**:
   - Tag the release (e.g., `v0.1.0`)
   - Merge release branch to `main`
   - Merge release branch back to `develop`

4. **Hotfixes** (if needed):
   - Create `hotfix/0.x.y` branch from `main`
   - Fix the issue and increment patch version
   - Merge back to both `main` and `develop`
   - Tag with new patch version

### Feature Flags

To support gradual deployment and risk mitigation, feature flags will be used:

- Each major component will have a feature flag in configuration
- New implementations will run alongside legacy code during transition
- Flags can be activated per environment (development, staging, production)
- Once a feature is stable, its flag is enabled by default and eventually removed

### Phase-Specific Git Workflow

**Phase 1: Core Architecture Refactoring**
- Branch: `develop` with feature branches for each major component
- Release: `v0.1.0` upon completion
- Testing: Unit tests and integration tests on isolated components

**Phase 2: Enhanced Features**
- Branch: Feature branches from updated `develop` branch
- Release: `v0.2.0` upon completion
- Testing: Expanded testing including performance benchmarks

**Phase 3: Advanced Improvements**
- Branch: Feature branches for async, templating, and error recovery
- Release: `v0.3.0` or `v1.0.0` depending on production readiness
- Testing: Full system testing, stress testing, and production simulations

## Migration Strategy

To ensure smooth transition while maintaining system stability:

1. **Create new components alongside existing ones**
   - Build the new Job Logging Service first
   - Integrate it with existing components
   - Ensure all authentication contexts are properly propagated
   
2. **Gradually migrate functionality**
   - Start redirecting device communication through the scheduler
   - Update each component to use the new logging system
   - Maintain backward compatibility with credential system interfaces
   
3. **Phase out old implementations**
   - Once all functionality is migrated, remove old implementations
   - Ensure backward compatibility for API consumers
   - Verify that all security controls and authentication requirements are preserved

## Implementation Guidelines and Coding Principles

The following principles **must** be adhered to when implementing this architecture redesign plan:

### Code Quality and Structure

- **Simplicity First**: Always prefer simple solutions over complex ones, even if it means more code.
- **Avoid Code Duplication**: Before writing new code, check if similar functionality exists elsewhere in the codebase that can be reused or refactored.
- **Module Size Limits**: Keep files under 200-300 lines of code. When a file exceeds this limit, refactor it into multiple focused modules.
- **Scope Discipline**: Only make changes that are directly requested or related to the task at hand. Avoid "scope creep" during implementation.

### Technology ChoicesBria

- **Conservative Enhancement**: When fixing bugs or issues, exhaust all options with existing patterns and technologies before introducing new ones.
- **Legacy Code Replacement**: If introducing a new pattern or technology is necessary, completely remove the old implementation to prevent duplicate logic and legacy code fragments.
- **Deployment Awareness**: Always consider how changes will affect the containerized deployment model, and ensure that deployment configurations are updated accordingly.

### Development Practices

- **Clean Workspace**: Remove temporary files, debug code, and commented-out sections before considering work complete.
- **Avoid In-File Scripts**: Do not embed one-off scripts or temporary code within production files.
- **Test Data Discipline**: Use mocking only in test code, never in development or production environments.
- **No Stub Patterns**: Never add stubbing or fake data patterns to code affecting development or production environments.

### Process Requirements

- **Phased Planning**: Always present a plan outlining proposed changes, broken into manageable phases, and wait for approval before proceeding.
- **Sequential Execution**: Ask for permission before moving to the next phase of an approved plan.
- **Source Control Discipline**: Commit and push code after successful completion of each phase with clear, descriptive commit messages.
- **Transparent Communication**: Provide clear explanations during coding, testing, and making changes, without being overly verbose.

These principles are non-negotiable requirements for all implementation work related to this architecture redesign. They ensure code quality, maintainability, and proper integration with existing systems.

## Appendix A: Key Interface Definitions

### Job Logging Service

```python
class JobLogEntry:
    """Structured representation of a job log entry"""
    job_id: str
    timestamp: datetime
    level: str  # INFO, WARNING, ERROR, CRITICAL
    category: str  # connection, execution, result, etc.
    message: str
    details: Dict[str, Any]
    source_component: str
    
class JobLoggingService:
    """Central service for job logging"""
    def log_entry(self, entry: JobLogEntry) -> None: ...
    def get_job_logs(self, job_id: str) -> List[JobLogEntry]: ...
    def filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
```

### Scheduler Service

```python
class Job:
    """Representation of a scheduled job"""
    id: str
    type: str  # backup, command_execution, etc.
    parameters: Dict[str, Any]
    device_id: Optional[str]
    status: JobStatus
    created_at: datetime
    scheduled_for: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
class SchedulerService:
    """Centralized scheduler for all device operations"""
    def schedule_job(self, job_type: str, parameters: Dict[str, Any], 
                    schedule_time: Optional[datetime] = None) -> Job: ...
    def execute_job(self, job: Job) -> JobResult: ...
    def get_job_status(self, job_id: str) -> JobStatus: ...
```

### Device Communication Service

```python
class DeviceError:
    """Unified error representation"""
    error_type: str  # authentication, timeout, connection
    message: str
    details: Dict[str, Any]
    timestamp: datetime

class DeviceProtocolAdapter:
    """Interface for different protocol implementations"""
    def connect(self) -> bool: ...
    def disconnect(self) -> bool: ...
    def send_command(self, command: str) -> str: ...
    
class DeviceCommunicationService:
    """Main service for device communication"""
    def connect_to_device(self, device_id: str, job_id: str) -> bool: ...
    def execute_command(self, device_id: str, command: str, job_id: str) -> CommandResult: ...
    def get_device_config(self, device_id: str, config_type: str, job_id: str) -> str: ...
```

### Authentication Integration

```python
class AuthenticationContext:
    """Authentication context for job operations"""
    user_id: str
    roles: List[str]
    permissions: List[str]
    
class JobPermissionVerifier:
    """Verifies permissions for job operations"""
    def can_create_job(self, auth_context: AuthenticationContext, job_type: str) -> bool: ...
    def can_access_job(self, auth_context: AuthenticationContext, job_id: str) -> bool: ...
    def can_access_device(self, auth_context: AuthenticationContext, device_id: str) -> bool: ...
```

### Credential System Integration

```python
class CredentialManager:
    """Interface to the credential system"""
    def get_device_credentials(self, device_id: str, auth_context: AuthenticationContext) -> List[Credential]: ...
    def update_credential_status(self, credential_id: str, success: bool, context: Dict[str, Any]) -> None: ...
    def get_smart_credential_selection(self, device_id: str, tag_id: Optional[str] = None) -> List[Credential]: ...
```

### Application Logging Integration

```python
class LoggingContext:
    """Context linking application and job logs"""
    correlation_id: str
    job_id: Optional[str]
    request_id: str
    
class ApplicationLogger:
    """Application logging interface"""
    def log(self, level: str, message: str, context: LoggingContext, 
            additional_data: Optional[Dict[str, Any]] = None) -> None: ...
```

## Appendix B: References

- Current implementation in `/netraven/core/device_comm.py` and `/netraven/jobs/device_connector.py`
- DevOps best practices for microservice architecture
- [Gateway Overview Documentation](/home/netops/Projects2025/python/netraven/docs/iadocs/gateway-documentation/gateway-overview.md)
- [Job Logging Overview Documentation](/home/netops/Projects2025/python/netraven/docs/iadocs/gateway-documentation/job-logging-overview.md)
- [Device Communication Documentation](/home/netops/Projects2025/python/netraven/docs/iadocs/gateway-documentation/device-comm-documentation.md)
