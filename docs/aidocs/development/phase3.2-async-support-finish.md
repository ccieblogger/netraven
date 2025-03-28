# Phase 3.2: Async Support Completion Plan

## Overview

This document outlines the implementation plan to complete the async support feature for NetRaven. The project has already implemented partial async support, including async database integration, async compatible database models, and SQLAlchemy async features. This phase will focus on completing the remaining async implementations to ensure all components work properly in both synchronous and asynchronous contexts.

## Current Status

As of May 2025, async support is approximately 80% complete with the following components implemented:

- ✅ Async database integration
- ✅ Async compatible database models
- ✅ Integration of SQLAlchemy async features
- ✅ Modified `ensure_schema.py` to work with async engines
- ✅ Updated tag CRUD operations to handle both async and sync sessions
- ✅ Docker container compatibility fixes for async environment

## Remaining Tasks

1. **CRUD Operations**
   - Complete migration of remaining CRUD operations to support async patterns
   - Ensure backwards compatibility with synchronous code

2. **Service Functions**
   - Implement async versions of remaining service functions
   - Add proper error handling for async contexts

3. **Test Suite**
   - Complete the async test suite implementation
   - Fix the SQLAlchemy NullPool dependency issue in tests

## Implementation Plan

### Phase 1: Setup and Analysis (1 day)

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/phase3.2-async-support-finish
   ```

2. **Analyze Remaining Non-Async Code**
   - Identify all remaining CRUD operations that need async versions
   - Catalog service functions that require async implementations
   - Document the dependency issue with SQLAlchemy NullPool in tests

3. **Establish Testing Strategy**
   - Define how to verify async implementations work correctly
   - Set up test fixtures for async testing

### Phase 2: CRUD Operations Migration (2-3 days)

1. **Device CRUD Operations**
   - Implement async versions of device create/read/update/delete operations
   - Ensure both sync and async operations share code where possible
   - Update related services to use async operations when appropriate

2. **Backup CRUD Operations**
   - Implement async versions of backup create/read/update/delete operations
   - Add support for async backup retrieval and storage

3. **User and Authentication CRUD Operations**
   - Implement async versions of user management operations
   - Update authentication flows to support async operations

4. **Settings and Configuration CRUD Operations**
   - Implement async versions of settings operations
   - Ensure configuration loading works in async contexts

### Phase 3: Service Function Implementation (2-3 days)

1. **Credential Management Service**
   - Add async versions of credential retrieval and storage operations
   - Implement proper credential validation in async contexts

2. **Job Execution Service**
   - Update job execution to support async operation
   - Implement async job status tracking
   - Ensure proper error handling in async job execution

3. **Notification Service**
   - Add async notification delivery
   - Implement async event listeners

4. **Auditing Service**
   - Implement async audit logging
   - Ensure audit records are properly stored in async operations

### Phase 4: Test Suite Completion (2-3 days)

1. **Fix SQLAlchemy NullPool Issue**
   - Investigate and fix the dependency issue with SQLAlchemy's NullPool
   - Update test configuration to properly handle async sessions

2. **Complete Async Test Suite**
   - Implement missing tests for async CRUD operations
   - Add tests for async service functions
   - Ensure all async code paths are properly tested

3. **Integration Tests**
   - Add integration tests for async workflows
   - Test async operations end-to-end

### Phase 5: Documentation and Finalization (1-2 days)

1. **Update API Documentation**
   - Document async APIs
   - Add examples of using async operations

2. **Create Developer Guidelines**
   - Document patterns for implementing async code
   - Add guidelines for testing async functionality

3. **Finalize and Merge**
   - Complete code review
   - Fix any identified issues
   - Merge to develop branch

## Technical Details

### Async CRUD Pattern

When implementing async CRUD operations, follow this pattern:

```python
# Synchronous version
def get_device_by_id(db_session, device_id):
    return db_session.query(Device).filter(Device.id == device_id).first()

