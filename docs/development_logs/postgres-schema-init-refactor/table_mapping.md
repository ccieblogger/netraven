# Database Tables and Relationships Mapping

This document provides a comprehensive mapping of all database tables in the NetRaven system, their relationships, and how they will be affected by the Base class consolidation.

## Current Database Tables

### Main Base Class Tables (netraven.web.database.Base)

| Table Name | Model File | Primary Key | Important Columns | Relationships |
|------------|------------|-------------|-------------------|---------------|
| users | user.py | id (String) | username, email, password_hash | scheduled_jobs, job_logs, devices |
| devices | device.py | id (String) | hostname, ip_address, device_type | owner, scheduled_jobs, job_logs, tags (via device_tags) |
| backups | backup.py | id (String) | device_id, filename, version | device |
| tags | tag.py | id (String) | name, color, description | devices (via device_tags), rules |
| tag_rules | tag.py | id (String) | tag_id, rule_type, rule_value | tag |
| device_tags | tag.py | id (String) | device_id, tag_id | device, tag |
| job_logs | job_log.py | id (String) | session_id, job_type, status | device, user, log_entries |
| job_log_entries | job_log.py | id (String) | job_log_id, level, message | job_log |
| scheduled_jobs | scheduled_job.py | id (String) | name, device_id, schedule_type | device, user |
| admin_settings | admin_settings.py | id (UUID) | key, value, category | None |
| audit_logs | audit_log.py | id (UUID) | event_type, event_name, actor_id | None |

### Secondary Base Class Tables (netraven.core.credential_store.Base)

| Table Name | Model File | Primary Key | Important Columns | Relationships |
|------------|------------|-------------|-------------------|---------------|
| credentials | credential_store.py | id (String) | name, username, password | credential_tags |
| credential_tags | credential_store.py | id (String) | credential_id, tag_id, priority | credential |

## Relationships Between Tables

### One-to-Many Relationships
- User → Devices (one user has many devices)
- User → ScheduledJobs (one user has many scheduled jobs)
- User → JobLogs (one user creates many job logs)
- Device → Backups (one device has many backups)
- Device → ScheduledJobs (one device has many scheduled jobs)
- Device → JobLogs (one device has many job logs)
- Tag → TagRules (one tag has many rules)
- JobLog → JobLogEntries (one job log has many entries)

### Many-to-Many Relationships
- Devices ↔ Tags (through device_tags junction table)
- Credentials ↔ Tags (through credential_tags junction table)

## Foreign Key References

### device_tags Table
- device_id → devices.id
- tag_id → tags.id

### credential_tags Table
- credential_id → credentials.id
- tag_id → No direct foreign key constraint (references tags.id in code)

### job_logs Table
- device_id → devices.id
- created_by → users.id

### scheduled_jobs Table
- device_id → devices.id
- created_by → users.id

## Consolidation Impact Analysis

### Tables Affected by Base Consolidation
1. **credentials**: Will need to be recreated using the main Base class
2. **credential_tags**: Will need to be recreated using the main Base class

### Relationship Changes Required
1. **tag_id in credential_tags**: Should be properly linked to the tags table with a foreign key
2. **credential_tags relationship**: Will need to be updated to work with the new Base class

### Data Migration Considerations
- No data migration needed for a new product before release
- Ensure initialization scripts correctly set up all tables with the consolidated Base class

## Schema Initialization Changes

### Current Process
- Basic PostgreSQL initialization via SQL script
- Table creation via SQLAlchemy at runtime
- Two separate Base classes with separate metadata

### New Process
- Basic PostgreSQL initialization via SQL script (unchanged)
- Consolidated Base class with unified metadata
- Single initialization script that creates all tables properly
- No runtime schema modifications

## Next Steps
1. Create a unified model schema with a single Base class
2. Update credential_store models to use the main Base
3. Create a new initialization script that properly creates all tables
4. Update container startup process 