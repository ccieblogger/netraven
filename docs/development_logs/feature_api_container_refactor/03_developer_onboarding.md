# API Container Refactoring: Developer Onboarding Guide

## Introduction

This document is designed to help new developers quickly understand the API container refactoring effort and continue the work effectively. It supplements the gap analysis and implementation plan with practical context, code pointers, and implementation details.

## Project Context

The NetRaven system is a containerized application for network device configuration backup with the following key containers:
- **API Container**: Central interface for all system functionality (our focus)
- **Device Gateway Container**: Handles direct device communication 
- **Scheduler Container**: Coordinates tasks and job execution
- **PostgreSQL Container**: Provides persistent storage
- **Frontend Container**: Delivers the Vue.js user interface
- **Nginx Container**: Serves as a reverse proxy
- **Key Rotation Container**: Manages cryptographic keys

This refactoring focuses specifically on the API container, ensuring it aligns with the intended architecture defined in the `/docs/source_of_truth/` directory.

## Current State Overview

### Key Files to Understand

The API container implementation is spread across several files and directories:

1. **API Definition and Router Registration**:
   - `/netraven/web/api.py`: Defines the API router and includes sub-routers
   - `/netraven/web/app.py`: Alternative API definition with router configuration
   - `/netraven/web/main.py`: FastAPI application initialization and configuration

2. **Router Implementations**:
   - `/netraven/web/routers/`: Contains all API endpoint implementations
   - Notable routers:
     - `auth.py`: Authentication endpoints
     - `devices.py`: Device management endpoints
     - `credentials.py`: Credential management endpoints
     - `scheduled_jobs.py`: Job scheduling endpoints

3. **Service Layer**:
   - `/netraven/web/services/`: Web-specific service implementations
   - `/netraven/core/services/`: Core service implementations
   - `/netraven/core/services/service_factory.py`: Service initialization and dependency injection

4. **Database Layer**:
   - `/netraven/web/database.py`: Database connection and session management
   - `/netraven/web/models/`: Database model definitions
   - `/netraven/web/crud/`: CRUD operations for database entities

5. **Schema Definitions**:
   - `/netraven/web/schemas/`: Pydantic models for request/response validation

6. **Docker Configuration**:
   - `/docker/Dockerfile.api`: API container build definition
   - `/docker/docker-compose.yml`: Container orchestration configuration
   - `/docker/entrypoint.sh`: Container startup script

### Key Issues to Address

Based on the gap analysis, the most critical issues are:

1. **Service Boundary Violations**: The API container is directly implementing functionality that should be delegated to other services (especially device communication).

2. **Inconsistent API Structure**: The dual implementation in `api.py` and `app.py` creates confusion and inconsistency.

3. **Mixed Sync/Async Code**: The codebase mixes synchronous and asynchronous patterns, leading to potential issues.

4. **Direct Database Access from Routers**: Many router implementations access the database directly rather than going through a service layer.

5. **Incomplete Authentication**: The current JWT implementation lacks proper token refresh and scope-based authorization.

## Implementation Guide

### Phase 1: Core API Structure and Organization

#### Getting Started with Phase 1

1. **API Consolidation**:
   - Start by examining the differences between `api.py` and `app.py`
   - Determine which version should be the canonical implementation
   - Merge the router registrations into a single file
   - Update imports and references throughout the codebase

   **Example consolidation approach**:
   ```python
   # In a new consolidated file (e.g., /netraven/web/api_routes.py)
   from fastapi import APIRouter
   
   from netraven.web.routers import (
       auth, users, devices, tags, tag_rules, job_logs, scheduled_jobs,
       gateway, credentials, audit_logs, keys, backups
   )
   
   # Create the main API router
   api_router = APIRouter(prefix="/api")
   
   # Include all routers with consistent prefixing
   api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
   api_router.include_router(users.router, prefix="/users", tags=["users"])
   # ... include other routers with consistent patterns
   ```

2. **URL Pattern Standardization**:
   - Adopt a consistent URL pattern: `/api/{resource}/{id?}/{sub-resource?}`
   - Update each router to follow this pattern
   - Ensure all endpoints use appropriate HTTP methods (GET, POST, PUT, DELETE)
   
   **Example router refactoring**:
   ```python
   # Before: Mixed patterns
   @router.get("/get_device_by_id/{device_id}")
   @router.post("/create_new_device")
   
   # After: Consistent RESTful patterns
   @router.get("/{device_id}")
   @router.post("/")
   ```

3. **Middleware Pipeline**:
   - Implement a consistent middleware pipeline in `main.py`
   - Create middleware for cross-cutting concerns like logging, error handling, etc.
   
   **Example middleware implementation**:
   ```python
   # In /netraven/web/middleware/request_logging.py
   from fastapi import Request
   import time
   from netraven.core.logging import get_logger
   
   logger = get_logger("netraven.web.middleware.request_logging")
   
   async def request_logging_middleware(request: Request, call_next):
       start_time = time.time()
       response = await call_next(request)
       process_time = time.time() - start_time
       logger.info(f"Request {request.method} {request.url.path} processed in {process_time:.4f}s")
       return response
   
   # In main.py
   from netraven.web.middleware.request_logging import request_logging_middleware
   
   app.middleware("http")(request_logging_middleware)
   ```

### Phase 2: Service Layer Refactoring

#### Getting Started with Phase 2

