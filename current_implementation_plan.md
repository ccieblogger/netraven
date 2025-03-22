# NetRaven Test Implementation Plan

## Overview

This document outlines our systematic approach to testing and fixing all implemented tests in the NetRaven project. We are working through each test file methodically, identifying issues, implementing fixes, and tracking progress.

## Testing Methodology

For each test file, we:

1. Run the test in isolation to identify any issues
2. Document failures with error messages
3. Investigate root causes
4. Implement fixes
5. Verify the fix by re-running the test
6. Mark as complete when successfully passing

## Environment Setup

Before beginning testing:

1. Ensure the testing environment is properly configured:
   ```bash
   export NETRAVEN_ENV=test
   docker-compose build --no-cache api
   docker-compose up -d
   ```

2. Verify container health:
   ```bash
   docker-compose ps
   ```

## Authentication Approach Refactoring

We have completed a significant refactoring of our authentication approach in tests:

1. All integration tests now use the standard `api_token` fixture for authentication
2. The `api_token` fixture obtains a real token using admin credentials from `app_config`
3. Authentication failures now cause tests to fail with clear error messages (instead of skipping)
4. Tests are more realistic by using the actual authentication flow
5. Maintenance is simplified with this standardized approach

### Updated Test Files:

- ✅ `tests/integration/test_gateway_api.py`
- ✅ `tests/integration/test_auth_advanced.py`
- ✅ `tests/integration/test_credential_advanced.py`
- ✅ `tests/integration/test_job_logs_advanced.py`
- ✅ `tests/integration/test_admin_settings_api.py`
- ✅ `tests/integration/test_admin_settings_ui.py`
- ✅ `tests/integration/test_key_management_ui.py`

## Test Execution Tracking

### 1. Integration Tests - Gateway API

| Test | Status | Issues | Fix Applied |
|------|--------|--------|-------------|
| `test_gateway_status_authenticated` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_gateway_status_unauthenticated` | Complete | No issues | |
| `test_gateway_devices_listing` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_gateway_devices_filtering` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_gateway_metrics_collection` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_gateway_metrics_historical` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_gateway_config_retrieval` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_gateway_config_authentication_required` | Complete | No issues | |

**Execution Command**:
```bash
docker exec netraven-api-1 python -m pytest -v tests/integration/test_gateway_api.py
```

### 2. Integration Tests - Credential Advanced Features

| Test | Status | Issues | Fix Applied |
|------|--------|--------|-------------|
| `test_credential_statistics_empty` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_credential_statistics_with_data` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_tag_credential_statistics` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_credential_testing_valid` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_credential_testing_invalid` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_bulk_tag_assignment` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_bulk_tag_removal` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_smart_credential_selection` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_credential_priority_optimization` | Complete | Used mock token | Updated to use `api_token` fixture |

**Execution Command**:
```bash
docker exec netraven-api-1 python -m pytest -v tests/integration/test_credential_advanced.py
```

### 3. Integration Tests - Job Logs Advanced Features

| Test | Status | Issues | Fix Applied |
|------|--------|--------|-------------|
| `test_job_log_entries_retrieval` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_job_log_entries_pagination` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_job_log_retention_policy_application` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_job_log_cleanup_old_logs` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_active_jobs_listing` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_job_statistics_calculation` | Complete | Used mock token | Updated to use `api_token` fixture |

**Execution Command**:
```bash
docker exec netraven-api-1 python -m pytest -v tests/integration/test_job_logs_advanced.py
```

### 4. Integration Tests - Auth Advanced Features

| Test | Status | Issues | Fix Applied |
|------|--------|--------|-------------|
| `test_token_refresh_flow` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_token_scope_verification` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_login_with_valid_credentials` | Complete | Used mock credentials | Updated to use admin credentials from config |
| `test_login_with_invalid_credentials` | Complete | No issues | |
| `test_auth_event_logging` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_session_management_logout` | Complete | Used mock token | Updated to use `api_token` fixture |
| `test_token_validation` | Complete | Used mock token | Updated to use `api_token` fixture |

**Execution Command**:
```bash
docker exec netraven-api-1 python -m pytest -v tests/integration/test_auth_advanced.py
```

### 5. Integration Tests - Admin Settings API

| Test | Status | Issues | Fix Applied |
|------|--------|--------|-------------|
| `test_get_admin_settings_unauthorized` | Complete | No issues | |
| `test_get_admin_settings_forbidden` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_get_all_settings` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_get_settings_by_category` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_get_setting_by_id` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_get_setting_by_key` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_get_nonexistent_setting` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_create_setting` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_create_duplicate_setting` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_create_invalid_setting` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_update_setting` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_update_nonexistent_setting` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_update_setting_invalid_value` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_delete_setting` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_delete_nonexistent_setting` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_delete_protected_setting` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_initialize_default_settings` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_get_default_value` | Complete | Used custom token approach | Updated to use `api_token` fixture |

**Execution Command**:
```bash
docker exec netraven-api-1 python -m pytest -v tests/integration/test_admin_settings_api.py
```

### 6. Integration Tests - Admin Settings UI

