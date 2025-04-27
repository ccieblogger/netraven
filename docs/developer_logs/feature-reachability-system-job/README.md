# Development Log: Reachability System Job

## Summary
This log documents the implementation of the system reachability job in NetRaven, which is automatically created at system initialization and associated with the default tag and credentials. This job is protected from deletion and is intended to provide baseline device reachability monitoring for all devices.

## Changes Made

### 1. Schema and Model
- Added `is_system_job` Boolean field to the `Job` model (`netraven/db/models/job.py`).
- Updated the initial Alembic schema (`alembic/versions/a3992da91329_initial_schema_definition.py`) to include the `is_system_job` column in the `jobs` table.

### 2. Initialization Script
- Updated `netraven/db/init_data.py` to create a `system-reachability` job if it does not exist, associating it with the default tag and marking it as a system job.
- The job is created with:
  - `name`: `system-reachability`
  - `description`: System job: checks device reachability via ICMP and TCP.
  - `job_type`: `reachability`
  - `is_enabled`: `True`
  - `is_system_job`: `True`
  - Associated with the default tag

### 3. Rationale
- Ensures every deployment has a baseline reachability job for all devices.
- System jobs are protected from accidental deletion or modification.
- Supports future extensibility for other system jobs.

## Deployment Notes
- This is a pre-release, containerized product. The schema change is made directly in the initial migration.
- After updating, drop all tables and re-run the Postgres container to apply the new schema.

## Next Steps
- Update API/UI to prevent deletion or editing of system jobs if not already enforced.
- Test system initialization to confirm the reachability job is created and associated as expected. 