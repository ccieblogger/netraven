# NetRaven Logging System Audit 2025 (Working Draft)

This document is a working draft for the 2025 audit of all logging calls in the NetRaven codebase. It is modeled after previous audits but is a new, separate file for iterative development. As we review and improve the logging system, update this file with new findings, changes, and recommendations. Once finalized, this will become the living inventory for all logging in NetRaven.

---

## How to Use & Update
- Add new log calls as you discover or implement them.
- Update or annotate existing entries as you review or refactor code.
- Use this document for code reviews, audits, and to ensure all critical events are logged to the correct destinations.
- When finalized, this document will be moved to the main docs folder as the canonical reference.

**Columns:**
- #: Sequential number
- File & Line: Path and line number
- Function/Context: Function or code context
- Log Type: e.g., job_log, system_log, connection_log
- Level: Log level (INFO, WARNING, ERROR, etc.)
- Message/Content: Main message or format string
- Destinations: Where the log is routed (stdout, db, redis, etc.)
- Notes: Any special notes, e.g., if this is a critical event, fallback, or needs improvement

---

| # | File & Line | Function/Context | Log Type | Level | Message/Content | Destinations | Notes |
|---|-------------|------------------|----------|-------|-----------------|-------------|-------|
| 1 | api/routers/auth_router.py:45 | login_for_access_token | system_log | INFO | "Login attempt for user: {form_data.username}" | stdout | UnifiedLogger |
| 2 | api/routers/auth_router.py:54 | login_for_access_token | system_log | WARNING | "Login attempt for inactive user: {form_data.username}" | stdout | UnifiedLogger |
| 3 | api/routers/auth_router.py:60 | login_for_access_token | system_log | INFO | "Token generated successfully for user: {form_data.username}" | stdout | UnifiedLogger |
| 4 | api/routers/jobs.py:296 | jobs_router | system_log | ERROR | "Failed to get Redis info: {e}" | stdout | UnifiedLogger |
| 5 | scheduler/job_definitions.py:18 | schedule_job | job_log | INFO | "Executing scheduled job '{job_name}' via worker" | stdout, db | UnifiedLogger |
| 6 | scheduler/job_definitions.py:27 | schedule_job | job_log | INFO | "Worker job execution finished for job '{job_name}'" | stdout, db | UnifiedLogger |
| 7 | scheduler/job_definitions.py:36 | schedule_job | job_log | ERROR | "Worker job execution failed for job '{job_name}': {error}" | stdout, db | UnifiedLogger |
| 8 | worker/executor.py:85 | handle_device | job_log | INFO | "Entered reachability handler for device '{device_name}' in job '{job_name}'" | stdout, db | UnifiedLogger |
| 9 | worker/executor.py:132 | handle_device | job_log | ERROR | "No handler registered for job type '{job_type}' in job '{job_name}'" | stdout, db | UnifiedLogger |
| 10 | db/init_data.py:31 | initialize_db | system_log | INFO | "Database initialization started" | stdout | UnifiedLogger |
| 11 | db/log_utils.py:31 | save_log | system_log | ERROR | "[LOGGER EXCEPTION] {e}" | stdout | Only on DB log failure |
| 12 | utils/unified_logger.py:205 | _log_to_db | system_log | DEBUG | "_log_to_db called with record: {record}" | stdout | Debug only |
| 13 | worker/runner.py:386 | run_job | job_log | ERROR | "log_runner_error(job_id, error_msg_for_log, db_to_use, error_type='CREDENTIAL')" | db | Used for critical job-level errors |
| 14 | worker/runner.py:403 | run_job | job_log | ERROR | "log_runner_error(job_id, error_msg, db_to_use)" | db | Used for general job-level errors |
| 15 | worker/device_capabilities.py:315 | detect_capabilities | system_log | WARNING | "Unknown device type: {device_type}, using default commands" | stdout | UnifiedLogger |
| 16 | worker/device_capabilities.py:346 | detect_capabilities | system_log | WARNING | "Unknown command type: {command_type} for device: {device_type}" | stdout | UnifiedLogger |
| 17 | worker/device_capabilities.py:352 | detect_capabilities | system_log | ERROR | "No default found for command type: {command_type}" | stdout | UnifiedLogger |
| 18 | worker/device_capabilities.py:432 | detect_capabilities | system_log | WARNING | "No capability patterns defined for {device_type}, using limited detection" | stdout | UnifiedLogger |
| 19 | worker/device_capabilities.py:442 | detect_capabilities | system_log | WARNING | "[Job: {job_id}] Could not parse {capability} from output for {device_name}" | stdout | UnifiedLogger |
| 20 | worker/device_capabilities.py:472 | detect_capabilities | system_log | WARNING | "No capability flags defined for {device_type}, using defaults" | stdout | UnifiedLogger |

<!-- Add more rows as you discover or add log calls. Keep this table up to date during the audit! -->

---

## Notes
- This table is a working draft. Continue to add log calls as you audit more files or add new features.
- For a full audit, repeat the search for logger.log, save_log, log_runner_error, and print in all backend directories.
- Use this as the working reference for all logging in NetRaven until finalized. 