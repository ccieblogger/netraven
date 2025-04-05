# API Container: Intended State

## Overview

The API container serves as the central interface for the NetRaven system, providing a comprehensive set of REST endpoints that allow users and other services to interact with the platform. It implements a secure, well-structured, and documented FastAPI application that exposes all core functionality while enforcing proper authentication, authorization, and data validation.

## Core Purpose

This container delivers the API layer of the system that:

1. Exposes REST endpoints for all NetRaven functionality
2. Manages user authentication and authorization
3. Enforces security policies and access controls
4. Provides API documentation and interactive testing
5. Implements data validation and error handling
6. Coordinates communication between frontend and backend services
7. Serves as the integration point for client applications

## Service Architecture

The API container implements a layered architecture that follows modern API design practices:

### Routing Layer

- FastAPI router implementation with endpoint grouping by domain
- URL versioning and consistent path structure
- HTTP method mapping to appropriate operations
- Middleware integration for cross-cutting concerns

### Authentication and Authorization Layer

- Token-based authentication with JWT
- Role-based access control
- Scope-based permission model
- Token issuance, validation, and refresh
- Request-level authorization checks

### Request Handling Layer

- Input validation using Pydantic models
- Request preprocessing and normalization
- Parameter parsing and type conversion
- Request logging and audit trail generation

### Business Logic Layer

- Service integration for core functionality
- Transaction management
- Delegation to appropriate service handlers
- Domain object management

### Response Formatting Layer

- Standardized response structure
- Consistent error reporting
- Pagination handling for list endpoints
- Data transformation and serialization
- Content type negotiation

## API Endpoints

The API container exposes endpoints organized into the following functional areas:

### Authentication and User Management

- `/api/auth/token`: Obtain authentication tokens
- `/api/auth/refresh`: Refresh expired tokens
- `/api/auth/me`: Get current user information
- `/api/users/*`: User management endpoints

### Device Management

- `/api/devices/*`: Network device CRUD operations
- `/api/devices/{id}/status`: Device status checking
- `/api/devices/{id}/configs`: Device configuration management
- `/api/devices/discovery/*`: Network discovery operations

### Tag Management

- `/api/tags/*`: Tag CRUD operations
- `/api/tag-rules/*`: Tag rule management
- `/api/devices/{id}/tags`: Device tag assignments

### Credential Management

- `/api/credentials/*`: Credential CRUD operations
- `/api/credentials/test`: Credential validation endpoints
- `/api/keys/*`: Encryption key management

### Job Management

- `/api/scheduled-jobs/*`: Scheduled job operations
- `/api/job-logs/*`: Job logging and history

### Backup Management

- `/api/backups/*`: Configuration backup operations
- `/api/backups/history/*`: Backup history and comparison

### System Administration

- `/api/admin-settings/*`: System settings management
- `/api/audit-logs/*`: System audit logs

### Gateway Operations

- `/api/gateway/*`: Device Gateway interaction endpoints

All endpoints include comprehensive schema validation, error handling, and documentation via OpenAPI.

## Security Model

The API container implements a robust security model:

1. **Authentication**:
   - JWT token-based authentication
   - Token expiration and refresh mechanisms
   - Password hashing and validation
   - Login rate limiting and account lockout

2. **Authorization**:
   - Role-based access control
   - Scope-based permissions
   - Resource ownership validation
   - Hierarchical permission structure

3. **Transport Security**:
   - HTTPS enforcement (via reverse proxy)
   - Secure header policies
   - CORS configuration

4. **Data Protection**:
   - Input validation and sanitization
   - SQL injection prevention
   - Sensitive data filtering in logs
   - Proper error handling to prevent information leakage

5. **API Protection**:
   - Rate limiting
   - Request throttling
   - API usage monitoring

## Containerization Details

The API container is built and configured as follows:

1. **Base Image**:
   - Python 3.10 slim image
   - Non-root user execution

2. **Dependencies**:
   - FastAPI framework
   - SQLAlchemy ORM
   - Pydantic for validation
   - JWT libraries for authentication
   - Required libraries for networking and communication

3. **Exposed Ports**:
   - Port 8000 for API access

4. **Environment Variables**:
   - `DATABASE_URL`: PostgreSQL connection string
   - `TOKEN_SECRET_KEY`: Secret key for JWT token generation
   - `TOKEN_EXPIRY_HOURS`: JWT token lifetime
   - `NETRAVEN_ENV`: Environment (prod, test, dev)
   - `GATEWAY_URL`: URL of the Device Gateway service
   - `CORS_ORIGINS`: Allowed origins for CORS

5. **Volume Mounts**:
   - `/app/data`: For persistent API data
   - `/app/config.yml`: Configuration file
   - `/app/data/netmiko_logs`: For device session logs

6. **Health Checks**:
   - HTTP endpoint to verify API responsiveness
   - Database connection validation
   - Service dependency checks

## Interface with Other Services

The API container interacts with other services in the following ways:

1. **PostgreSQL Database**:
   - Stores and retrieves all persistent data
   - Manages user accounts and credentials
   - Tracks device information and configurations

2. **Frontend**:
   - Serves API requests from the Vue.js frontend
   - Provides authentication and session management
   - Delivers data for UI rendering

3. **Device Gateway**:
   - Forwards device operation requests
   - Receives device communication results
   - Coordinates device interaction

4. **Scheduler Service**:
   - Manages job scheduling and execution
   - Receives job status updates
   - Coordinates scheduled operations

5. **Job Logging Service**:
   - Records API operation activities
   - Provides access to operation history
   - Maintains audit trail

## Performance Characteristics

The API container is designed for optimal performance:

1. **Request Handling**:
   - Asynchronous request processing
   - Connection pooling for database access
   - Efficient route handling

2. **Resource Management**:
   - Optimized memory usage
   - Database query optimization
   - Connection pooling

3. **Scaling Considerations**:
   - Stateless design for horizontal scaling
   - Minimal in-memory state
   - Efficient use of shared resources

4. **Caching**:
   - Strategic response caching where appropriate
   - Cache invalidation on data changes
   - Optimized database query patterns

## Documentation and Developer Experience

The API container provides comprehensive documentation:

1. **OpenAPI Documentation**:
   - Interactive Swagger UI at `/api/docs`
   - Complete schema documentation
   - Example requests and responses

2. **Authentication Documentation**:
   - Clear instructions for token acquisition
   - Scope and permission details
   - Authentication error responses

3. **Error Documentation**:
   - Standardized error format
   - Clear error messages
   - Error code documentation

4. **Rate Limiting Information**:
   - Headers showing rate limit status
   - Clear messaging on limit exceeded
   - Documentation of limits by endpoint

## Important Product Considerations

As NetRaven is a deployable product rather than a continuously running service:

1. **API Stability**: The API design follows a versioned approach to ensure backward compatibility and smooth upgrades for customers.

2. **Security Configuration**: Default security settings are robust, but can be customized to fit customer security policies through configuration.

3. **Performance Tuning**: The API container includes configuration options for customers to tune performance based on their environment constraints.

4. **Integration Points**: Well-documented API endpoints enable customers to integrate with their existing systems and workflows.

5. **Documentation**: Embedded API documentation makes the product self-documenting for customer developers and administrators.

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