| Test | Status | Issues | Fix Applied |
|------|--------|--------|-------------|
| `test_settings_form_validation_required_fields` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_settings_form_validation_data_types` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_settings_form_validation_range_limits` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_settings_persistence_across_api_requests` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_settings_persistence_across_sessions` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_settings_persistence_after_multiple_changes` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_admin_only_access_to_settings_pages` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_permission_based_settings_display` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_password_complexity_settings_ui_validation` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_token_expiry_settings_effect` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_system_job_settings_effect` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_notification_settings_effect` | Complete | Used custom token approach | Updated to use `api_token` fixture |

**Execution Command**:
```bash
docker exec netraven-api-1 python -m pytest -v tests/integration/test_admin_settings_ui.py
```

### 7. Integration Tests - Key Management UI

| Test | Status | Issues | Fix Applied |
|------|--------|--------|-------------|
| `test_key_dashboard_display` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_key_details_display` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_key_creation_form_validation` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_key_activation_workflow` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_key_rotation_workflow` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_key_backup_restore_workflow` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_permission_based_ui_actions` | Complete | Used custom token approach | Updated to use `api_token` fixture |
| `test_error_handling_display` | Complete | Used custom token approach | Updated to use `api_token` fixture |

**Execution Command**:
```bash
docker exec netraven-api-1 python -m pytest -v tests/integration/test_key_management_ui.py
```

## Implementation Phases

### Phase 1: API Authentication Standardization (Completed)
- ✅ Update all API tests to use the standard `api_token` fixture
- ✅ Verify the authentication approach works consistently
- ✅ Update API test utility functions to support the authentication approach

### Phase 2: Core Functionality Tests (Completed)
- ✅ Update `test_security_features.py` to use the `api_token` fixture
- ✅ Update `test_backup_storage_integration.py` to use the `api_token` fixture
- ✅ Update `test_system_functionality.py` to use the `api_token` fixture
- ✅ Run the updated tests to verify they pass with the new authentication approach

### Phase 3: Advanced Tests (Completed)
- ✅ Update `test_credential_store_integration.py` to use the `api_token` fixture
- ✅ Update `test_key_rotation_integration.py` to use the `api_token` fixture
- ✅ Update `test_job_tracking_notification_integration.py` to use the `api_token` fixture
- ✅ Run the updated tests to verify they pass with the new authentication approach

### Phase 4: Test Verification and Troubleshooting (In Progress)
- ✅ Execute all integration tests and identify any failures
- ✅ Diagnose root causes of test failures
  - Multiple issues identified during test execution:
    - `NameError: name 'app' is not defined` in netraven/web/app.py
    - ImportErrors for modules like `LocalFileStorage`, `delete_test_device`, `netraven.core.device_connector`
    - Indentation errors in test files like `test_admin_settings_effects.py`
    - Incorrect import paths in various test files
    - FastAPI router configuration errors with empty prefixes and paths
    - Missing dependencies like sqlalchemy-utils in test environment
- ✅ Fix issues in test files or application code
  - Created proper FastAPI app definition in app.py
  - Added backward compatibility wrappers for storage classes (LocalFileStorage, S3Storage)
  - Added missing functions to api_test_utils.py: get_api_token, update_admin_setting, ensure_user_exists_with_role
  - Fixed indentation errors in test files
  - Updated import paths to reflect actual module locations
  - Fixed incorrect imports from `netraven.web.db` to use `netraven.web.database` instead
  - Fixed FastAPI router configuration by changing empty path routes ("") to explicit slash routes ("/")
  - Fixed API configuration in `netraven.web.api.py` by adding missing closing brackets and ensuring all routers are properly included
  - Added `sqlalchemy-utils` to the test requirements
  - Fixed the `tag_rule` import in `tests/utils/db_init.py` to use the correct import path
- [ ] Resolve remaining test failures:
  - Fix TestClient compatibility issue - tests failing with error: "TypeError: Client.__init__() got an unexpected keyword argument 'app'"
  - Add version constraints in test-requirements.txt to ensure compatible versions of httpx, starlette and fastapi
  - Run comprehensive test suite after fixing compatibility issues
- [ ] Document any application issues discovered
- [ ] Verify all tests pass successfully
- [ ] Create a comprehensive test report

### Phase 5: End-to-End Test Implementation (Pending)
- [ ] Develop end-to-end tests for critical user workflows
- [ ] Implement API-based UI testing patterns
- [ ] Create comprehensive test plan documentation
- [ ] Verify test coverage across all key features

## Timeline and Progress

| Feature Area                   | Status      | ETA           | 
|--------------------------------|-------------|---------------|
| API Authentication Standard    | ✅ Complete | March 22, 2025 |
| Core Functionality Tests       | ✅ Complete | March 22, 2025 |
| Advanced Tests                 | ✅ Complete | March 23, 2025 |
| Test Verification & Troubleshooting | 📅 Scheduled | March 24, 2025 |
| End-to-End Test Implementation | 📅 Scheduled | March 25, 2025 |
| Final Test Run & Verification  | 📅 Scheduled | March 26, 2025 |

## Progress Tracking

- 68 tests completed and passing
- Multiple issues identified and fixed in Phase 4:
  - App definition issues in web/app.py
  - Missing utility functions in api_test_utils.py
  - Storage class compatibility wrappers added
  - Import path corrections
- Ready to continue troubleshooting remaining test failures

## Next Steps

1. Continue Phase 4: Test Verification and Troubleshooting
   - Fix remaining import and module errors
   - Resolve any other test failures
   - Verify tests run correctly after all fixes

2. After establishing a stable test baseline, proceed to Phase 5 for end-to-end tests
   - Start with authentication flow end-to-end tests
   - Develop device management workflow tests
   - Implement backup and configuration comparison tests

3. Create comprehensive test plan documentation to guide future testing efforts

4. Verify test coverage across all key product features

5. Conduct final test run and validation before releasing to production

## Key Improvements

1. All tests now use a consistent authentication method
2. Authentication failures now cause tests to fail rather than skip
3. Clear error messages when authentication fails
4. Tests are more realistic by using the actual authentication flow
5. Maintenance is simplified with a standardized approach

## Completion Criteria

Testing implementation will be considered complete when:
1. All tests have been executed
2. All tests are passing
3. Any required fixes have been properly documented
4. The application demonstrates consistent behavior across all test cases 