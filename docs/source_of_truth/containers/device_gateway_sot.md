# Device Gateway Container: Intended State

## Overview

The Device Gateway container serves as the specialized communication interface between the NetRaven system and network devices. It provides a secure, standardized API for executing commands and retrieving configurations from diverse network equipment while abstracting protocol complexities and managing connection resources efficiently.

## Core Purpose

This container exposes the Device Communication Service capabilities through a RESTful API that:

1. Establishes secure connections to network devices using various protocols
2. Executes commands and retrieves configurations from devices
3. Abstracts protocol differences behind a unified interface
4. Manages a pool of connections for efficient resource utilization
5. Provides standardized error handling and reporting
6. Integrates with the Job Logging service for comprehensive operation tracking

## Service Architecture

The Device Gateway implements a layered architecture that separates concerns:

### API Layer

- RESTful endpoints built with Flask/FastAPI
- Authentication middleware for validating requests
- Request/response formatting and validation
- Integration with the job logging system

### Protocol Abstraction Layer

- Implementation of the `DeviceProtocolAdapter` interface
- Support for multiple communication protocols:
  - SSH (primary protocol via Netmiko)
  - Telnet (for legacy devices)
  - HTTP/REST (for API-enabled devices)
- Command normalization across different device types
- Unified error handling mechanism

### Connection Management Layer

- Connection pooling to optimize resource usage
- Connection lifecycle management (creation, validation, cleanup)
- Dynamic timeout and retry handling
- Monitoring of connection health and statistics

## API Endpoints

The Device Gateway exposes the following RESTful endpoints:

### Device Connectivity

- `GET /health`: Gateway health check
- `POST /check-connectivity`: Verify device reachability
- `GET /devices`: List currently connected devices

### Device Operations

- `POST /connect`: Establish a connection to a network device
- `POST /disconnect`: Close an active device connection
- `POST /execute-command`: Execute a command on a connected device
- `POST /execute-commands`: Execute multiple commands in sequence
- `GET /config/{config_type}`: Retrieve a specific configuration type (running, startup)
- `GET /device-info`: Retrieve identifying information from a device

All endpoints return standardized JSON responses with consistent status codes and error formats.

## Security Model

The Device Gateway implements a comprehensive security model:

1. **Authentication**:
   - API key authentication for internal service-to-service communication
   - JWT token validation for web UI initiated requests
   - Requests must include appropriate credentials in headers

2. **Credential Handling**:
   - Device credentials (passwords, keys) are never stored in the container
   - Credentials are passed for each connection request
   - Memory handling techniques to minimize credential exposure

3. **Connection Security**:
   - SSH with key or password authentication
   - Support for strict host key checking
   - TLS for API communications
   - Connection timeouts to limit exposure

4. **Access Control**:
   - All operations are validated against the requester's permissions
   - Integration with central permission model
   - Audit logging of all access attempts

## Containerization Details

The Device Gateway container is built and configured as follows:

1. **Base Image**:
   - Python 3.10 slim image
   - Minimal dependencies to reduce attack surface

2. **Dependencies**:
   - Netmiko for network device communication
   - Flask/Gunicorn for API exposure
   - Required libraries for protocol implementations
   - Monitoring and logging libraries

3. **Exposed Ports**:
   - Port 8001 for API access (internal to Docker network)

4. **Environment Variables**:
   - `API_URL`: URL of the main API service
   - `NETRAVEN_ENV`: Environment (prod, test, dev)
   - `NETMIKO_LOG_DIR`: Directory for Netmiko logs
   - `NETMIKO_PRESERVE_LOGS`: Whether to preserve session logs

5. **Volume Mounts**:
   - `/app/data/netmiko_logs`: For connection logs
   - `/app/config.yml`: Configuration file
   - `/app/tokens`: For authentication tokens

6. **Health Checks**:
   - HTTP endpoint to verify container health
   - Connection pool monitoring
   - Resource usage checks

## Interface with Other Services

The Device Gateway interacts with other services as follows:

1. **Scheduler Service**:
   - Receives job requests for device operations
   - Reports job status and results

2. **Job Logging Service**:
   - Sends detailed logs of all device operations
   - Includes structured information about connections, commands, and responses
   - Filters sensitive data before logging

3. **Database**:
   - Retrieves device metadata for specialized handling
   - Updates device status information
   - Records device details discovered during connections

4. **Credential Store**:
   - Receives credentials for device authentication
   - Reports success/failure of credential usage

## Performance Characteristics

The Device Gateway is designed for efficient performance:

1. **Connection Pooling**:
   - Maintains a configurable pool of active connections
   - Reuses connections where possible
   - Implements connection aging and renewal

2. **Concurrency**:
   - Handles multiple simultaneous device connections
   - Uses asynchronous operations where supported
   - Implements request queuing when needed

3. **Resource Management**:
   - Enforces connection limits to prevent resource exhaustion
   - Implements graceful degradation under high load
   - Auto-closes idle connections

4. **Optimizations**:
   - Persistent SSH connections when supported
   - Command batching for efficiency
   - Response streaming for large outputs

## Logging and Monitoring

The Device Gateway implements comprehensive logging:

1. **Structured Logging**:
   - JSON-formatted logs for machine readability
   - Consistent schema across all log entries
   - Context correlation IDs for tracking operations

2. **Log Categories**:
   - Connection events (connect, disconnect, failures)
   - Command execution (commands, responses, timing)
   - Error conditions with detailed context
   - Performance metrics and statistics

3. **Monitoring Endpoints**:
   - `/metrics`: Prometheus-compatible metrics endpoint
   - `/status`: Detailed status information
   - Connection pool statistics

4. **Sensitive Data Handling**:
   - Automatic redaction of passwords and sensitive data
   - Configurable patterns for identifying sensitive information
   - Safe logging practices throughout

## Error Handling

The Device Gateway implements a robust error handling system:

1. **Error Classification**:
   - Connection errors (network, authentication, timeout)
   - Command errors (syntax, execution, permission)
   - Protocol errors (unsupported features, version mismatch)
   - System errors (resource constraints, internal errors)

2. **Error Responses**:
   - Standardized JSON error format
   - HTTP status codes matched to error types
   - Detailed error information for troubleshooting
   - User-friendly error messages

3. **Retry Mechanism**:
   - Automatic retry for transient errors
   - Exponential backoff for connection issues
   - Circuit breaker pattern for persistent failures

## Important Product Considerations

As NetRaven is a deployable product rather than a continuously running service:

1. **Deployment Flexibility**: The Device Gateway container must operate correctly in diverse customer network environments without manual tuning.

2. **Resource Efficiency**: Connection pooling and management are optimized for the constraints of customer environments, which may have limited resources.

3. **Network Positioning**: The container requires network access to both the internal NetRaven components and the customer's network devices.

4. **Security Isolation**: The container maintains strict security boundaries to protect both customer device credentials and the NetRaven system.

5. **Configuration Simplicity**: Default configurations are optimized for typical use cases to minimize the need for customer configuration.

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