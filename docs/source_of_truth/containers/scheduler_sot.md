# Scheduler Container: Intended State

## Overview

The Scheduler container serves as the central coordination hub for all device operations in the NetRaven system. It manages the scheduling, queuing, prioritization, and execution of configuration retrieval jobs and other device-related tasks, ensuring operations are performed efficiently and reliably across the deployment environment.

## Core Purpose

This container implements the Scheduler Service, which:

1. Orchestrates all device interaction operations throughout the system
2. Maintains a queue of pending jobs with appropriate prioritization
3. Executes scheduled jobs at their designated times
4. Manages recurring job scheduling with configurable patterns
5. Tracks job states and handles job lifecycle management
6. Provides a registration system for task handlers to process different job types
7. Maintains a worker pool for concurrent job execution

## Service Architecture

The Scheduler implements a multi-layered architecture that separates concerns:

### Job Management Layer

- Job definition and representation
- Job state tracking and updates
- Job creation, cancellation, and rescheduling
- Worker thread pool management
- Task handler registration and dispatch

### Scheduling Layer

- Time-based scheduling of one-time and recurring tasks
- Integration with system clock and time management
- Schedule persistence across container restarts
- Schedule pattern definition (daily, weekly, monthly)
- Schedule conflict resolution

### Queue Management Layer

- Priority-based job queue implementation
- Job sorting and prioritization
- Queue size management and throttling
- Worker thread assignment

### Integration Layer

- Communication with other system services
- Database state synchronization
- Request handling for external job submissions
- Status reporting and monitoring

## Job Types and Handlers

The Scheduler container supports the following core job types:

1. **Configuration Backup Jobs**:
   - Regular backup of device configurations
   - Comparison with previous configurations
   - Git repository commit integration

2. **Device Discovery Jobs**:
   - Scheduled network scanning
   - Device metadata collection
   - Inventory updates

3. **Status Check Jobs**:
   - Device reachability verification
   - Operational status monitoring
   - Health assessment

4. **Maintenance Jobs**:
   - Database maintenance operations
   - Log rotation and cleanup
   - System health monitoring

Each job type has a registered handler that implements the specific logic required to process that particular job type, allowing for extensibility.

## Job Execution Flow

The job execution flow follows a well-defined path:

1. **Job Creation**: A job is created through the API or scheduled creation
2. **Queue Insertion**: Job is inserted into the priority queue
3. **Worker Assignment**: Available worker thread pulls job from queue
4. **Handler Selection**: Appropriate task handler is selected based on job type
5. **Job Execution**: Task handler executes the job logic
6. **Status Update**: Job status is updated in the database
7. **Logging**: Comprehensive logging of execution details
8. **Result Storage**: Job results are stored in the database
9. **Rescheduling**: Recurring jobs are rescheduled as needed

## Containerization Details

The Scheduler container is built and configured as follows:

1. **Base Image**:
   - Python 3.10 slim image
   - Minimal dependencies to reduce attack surface

2. **Dependencies**:
   - SQLAlchemy for database access
   - Schedule library for time-based job scheduling
   - Required libraries for job processing
   - YAML for configuration parsing

3. **Configuration**:
   - Configurable number of worker threads
   - Adjustable job queue size
   - Tunable scheduling parameters
   - Customizable retry policies

4. **Environment Variables**:
   - `API_URL`: URL of the main API service
   - `NETRAVEN_ENV`: Environment (prod, test, dev)
   - `NETMIKO_LOG_DIR`: Directory for Netmiko logs
   - `NETMIKO_PRESERVE_LOGS`: Whether to preserve session logs

5. **Volume Mounts**:
   - `/app/logs`: For job execution logs
   - `/app/data/netmiko_logs`: For device session logs
   - `/app/config.yml`: Configuration file

6. **Health Management**:
   - Automatic worker thread monitoring
   - Thread restart on failure
   - Job timeout handling
   - Resource monitoring

## Interface with Other Services

The Scheduler container interacts with other services in the following ways:

1. **API Service**:
   - Receives job creation requests
   - Provides job status updates
   - Offers management endpoints

2. **Device Gateway**:
   - Dispatches device operation requests
   - Receives operation results
   - Coordinates device connection management

3. **Job Logging Service**:
   - Sends detailed logs of all job executions
   - Records job status transitions
   - Maintains audit trail of operations

4. **Database**:
   - Persists job definitions and schedules
   - Stores job execution history
   - Maintains system state across restarts

## Performance Characteristics

The Scheduler container is designed for optimal performance:

1. **Concurrency Model**:
   - Multi-threaded execution for job processing
   - Configurable worker thread pool
   - Non-blocking I/O for external service calls

2. **Resource Management**:
   - Thread pool sizing based on available resources
   - Job queue limiting to prevent memory exhaustion
   - Adaptive scheduling under high load

3. **Throttling and Rate Limiting**:
   - Device-specific operation rate limits
   - Global job execution rate limits
   - Backpressure mechanisms for overload protection

4. **Optimizations**:
   - Efficient job prioritization algorithm
   - Batched database operations
   - Caching of frequently accessed data

## Error Handling and Recovery

The Scheduler implements robust error handling:

1. **Job Failure Handling**:
   - Automatic retry with configurable policies
   - Exponential backoff for transient errors
   - Dead-letter queue for unprocessable jobs

2. **Service Recovery**:
   - Automatic service restart on failure
   - State recovery from persistent storage
   - Job resumption after service interruption

3. **Resource Protection**:
   - Thread deadlock detection and recovery
   - Memory usage monitoring
   - CPU usage throttling

4. **Error Classification**:
   - Transient vs. persistent errors
   - Resource exhaustion errors
   - Authentication and authorization errors
   - Network connectivity errors

## Monitoring and Maintenance

The Scheduler exposes monitoring capabilities:

1. **Status Information**:
   - Currently executing jobs
   - Queue depth and composition
   - Worker thread status
   - Error rates and types

2. **Performance Metrics**:
   - Job throughput
   - Average execution time
   - Queue wait time
   - Resource utilization

3. **Management Operations**:
   - Manual job creation
   - Job cancellation
   - Worker thread management
   - Schedule adjustment

## Important Product Considerations

As NetRaven is a deployable product rather than a continuously running service:

1. **Deployment Resilience**: The Scheduler container must recover gracefully from interruptions in the customer environment, maintaining job schedules and state.

2. **Resource Efficiency**: Job execution is optimized for performance in various customer environments, which may have different resource constraints.

3. **Schedule Persistence**: All schedules must be persisted to survive container restarts and system reboots in the customer environment.

4. **Configuration Simplicity**: Default configurations are optimized for typical use cases to minimize customer configuration requirements.

5. **Diagnostics**: The container provides clear diagnostic information to help customers troubleshoot scheduling issues without vendor assistance.

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