# Async version
async def get_device_by_id_async(db_session, device_id):
    result = await db_session.execute(
        select(Device).filter(Device.id == device_id)
    )
    return result.scalars().first()

# Combined version with overloading
def get_device_by_id_combined(db_session, device_id):
    if isinstance(db_session, AsyncSession):
        # Return awaitable coroutine
        async def _async_impl():
            result = await db_session.execute(
                select(Device).filter(Device.id == device_id)
            )
            return result.scalars().first()
        return _async_impl()
    else:
        # Synchronous implementation
        return db_session.query(Device).filter(Device.id == device_id).first()
```

### Async Service Pattern

When implementing async service functions, follow this pattern:

```python
class DeviceService:
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.is_async = isinstance(db_session, AsyncSession) if db_session else False
    
    def get_device(self, device_id):
        if self.is_async:
            return self._get_device_async(device_id)
        else:
            return self._get_device_sync(device_id)
    
    def _get_device_sync(self, device_id):
        return self.db_session.query(Device).filter(Device.id == device_id).first()
    
    async def _get_device_async(self, device_id):
        result = await self.db_session.execute(
            select(Device).filter(Device.id == device_id)
        )
        return result.scalars().first()
```

### NullPool Issue Solution

The SQLAlchemy NullPool issue in the tests appears to be related to how the test fixtures create and manage database sessions. A potential solution is:

```python
@pytest.fixture
async def async_db_engine():
    # Use connect_args={"check_same_thread": False} for SQLite
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=NullPool
    )
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def async_db_session(async_db_engine):
    # Create session factory
    async_session = sessionmaker(
        async_db_engine, expire_on_commit=False, class_=AsyncSession
    )
    # Create session
    async with async_session() as session:
        yield session
```

## Progress Log

This section will be updated as implementation progresses.

### 2025-03-27: Initial Setup and CRUD Operations Implementation

1. Created feature branch `feature/phase3.2-async-support-finish`
2. Fixed the NullPool issue in `tests/conftest.py` by changing the import from `sqlalchemy.ext.asyncio` to `sqlalchemy.pool`
3. Analyzed remaining non-async code and documented implementation plan
4. Implemented async versions for device CRUD operations:
   - Updated get_device, get_devices, create_device, update_device, update_device_backup_status, and delete_device
   - Added comprehensive tests for all async device operations
5. Implemented async versions for backup CRUD operations:
   - Updated get_backup, get_backups, create_backup, delete_backup, and get_backup_content
   - Added comprehensive tests for all async backup operations
6. Implemented async versions for user CRUD operations:
   - Updated get_user, get_user_by_email, get_user_by_username, get_users, create_user, update_user, update_user_last_login, and delete_user
   - Added comprehensive tests for all async user operations

### [Future Date]: Remaining CRUD Operations Implementation

*The progress will be documented here as work is completed*

### [Future Date]: Service Function Implementation

*The progress will be documented here as work is completed*

### [Future Date]: Test Suite Completion

*The progress will be documented here as work is completed*

### [Future Date]: Documentation and Finalization

*The progress will be documented here as work is completed*

## Handoff Notes

This section contains information for developers who may need to continue this work:

### Important Files

- `netraven/core/db/session.py` - Contains session management code for both sync and async
- `netraven/core/services/` - Contains service implementations that need async versions
- `tests/conftest.py` - Contains test fixtures that need updating for async tests

### Known Issues

- The SQLAlchemy NullPool issue in tests needs resolution
- Some services may need refactoring to properly support both sync and async patterns
- Certain operations that inherently block (file I/O, external APIs) need careful handling

### Contact Information

If you need to continue this work and have questions, contact:
- [Developer Name]: [email/contact]
- [Developer Name]: [email/contact]

## Conclusion

By following this implementation plan, we'll complete the async support for the NetRaven application. This will improve system performance, especially for I/O-bound operations, and provide a foundation for future enhancements to the system's scalability. 