1. **Service Factory Enhancement**:
   - Examine the current service factory implementation in `/netraven/core/services/service_factory.py`
   - Enhance it to consistently initialize all required services
   - Implement proper dependency tracking and injection
   
   **Example service factory enhancement**:
   ```python
   # In service_factory.py
   class ServiceFactory:
       def __init__(self, db_session):
           self._db_session = db_session
           self._services = {}  # Cache for initialized services
           
       def get_service(self, service_class):
           """Get or create a service instance by class."""
           if service_class not in self._services:
               # Create service instance with appropriate dependencies
               self._services[service_class] = service_class(
                   db_session=self._db_session,
                   factory=self
               )
           return self._services[service_class]
           
       # Convenience methods for common services
       @property
       def device_service(self):
           from netraven.web.services.device_service import DeviceService
           return self.get_service(DeviceService)
   ```

2. **Router Refactoring**:
   - Move business logic from routers to appropriate services
   - Replace direct database access with service calls
   
   **Example router refactoring**:
   ```python
   # Before: Direct database access
   @router.get("/{device_id}")
   async def get_device(device_id: str, db: AsyncSession = Depends(get_async_session)):
       device = await db.get(Device, device_id)
       if not device:
           raise HTTPException(status_code=404, detail="Device not found")
       return device
   
   # After: Using service layer
   @router.get("/{device_id}")
   async def get_device(
       device_id: str, 
       factory: ServiceFactory = Depends(get_service_factory)
   ):
       try:
           return await factory.device_service.get_device(device_id)
       except DeviceNotFoundError:
           raise HTTPException(status_code=404, detail="Device not found")
   ```

### Phase 3: Service Integration Architecture

#### Getting Started with Phase 3

1. **Client Adapter Implementation**:
   - Create adapter classes for the Device Gateway and Scheduler services
   - Implement proper error handling and retry logic
   
   **Example Gateway Adapter**:
   ```python
   # In /netraven/web/services/gateway_client.py
   import httpx
   from netraven.core.logging import get_logger
   
   logger = get_logger("netraven.web.services.gateway_client")
   
   class GatewayClient:
       def __init__(self, base_url):
           self.base_url = base_url
           self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
           
       async def check_device_connectivity(self, device_id, credentials):
           """Check if a device is reachable using the Device Gateway."""
           try:
               response = await self.client.post(
                   "/check-connectivity",
                   json={"device_id": device_id, "credentials": credentials}
               )
               response.raise_for_status()
               return response.json()
           except httpx.HTTPError as e:
               logger.error(f"Gateway communication error: {str(e)}")
               raise GatewayError(f"Failed to communicate with Device Gateway: {str(e)}")
   ```

2. **Removing Direct Device Communication**:
   - Identify and remove direct device communication from API code
   - Replace with calls to the Gateway Adapter
   
   **Example replacement approach**:
   ```python
   # Before: Direct device communication in API
   @router.post("/devices/{device_id}/connect")
   async def connect_to_device(device_id: str, ...):
       # Direct SSH connection code here
       
   # After: Using Gateway service
   @router.post("/devices/{device_id}/connect")
   async def connect_to_device(
       device_id: str,
       gateway_client: GatewayClient = Depends(get_gateway_client)
   ):
       return await gateway_client.connect_to_device(device_id)
   ```

## Common Implementation Pitfalls

Based on the architecture and codebase analysis, here are some common pitfalls to avoid:

1. **Circular Dependencies**: Be careful when refactoring services to avoid circular dependencies. Use dependency injection and interfaces to break cycles.

2. **Missing Error Handling**: Always handle errors properly and return appropriate HTTP status codes. Wrap external service calls in try/except blocks.

3. **Inconsistent Async/Sync**: When converting to async, ensure all calls in a chain are async. A single sync call can block the entire async chain.

4. **Premature Optimization**: Focus on correctness and architecture alignment first. Performance optimizations can come after the basics are working correctly.

5. **Inadequate Testing**: Each change should be accompanied by appropriate tests. Without tests, it's easy to break existing functionality.

## Useful Development Commands

Here are some helpful commands for developing and testing the API container:

### Building and Running the Container
```bash
# Build and run the API container
docker-compose -f docker/docker-compose.yml build api
docker-compose -f docker/docker-compose.yml up -d api

# View logs
docker-compose -f docker/docker-compose.yml logs -f api

# Run tests
docker-compose -f docker/docker-compose.yml run --rm api pytest tests/
```

### Code Organization
```bash
# Check code style
flake8 netraven/web/

# Run unit tests for a specific module
pytest tests/unit/web/test_api.py -v
```

## Next Steps for a New Developer

If you're taking over this project, here's a recommended approach:

1. **Understand the Architecture**: Review the source of truth documents in `/docs/source_of_truth/` to understand the intended architecture.

2. **Familiarize with Codebase**: Explore the key files and directories mentioned in the "Current State Overview" section.

3. **Run the Application**: Build and run the containers to see the current state of the application.

4. **Start with Phase 1**: Begin implementation with Phase 1 tasks, focusing on API structure consolidation.

5. **Write Tests First**: For each change, write tests first to ensure the functionality works as expected after refactoring.

6. **Document Your Progress**: Update the development logs with your findings and implementation details.

## Conclusion

This guide should provide you with the necessary context and starting points to continue the API container refactoring. Remember to follow the project's coding principles and maintain backward compatibility as you implement changes.

If you encounter issues or have questions, refer to the source of truth documentation or consult with the team for clarification. 