# NetRaven Logging Audit (Issue #64)

This document catalogs all log calls in the NetRaven codebase as of the start of enhancement #64. Use this to review and annotate which log categories or specific calls should go to which destinations (file, DB, Redis, stdout, etc.).

---

## How to Use
- Review each log call entry below.
- For each, specify the desired destinations (e.g., file, db, redis, stdout).
- Add any notes or exceptions as needed.

---

| # | File & Line | Log Type | Category | Log Level | Message Content | Metadata | Current Destinations | Desired Destinations | Notes |
|---|-------------|----------|----------|-----------|-----------------|----------|----------------------|----------------------|-------|
| 1 | worker/dispatcher.py:39 | Dispatcher | system_log | getLogger | log = logging.getLogger(__name__) | — | stdout (default) | stdout | |
| 2 | worker/dispatcher.py:111 | Dispatcher | job_log | info | "Job '{job_name}' started: dispatching tasks to devices" | job_id | stdout | stdout, db | |
| 3 | worker/dispatcher.py:115 | Dispatcher | job_log | warning | "No devices to process for job '{job_name}'" | job_id | stdout | stdout, db | |
| 4 | worker/dispatcher.py:118 | Dispatcher | job_log | info | "Job '{job_name}' will process {device_count} devices" | job_id | stdout | stdout, db | |
| 5 | worker/dispatcher.py:133 | Dispatcher | job_log | info | "Submitting task for device '{device_name}' in job '{job_name}'" | job_id, device_id | stdout | stdout, db | |
| 6 | worker/dispatcher.py:169 | Dispatcher | job_log | info | "Task completed for device '{device_name}' in job '{job_name}'" | job_id, device_id | stdout | stdout, db | |
| 7 | worker/dispatcher.py:173 | Dispatcher | job_log | error | "Thread error processing device '{device_name}' in job '{job_name}': {error}" | job_id, device_id | stdout | stdout, db | |
| 8 | worker/dispatcher.py:202 | Dispatcher | job_log | info | "All device tasks completed for job '{job_name}'. Success rate: ..." | job_id | stdout | stdout, db | |
| 9 | worker/dispatcher.py:381 | Dispatcher | job_log | warning | "Non-retriable error for device '{device_name}' in job '{job_name}': ..." | job_id, device_id | stdout | stdout, db | |
| 10 | worker/log_utils.py:17 | Worker | system_log | getLogger | log = logging.getLogger(__name__) | — | stdout (default) | | |
| 11 | worker/log_utils.py:58 | Worker | connection_log | error | "Error committing connection log for device '{device_name}' in job '{job_name}': {commit_error}" | job_id, device_id | stdout | stdout, db | Life cycle event: commit error |
| 12 | worker/log_utils.py:62 | Worker | connection_log | error | "Error saving connection log for device '{device_name}' in job '{job_name}': {error}" | job_id, device_id | stdout | stdout, db | Life cycle event: save error |
| 13 | worker/log_utils.py:98 | Worker | job_log | info | "Job log called for device '{device_name}' in job '{job_name}'" | job_id, device_id | stdout | stdout, db | |
| 14 | worker/log_utils.py:124 | Worker | job_log | info | "Committed new job log entry for device '{device_name}' in job '{job_name}'" | job_id, device_id | stdout | stdout, db | |
| 15 | worker/log_utils.py:126 | Worker | job_log | error | "Error committing job log for device '{device_name}' in job '{job_name}': {commit_error}" | job_id, device_id | stdout | stdout, db | |
| 16 | worker/log_utils.py:129 | Worker | job_log | info | "Added job log entry to session for device '{device_name}' in job '{job_name}' (not committed)" | job_id, device_id | stdout | stdout, db | |
| 17 | worker/log_utils.py:131 | Worker | job_log | error | "Error saving job log for device '{device_name}' in job '{job_name}': {error}" | job_id, device_id | stdout | stdout, db | |
| 18 | worker/log_utils.py:139 | Worker | job_log | info | "Closed managed session for job log entry for device '{device_name}' in job '{job_name}'" | job_id, device_id | stdout | stdout, db | |
| 19 | api/routers/auth_router.py:20 | Auth | system_log | getLogger | logger = logging.getLogger(__name__) | — | stdout (default) | stdout | |
| 20 | api/routers/auth_router.py:41 | Auth | system_log | warning | logger.warning(f"Authentication failed: User not found: {username}") | username | stdout | stdout | |
| 21 | api/routers/auth_router.py:46 | Auth | system_log | info | logger.info(f"Attempting password verification for user: {username}") | username | stdout | stdout | |
| 22 | api/routers/auth_router.py:47 | Auth | system_log | debug | logger.debug(f"Password provided length: {len(password)}") | username | stdout | stdout | |
| 23 | api/routers/auth_router.py:48 | Auth | system_log | debug | logger.debug(f"Stored hash: {user.hashed_password[:10]}...") | username | stdout | stdout | |
| 24 | api/routers/auth_router.py:51 | Auth | system_log | warning | logger.warning(f"Authentication failed: Invalid password for user: {username}") | username | stdout | stdout | |
| 25 | api/routers/auth_router.py:54 | Auth | system_log | info | logger.info(f"Authentication successful for user: {username}") | username | stdout | stdout | |
| 26 | api/routers/auth_router.py:70 | Auth | system_log | info | logger.info(f"Login attempt for user: {form_data.username}") | username | stdout | stdout | |
| 27 | api/routers/auth_router.py:82 | Auth | system_log | warning | logger.warning(f"Login attempt for inactive user: {form_data.username}") | username | stdout | stdout | |
| 28 | api/routers/auth_router.py:97 | Auth | system_log | info | logger.info(f"Token generated successfully for user: {form_data.username}") | username | stdout | stdout | |
| 29 | config/loader.py:6 | Config | system_log | getLogger | log = structlog.get_logger() | — | stdout (default) | stdout | |
| 30 | config/loader.py:67 | Config | system_log | debug | log.debug(f"Environment not specified, using NETRAVEN_ENV or default: {env}") | — | stdout | stdout | |
| 31 | config/loader.py:83 | Config | system_log | debug | log.debug(f"Loaded base configuration from {base_config_path}") | — | stdout | stdout | |
| 32 | config/loader.py:85 | Config | system_log | error | log.error(f"Failed to load base config {base_config_path}", error=str(e)) | — | stdout | stdout | |
| 33 | config/loader.py:94 | Config | system_log | debug | log.debug(f"Loaded environment configuration from {env_config_path}") | — | stdout | stdout | |
| 34 | config/loader.py:96 | Config | system_log | error | log.error(f"Failed to load environment config {env_config_path}", error=str(e)) | — | stdout | stdout | |
| 35 | config/loader.py:98 | Config | system_log | warning | log.warning(f"Environment config file not found: {env_config_path}") | — | stdout | stdout | |
| 36 | config/loader.py:104 | Config | system_log | debug | log.debug("Applied environment variable overrides", overrides=env_overrides) | — | stdout | stdout | |
| 37 | config/loader.py:107 | Config | system_log | warning | log.warning("Configuration result is empty. Check config files and environment.") | — | stdout | stdout | |
| 38 | db/session.py:6 | DB | system_log | getLogger | log = structlog.get_logger() | — | stdout (default) | stdout | |
| 39 | db/session.py:15 | DB | system_log | info | log.info("Database session configured", db_url=db_url) | — | stdout | stdout | |
| 40 | db/init_data.py:16 | DB Init | system_log | getLogger | logger = logging.getLogger(__name__) | — | stdout (default) | stdout | |
| 41 | db/init_data.py:28 | DB Init | system_log | error | logger.error(f"Failed to import required modules: {e}") | — | stdout | stdout | |
| 42 | db/init_data.py:44 | DB Init | system_log | warning | logger.warning(f"Standard DB session failed: {e}") | — | stdout | stdout | |
| 43 | db/init_data.py:45 | DB Init | system_log | info | logger.info("Trying to connect using localhost instead...") | — | stdout | stdout | |
| 44 | db/init_data.py:62 | DB Init | system_log | info | logger.info(f"Admin user '{DEFAULT_ADMIN['username']}' already exists with ID: {existing_admin.id}") | — | stdout | stdout | |
| 45 | db/init_data.py:77 | DB Init | system_log | info | logger.info(f"Admin user '{DEFAULT_ADMIN['username']}' created with ID: {new_admin.id}") | — | stdout | stdout | |
| 46 | db/init_data.py:89 | DB Init | system_log | info | logger.info(f"Tag '{tag_data['name']}' already exists with ID: {existing_tag.id}") | — | stdout | stdout | |
| 47 | db/init_data.py:101 | DB Init | system_log | info | logger.info(f"Tag '{tag_data['name']}' created with ID: {new_tag.id}") | — | stdout | stdout | |
| 48 | db/init_data.py:120 | DB Init | system_log | info | logger.info(f"Credential with username '{cred_data['username']}' already exists with ID: {result[0]}") | — | stdout | stdout | |
| 49 | db/init_data.py:146 | DB Init | system_log | info | logger.info(f"System credential '{cred_data['username']}' created with ID: {new_cred.id}") | — | stdout | stdout | |
| 50 | db/init_data.py:151 | DB Init | system_log | error | logger.error(f"Error creating credential: {e}") | — | stdout | stdout | |
| 51 | db/init_data.py:170 | DB Init | system_log | warning | logger.warning("Default tag not found, cannot associate with devices") | — | stdout | stdout | |
| 52 | db/init_data.py:177 | DB Init | system_log | info | logger.info("All existing devices already have the default tag") | — | stdout | stdout | |
| 53 | worker/error_handler.py:35 | Error Handler | system_log | getLogger | logger = logging.getLogger(__name__) | — | stdout (default) | stdout | |
| 54 | worker/error_handler.py:226 | Error Handler | system_log | log (dynamic) | logger_to_use.log(self.log_level, msg, extra=log_data) | — | stdout | stdout | |
| 55 | scheduler/scheduler_runner.py:8 | Scheduler | system_log | getLogger | log = structlog.get_logger() | — | stdout (default) | stdout | |
| 56 | scheduler/scheduler_runner.py:34 | Scheduler | system_log | info | log.info("Starting NetRaven Scheduler", redis_url=redis_url, poll_interval=polling_interval) | — | stdout | stdout | |
| 57 | scheduler/scheduler_runner.py:38 | Scheduler | system_log | info | log.info("Successfully connected to Redis.") | — | stdout | stdout | |
| 58 | scheduler/scheduler_runner.py:41 | Scheduler | system_log | error | log.error("Failed to connect to Redis or initialize scheduler", error=str(e), redis_url=redis_url) | — | stdout | stdout | |
| 59 | scheduler/scheduler_runner.py:45 | Scheduler | system_log | info | log.info("Scheduler polling for jobs...") | — | stdout | stdout | |
| 60 | scheduler/scheduler_runner.py:48 | Scheduler | system_log | debug | log.debug("Job sync process completed.") | — | stdout | stdout | |
| 61 | scheduler/scheduler_runner.py:50 | Scheduler | system_log | error | log.error("Error during job synchronization", error=str(e), exc_info=True) | — | stdout | stdout | |
| 62 | scheduler/scheduler_runner.py:52 | Scheduler | system_log | debug | log.debug(f"Scheduler sleeping for {polling_interval} seconds.") | — | stdout | stdout | |
| 63 | scheduler/job_registration.py:12 | Job Registration | system_log | getLogger | log = structlog.get_logger() | — | stdout (default) | stdout | |
| 64 | scheduler/job_registration.py:21 | Job Registration | system_log | debug | log.debug("Starting job synchronization from database...") | — | stdout | stdout | |
| 65 | scheduler/job_registration.py:27 | Job Registration | system_log | info | log.info(f"Found {len(jobs_to_schedule)} enabled jobs in DB.") | — | stdout | stdout | |
| 66 | scheduler/job_registration.py:31 | Job Registration | system_log | debug | log.debug(f"{len(existing_rq_job_ids)} jobs currently in RQ-Scheduler.") | — | stdout | stdout | |
| 67 | scheduler/job_registration.py:49 | Job Registration | system_log | debug | log.debug("Job already scheduled in RQ-Scheduler, skipping.", **job_log_details) | — | stdout | stdout | |
| 68 | scheduler/job_registration.py:53 | Job Registration | system_log | debug | log.debug("Job is disabled, skipping.", **job_log_details) | — | stdout | stdout | |
| 69 | scheduler/job_registration.py:67 | Job Registration | job_log | info | "Scheduled interval job '{job_name}' (interval: {interval}s)" | job_id | stdout | stdout, db | |
| 70 | scheduler/job_registration.py:80 | Job Registration | job_log | info | "Scheduled cron job '{job_name}' (cron: {cron_string})" | job_id | stdout | stdout, db | |
| 71 | scheduler/job_registration.py:97 | Job Registration | job_log | info | "Scheduled one-time job '{job_name}' for {run_time}" | job_id | stdout | stdout, db | |
| 72 | scheduler/job_registration.py:103 | Job Registration | job_log | warning | "One-time job '{job_name}' scheduled in the past for {run_time}, skipping" | job_id | stdout | stdout, db | |
| 73 | scheduler/job_registration.py:108 | Job Registration | job_log | warning | "Job '{job_name}' has no valid schedule type/params, skipping" | job_id | stdout | stdout, db | |
| 74 | scheduler/job_registration.py:115 | Job Registration | job_log | error | "Failed to schedule job '{job_name}': {error}" | job_id | stdout | stdout, db | |
| 75 | scheduler/job_registration.py:122 | Job Registration | job_log | info | "Finished job synchronization. Total enabled: {total_enabled}, newly scheduled: {newly_scheduled}, skipped: {skipped}, errors: {errors}" | — | stdout | stdout, db | |
| 76 | scheduler/job_registration.py:127 | Job Registration | system_log | error | log.error("Error during database query or setup", error=str(e), exc_info=True) | — | stdout | stdout | |
| 77 | scheduler/job_registration.py:135 | Job Registration | system_log | debug | log.debug("Database session closed.") | — | stdout | stdout | |
| 78 | worker/executor.py:63 | Executor | system_log | getLogger | log = logging.getLogger(__name__) | — | stdout (default) | | |
| 79 | worker/executor.py:83 | Executor | job_log | info | "Entered reachability handler for device '{device_name}' in job '{job_name}'" | job_id, device_id | stdout | stdout, db | |
| 80 | worker/executor.py:123 | Executor | job_log | info | "About to save job log (success) for device '{device_name}' in job '{job_name}'" | job_id, device_id | stdout | stdout, db | |
| 81 | worker/executor.py:124 | Executor | job_log | info | "Reachability check completed successfully for device '{device_name}' in job '{job_name}'" | job_id, device_id | db | stdout, db | |
| 82 | worker/executor.py:125 | Executor | job_log | info | "Saved job log (success) for device '{device_name}' in job '{job_name}'" | job_id, device_id | stdout | stdout, db | |
| 83 | worker/executor.py:134 | Executor | job_log | info | "About to save job log (failure) for device '{device_name}' in job '{job_name}'" | job_id, device_id | stdout | stdout, db | |
| 84 | worker/executor.py:135 | Executor | job_log | info | "Reachability check failed for device '{device_name}' in job '{job_name}': {msg}" | job_id, device_id | db | stdout, db | |
| 85 | worker/executor.py:136 | Executor | job_log | info | "Saved job log (failure) for device '{device_name}' in job '{job_name}'" | job_id, device_id | stdout | stdout, db | |
| 86 | worker/executor.py:138 | Executor | job_log | error | "Exception in save_job_log for device '{device_name}' in job '{job_name}': {log_exc}" | job_id, device_id | stdout | stdout, db | |
| 87 | worker/executor.py:162 | Executor | job_log | info | "handle_device called for job '{job_name}'" | job_id | stdout | stdout, db | |
| 88 | worker/executor.py:165 | Executor | job_log | error | "No handler registered for job type '{job_type}' in job '{job_name}'" | job_id | stdout | stdout, db | |
| 89 | worker/executor.py:167 | Executor | job_log | info | "Dispatching job '{job_name}' (type: {job_type}) to handler: {handler_name}" | job_id | stdout | stdout, db | |
| 90 | scheduler/job_definitions.py:7 | Job Definitions | system_log | getLogger | log = structlog.get_logger() | — | stdout (default) | | |
| 91 | scheduler/job_definitions.py:15 | Job Definitions | job_log | info | "Executing scheduled job '{job_name}' via worker" | job_id | stdout | stdout, db | |
| 92 | scheduler/job_definitions.py:17 | Job Definitions | job_log | info | "Worker job execution finished for job '{job_name}'" | job_id | stdout | stdout, db | |
| 93 | scheduler/job_definitions.py:20 | Job Definitions | job_log | error | "Worker job execution failed for job '{job_name}': {error}" | job_id | stdout | stdout, db | |
| 100 | worker/netmiko_session.py | Worker | connection_log | debug | "Netmiko session log: {session_event}" | job_id, device_id | — | stdout, redis channel | Session log: should be streamed to Redis for real-time UI, not persisted in DB. Not yet implemented. |
// ... more entries to be added from other files ... 

---

## Implementation Notes & Required Codebase Changes

- All log entries must explicitly list 'stdout' in the Desired Destinations column, regardless of whether it is present in Current Destinations. This is to ensure clarity for all developers that stdout is always a required destination.
- All log entries must be routed to stdout in addition to any other destinations (db, redis channel, etc.).
- All job_log entries must be routed to the DB for persistence and UI display.
- All connection_log entries for life cycle events (connect, authenticate, run command, disconnect) must be routed to the DB.
- Netmiko session logs (low-level debug/session events) should be streamed to a Redis channel for real-time UI, not persisted in the DB. This requires a new handler or Netmiko integration.
- Audit the codebase for missing connection_log calls for all device life cycle events and add as needed.
- Add a Redis log handler for Netmiko session logs.
- Update logging configuration and documentation accordingly. 