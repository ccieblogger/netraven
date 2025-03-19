# NetRaven Implementation Plan - Phase 1.4

## Current Status Overview

We've implemented device-specific backup endpoints and fixed critical issues in the backup API. Current implementation includes:

1. `POST /api/devices/{device_id}/backup` - Creates a backup for a specific device
2. `GET /api/devices/{device_id}/backups` - Lists all backups for a specific device
3. Proper error handling in all implemented endpoints
4. Fixed the `get_backups` function to correctly return database results
5. Updated tests with appropriate skip markers for unimplemented features

## Remaining Implementation Items

### 1. Backup API Completion

#### 1.1. Backup Content Storage Implementation
- **Files to modify**: 
  - `netraven/web/routers/backups.py`
  - `netraven/web/crud/backup.py`
- **Implementation details**:
  - Create a proper file storage mechanism for backup content
  - Implement logic to store device configurations in actual files
  - Update the `create_backup` function to handle file creation
  - Ensure backup files are stored in a designated directory with proper permissions

#### 1.2. Backup Content Retrieval Endpoint
- **Files to modify**: `netraven/web/routers/backups.py`
- **Implementation details**:
  - Enhance the `get_backup_content_endpoint` to read actual backup files
  - Add proper error handling for file access issues
  - Implement content sanitization for security

#### 1.3. Backup Deletion Logic
- **Files to modify**: `netraven/web/crud/backup.py`
- **Implementation details**:
  - Update `delete_backup` to also remove the backup file from disk
  - Add error handling for file deletion failures
  - Add logging for successful file deletion

#### 1.4. Backup Comparison Feature
- **Files to modify**: `netraven/web/routers/backups.py`
- **Implementation details**:
  - Enhance the `compare_backups` endpoint to work with actual file content
  - Implement a more robust diff algorithm for comparing device configurations
  - Add line-by-line comparison visualization with highlighted changes

### 2. Fixing Pydantic Deprecation Warnings

#### 2.1. Update ConfigDict Implementation
- **Files to modify**:
  - `netraven/web/schemas/*.py` (all schema files)
  - `netraven/web/routers/*.py` (all router files with model definitions)
- **Implementation details**:
  - Replace class-based `config` with `model_config = ConfigDict(...)`
  - Update models to follow the pattern: `model_config = ConfigDict(from_attributes=True)`

#### 2.2. Replace @validator with @field_validator
- **Files to modify**: `netraven/web/schemas/tag_rule.py` and any other files using validators
- **Implementation details**:
  - Replace all `@validator` decorators with `@field_validator`
  - Update import statements to import `field_validator` from pydantic
  - Adjust validator function signatures according to Pydantic V2 requirements

#### 2.3. Update Schema Parameters
- **Files to modify**: All schema files using deprecated parameters
- **Implementation details**:
  - Replace `min_items` with `min_length`
  - Replace `schema_extra` with `json_schema_extra`
  - Update any other deprecated parameters identified in the warnings

### 3. Testing Strategy

#### 3.1. Integration Test Updates
- **Files to modify**: 
  - `tests/integration/test_api_backups.py`
  - Other test files as needed
- **Implementation details**:
  - Update backup tests to work with actual file storage
  - Remove skip markers once implementation is complete
  - Add assertions to verify file content and metadata
  - Add cleanup logic to remove test files after test completion

#### 3.2. Comprehensive Test Coverage
- **Files to create/modify**:
  - `tests/unit/test_backup_crud.py`
  - `tests/unit/test_backup_router.py`
- **Implementation details**:
  - Create unit tests for all CRUD operations
  - Test edge cases (e.g., file not found, permission issues)
  - Mock database and file system interactions for isolated testing
  - Test error handling and logging

### 4. User Management API Implementation

#### 4.1. User Creation Endpoint
- **Files to modify**: `netraven/web/routers/users.py`
- **Implementation details**:
  - Implement the `POST /api/users` endpoint
  - Add validation for required fields
  - Ensure proper permission checks
  - Add password hashing for security
  - Implement duplicate username/email checks

#### 4.2. User Authentication Improvements
- **Files to modify**:
  - `netraven/web/routers/auth.py`
  - `netraven/web/auth/__init__.py`
- **Implementation details**:
  - Implement token refresh mechanism
  - Add proper token expiration handling
  - Enhance error messages for authentication failures
  - Add rate limiting for login attempts

### 5. Documentation Updates

#### 5.1. API Documentation
- **Files to modify**: `openapi.json` and relevant source files with docstrings
- **Implementation details**:
  - Update endpoint descriptions
  - Document request/response formats
  - Add example requests/responses
  - Document error codes and responses

#### 5.2. Developer Documentation
- **Files to modify**: `docs/*.md` files
- **Implementation details**:
  - Document the backup file storage mechanism
  - Update the API reference with new endpoints
  - Add troubleshooting guide for common issues
  - Update installation and configuration instructions

## Implementation Approach

### Phase 1: Backup API Completion
1. Implement backup file storage mechanism
2. Update content retrieval endpoint
3. Enhance backup deletion logic
4. Implement robust backup comparison
5. Write unit and integration tests for each component
6. Update documentation

### Phase 2: Fix Pydantic Deprecation Warnings
1. Update all schema files to use ConfigDict
2. Replace all validators with field_validators
3. Update parameter names to current Pydantic standards
4. Verify no warnings are generated during tests

### Phase 3: User Management API
1. Implement user creation endpoint
2. Enhance authentication mechanisms
3. Add token refresh functionality
4. Update tests to cover new functionality
5. Document the authentication flow

### Phase 4: Final Testing and Documentation
1. Run comprehensive test suite for all APIs
2. Verify all tests pass or are appropriately skipped
3. Update API documentation with new endpoints
4. Create examples for common API usage patterns
5. Update developer documentation with implementation details

## Testing Strategy

Each phase will follow the testing approach outlined in the DEVELOPER.md file:

1. **Test-Driven Development**: Write failing tests first, then implement the functionality
2. **Unit Tests**: Test individual components in isolation
3. **Integration Tests**: Test component interactions
4. **API Tests**: Test the complete API flow

All tests will be run within the Docker container:
```bash
docker exec netraven-api-1 python -m pytest tests/unit
docker exec netraven-api-1 python -m pytest tests/integration
```

## Future Considerations

1. **Performance Optimization**: The current implementation focuses on correctness. Future phases should improve:
   - Backup file storage efficiency
   - Query optimization for large datasets
   - Pagination for listing endpoints

2. **Security Enhancements**:
   - Implement more robust authentication mechanisms
   - Add audit logging for sensitive operations
   - Enhance permission model for more granular control

3. **User Experience**:
   - Add more detailed error messages
   - Implement progress tracking for long-running operations
   - Add notification system for completed backups 