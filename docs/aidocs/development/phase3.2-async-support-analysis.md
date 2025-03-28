# Phase 3.2: Async Support Implementation Analysis

## Overview

This document outlines the findings from the initial analysis of the async support implementation for NetRaven. It identifies the CRUD operations that need async versions and documents the NullPool dependency issue in the test suite.

## CRUD Operations Requiring Async Support

### 1. Device Operations
- `get_device`: Get a device by ID
- `get_devices`: Get devices with optional filtering and pagination
- `create_device`: Create a new device
- `update_device`: Update an existing device
- `update_device_backup_status`: Update a device's backup status
- `delete_device`: Delete a device

### 2. Backup Operations
- `get_backup`: Get a backup by ID
- `get_backups`: Get backups with optional filtering
- `create_backup`: Create a new backup
- `delete_backup`: Delete a backup
- `get_backup_content`: Get the content of a backup

### 3. User Operations
- `get_user`: Get a user by ID
- `get_user_by_email`: Get a user by email
- `get_user_by_username`: Get a user by username
- `get_users`: Get all users with pagination
- `create_user`: Create a new user
- `update_user`: Update an existing user
- `update_user_last_login`: Update a user's last login timestamp
- `delete_user`: Delete a user

### 4. Admin Settings Operations
- `get_admin_setting`: Get an admin setting by ID
- `get_admin_setting_by_key`: Get an admin setting by key
- `get_admin_settings`: Get all admin settings with optional filtering
- `get_admin_settings_by_category`: Get admin settings grouped by category
- `create_admin_setting`: Create a new admin setting
- `update_admin_setting`: Update an admin setting
- `update_admin_setting_value`: Update an admin setting's value
- `delete_admin_setting`: Delete an admin setting
- `initialize_default_settings`: Initialize default admin settings

### 5. Job Log Operations
- `get_job_logs`: Get job logs with optional filtering
- `get_job_log`: Get a job log by ID
- `get_job_log_entries`: Get job log entries for a job
- `get_job_log_with_entries`: Get a job log with its entries
- `get_job_log_with_details`: Get a job log with details
- `delete_job_log`: Delete a job log
- `delete_old_job_logs`: Delete job logs older than a specified number of days
- `delete_job_logs_by_retention_policy`: Delete job logs according to retention policy

### 6. Scheduled Job Operations
- `get_scheduled_jobs`: Get scheduled jobs with optional filtering
- `get_scheduled_job`: Get a scheduled job by ID
- `get_scheduled_job_with_details`: Get a scheduled job with details
- `calculate_next_run`: Calculate the next run time for a scheduled job
- `create_scheduled_job`: Create a new scheduled job
- `update_scheduled_job`: Update a scheduled job
- `delete_scheduled_job`: Delete a scheduled job
- `toggle_scheduled_job`: Enable or disable a scheduled job
- `update_job_last_run`: Update the last run timestamp for a job
- `get_due_jobs`: Get jobs that are due for execution

## SQLAlchemy NullPool Issue

The issue with NullPool in the test suite is:

1. **Import Problem**: NullPool is currently imported from `sqlalchemy.ext.asyncio` in tests/conftest.py (line 22), but it should be imported from `sqlalchemy.pool`.

2. **Affected Files**:
   - tests/conftest.py
   - tests/utils/db_init.py

3. **Proposed Fix**:
   - Update the import in tests/conftest.py from `from sqlalchemy.ext.asyncio import NullPool` to `from sqlalchemy.pool import NullPool`
   - Update any other files that may have the incorrect import

## Implementation Strategy

Based on this analysis, the implementation will proceed in the following order:

1. **Fix NullPool Issue**:
   - Update the imports in affected files
   - Verify the fix with a basic test

2. **Implement Async CRUD Operations**:
   - Follow the pattern in tag.py for async support
   - Implement device operations first as they're most critical
   - Implement other operations in order of dependency

3. **Test Async Operations**:
   - Create test cases for each set of async operations
   - Ensure all async operations work with both sync and async sessions

4. **Documentation**:
   - Document async usage patterns
   - Add examples for developers

## Progress Tracking

This section will be updated as implementation progresses:

- ✅ Initial analysis completed
- ❌ NullPool issue fixed
- ❌ Device operations implemented
- ❌ Backup operations implemented
- ❌ User operations implemented
- ❌ Admin settings operations implemented
- ❌ Job log operations implemented
- ❌ Scheduled job operations implemented 