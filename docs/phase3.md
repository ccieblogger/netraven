# NetRaven Phase 3: Database Logging Integration

This document outlines the changes made in Phase 3 of the NetRaven project, which focuses on transitioning from file-based logging to database logging.

## Overview

Phase 3 introduces database logging for job execution, device interactions, and backup operations. This enhances the system's ability to track, query, and analyze job execution history and results.

## Key Components

### 1. Database Logger

A new `DatabaseLogHandler` class has been implemented in `netraven/core/db_logging.py`. This handler:

- Writes log entries to both files and the database
- Manages job sessions (start, end, status)
- Provides methods for logging device interactions
- Includes error handling for database connectivity issues

### 2. Device Logging Integration

The device logging module (`netraven/jobs/device_logging.py`) has been updated to:

- Use the database logger for all device interactions
- Track device connection attempts, successes, and failures
- Log command execution and responses
- Record backup operations with detailed metadata

### 3. Device Connector Updates

The `JobDeviceConnector` class has been enhanced to:

- Integrate with the database logger
- Track connection state more reliably
- Include user ID for database logging
- Provide more detailed error information

### 4. Backup Job Scheduler

A new scheduler module (`netraven/jobs/scheduler.py`) has been added to:

- Schedule backup jobs with various recurrence patterns (daily, weekly, interval)
- Manage scheduled jobs (add, list, remove)
- Execute backup jobs with database logging
- Run as a background service

### 5. CLI Integration

The CLI has been updated to:

- Support scheduling backup jobs
- List scheduled jobs
- Remove scheduled jobs
- Include user ID for database logging

### 6. Migration Tools

A migration script (`scripts/migrate_logs.py`) has been created to:

- Migrate existing file-based logs to the database
- Organize log entries by session
- Preserve device and job context

## Usage

### Database Logging

Database logging is enabled by default. No additional configuration is required.

### Scheduling Backup Jobs

To schedule a backup job:

```bash
netraven schedule add <device> --schedule-type daily --time 02:00
```

To list scheduled jobs:

```bash
netraven schedule list
```

To remove a scheduled job:

```bash
netraven schedule remove <job_id>
```

### Migrating Existing Logs

To migrate existing logs to the database:

```bash
scripts/migrate_logs.py --log-dir /path/to/logs
```

## Testing

A test script (`scripts/test_scheduler.py`) is provided to verify the scheduler functionality:

```bash
scripts/test_scheduler.py --device <device> --interval 5 --duration 30
```

## Dependencies

The following dependencies have been added:

- `schedule>=1.1.0`: For job scheduling
- `sqlalchemy>=1.4.0`: For database operations
- `pyyaml>=6.0`: For configuration handling

Install them using:

```bash
pip install -r requirements-scheduler.txt
``` 