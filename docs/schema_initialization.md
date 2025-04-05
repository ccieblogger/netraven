# Database Schema Initialization

This document describes the database schema initialization process for NetRaven.

## Overview

NetRaven uses a PostgreSQL database with a schema defined through SQLAlchemy models. The schema initialization follows a hybrid approach:

1. Basic database setup (extensions, schema) via SQL scripts
2. Table creation and relationships via SQLAlchemy models
3. Initial data population via Python code

## Initialization Process

The database initialization happens in the following sequence:

1. The PostgreSQL container starts and runs `scripts/init-db.sql` to:
   - Create necessary extensions (uuid-ossp, pgcrypto)
   - Create the netraven schema
   - Set the search path

2. The API container starts and runs `scripts/initialize_schema.py` to:
   - Create all tables based on SQLAlchemy models
   - Verify all required tables exist
   - Initialize default data (e.g., default tags)

## Schema Structure

All database models use a single SQLAlchemy Base class from `netraven.web.database`. The key tables include:

| Table Name | Description | Key Relationships |
|------------|-------------|-------------------|
| users | User accounts | devices, scheduled_jobs, job_logs |
| devices | Network devices | backups, scheduled_jobs, job_logs, tags |
| tags | Organizational tags | devices, credentials |
| credentials | Device credentials | tags |
| backups | Configuration backups | devices |
| job_logs | Job execution logs | devices, users |
| scheduled_jobs | Backup jobs | devices, users |

## Adding New Models

To add a new model to the schema:

1. Create a new model file in `netraven/web/models/` using the Base class from `netraven.web.database`
2. Update `netraven/web/models/__init__.py` to import and expose the model
3. No changes to initialization scripts are needed - tables will be created automatically

## Backup Process

Database backups can be created using the included backup script:

1. The PostgreSQL container has a `/backups` volume mounted
2. Run the backup script: `docker exec netraven-postgres /app/scripts/backup_db.sh`
3. Backups are stored as compressed SQL files with timestamps

## Troubleshooting

If the schema initialization fails, check:

1. Database connectivity (PostgreSQL container is running and healthy)
2. Logs from the `initialize_schema.py` script
3. SQLAlchemy model integrity (no conflicting definitions)
4. Permissions for the database user 