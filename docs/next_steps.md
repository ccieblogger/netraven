# Standardization Plan for Remaining NetRaven API Routers

This plan outlines the steps to implement standardized permission checks, error handling, and logging for the remaining API routers.

## 1. Job Logs Router Standardization

**Target File:** `netraven/web/routers/job_logs.py`

### Steps:
1. **Review current implementation:**
   - Examine all endpoints in the job_logs router
   - Identify permission checks, error handling, and logging patterns

2. **Update each endpoint:**
   - `list_job_logs` - Add standardized permission checks using `has_scope("read:job_logs")`, try-except blocks, and logging
   - `get_job_log_details` - Add permission checks for specific job log access
   - `create_job_log` - Update with proper permission validation and error handling
   - Any additional endpoints found during review

3. **Implement consistent patterns:**
   - Use `try-except` blocks for all database operations
   - Add standardized logging: `Access granted: user={current_user.username}, resource=job_logs, scope=read:job_logs`
   - Implement detailed error messages with proper status codes

4. **Testing:**
   - Restart API container after changes
   - Test listing job logs with admin credentials
   - Verify logging output in container logs

## 2. Device Router Standardization

**Target File:** `netraven/web/routers/devices.py`

### Steps:
1. **Review current implementation:**
   - Identify all device endpoints
   - Check for existing permission handling and logging

2. **Update core endpoints:**
   - `list_devices` - Add standardized permission checks for the `read:devices` scope
   - `get_device_details` - Update permission checks for specific device access
   - `create_device` - Implement standardized checks for `write:devices` scope
   - `update_device` - Add permission validation for specific device updates
   - `delete_device` - Ensure proper permission checks before deletion
   - `backup_device_config` - Update with standardized checks and logging

3. **Implement device-specific permission functions if needed:**
   - Create a standardized `check_device_access` function if not already present
   - Ensure it checks for ownership or admin status

4. **Add standardized logging and error handling:**
   - Log all device access attempts with username, resource ID, and scope
   - Implement consistent error handling across all endpoints
   - Add detailed error messages with proper HTTP status codes

5. **Testing:**
   - Test listing devices with admin credentials
   - Test creating, updating, and deleting devices
   - Verify permissions checks with different user types
   - Check logs for standardized access entries

## 3. User Router Standardization

**Target File:** `netraven/web/routers/users.py`

### Steps:
1. **Review current implementation:**
   - Identify all user-related endpoints
   - Check current permission handling patterns

2. **Update user endpoints:**
   - `list_users` - Add standardized permission checks for `read:users` scope
   - `get_user_details` - Add specific user access checks
   - `get_current_user` - Ensure proper error handling
   - `create_user` - Ensure admin-only access with proper scope checks
   - `update_user` - Add standardized permission validation
   - `delete_user` - Implement proper permission checks

3. **Implement specialized access control:**
   - Add checks for admin status for admin-only operations
   - Implement self-user checks (users can view/edit their own profiles)

4. **Add standardized logging and error handling:**
   - Add access granted/denied logs for all user operations
   - Implement consistent error handling with try-except blocks
   - Add appropriate HTTP exceptions with descriptive messages

5. **Testing:**
   - Test user listing and detail retrieval
   - Test user creation, update, and deletion with admin credentials
   - Test self-user access patterns
   - Verify logs for standardized access messages

## 4. Auth Router Standardization

**Target File:** `netraven/web/routers/auth.py`

### Steps:
1. **Review current implementation:**
   - Examine all authentication endpoints
   - Check existing security patterns

2. **Update auth endpoints:**
   - `login_for_access_token` - Add standardized error handling and logging
   - `create_service_access_token` - Update admin permission checks
   - `list_tokens` - Add standardized permission validation
   - `revoke_token` - Ensure proper permission checks and logging

3. **Add security-focused logging:**
   - Log all authentication attempts (success and failure)
   - Add detailed logging for token operations
   - Implement audit trail for sensitive operations

4. **Enhance error handling:**
   - Add clear error messages for authentication failures
   - Implement appropriate rate limiting messages
   - Add structured logging for security events

5. **Testing:**
   - Test login with valid and invalid credentials
   - Test token creation and revocation
   - Verify logs contain standardized authentication events
   - Check error handling for various failure scenarios

## 5. Gateway Router Standardization

**Target File:** `netraven/web/routers/gateway.py`

### Steps:
1. **Review current implementation:**
   - Identify all gateway-related endpoints
   - Check existing permission patterns

2. **Update gateway endpoints:**
   - `get_gateway_status` - Add standardized permission checks
   - `backup_device_config` - Update with proper permission validation
   - Any additional endpoints found during review

3. **Implement gateway-specific patterns:**
   - Add service token handling if needed
   - Ensure proper permission scopes for gateway operations

4. **Add standardized logging and error handling:**
   - Log all gateway access attempts
   - Implement consistent error handling for gateway operations
   - Add detailed error messages for various failure scenarios

5. **Testing:**
   - Test gateway status endpoint
   - Test device backup operation through the gateway
   - Verify logs for standardized access messages
   - Check error handling for gateway connection issues

## Implementation Strategy

For each router:
1. Examine the current router implementation thoroughly
2. Start with the most critical endpoints first
3. Implement changes one endpoint at a time
4. Restart the API after each router is updated
5. Test all updated endpoints
6. Verify logs for proper standardized patterns

## Common Patterns to Implement

For all routers, ensure consistent implementation of:

1. **Permission checks:**
```python
if not current_user.has_scope("required:scope") and not current_user.is_admin:
    logger.warning(f"Access denied: user={current_user.username}, resource=resource_name, scope=required:scope, reason=insufficient_permissions")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions: required:scope required"
    )
```

2. **Error handling:**
```python
try:
    # Operation code
    logger.info(f"Access granted: user={current_user.username}, resource=resource_name, scope=required:scope")
    return result
except HTTPException:
    # Re-raise HTTP exceptions
    raise
except Exception as e:
    logger.exception(f"Error performing operation: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error performing operation: {str(e)}"
    )
```

3. **Resource-specific access checks:**
```python
resource = check_resource_access(
    principal=current_user,
    resource_id_or_obj=resource_id,
    required_scope="required:scope",
    db=db
)
``` 