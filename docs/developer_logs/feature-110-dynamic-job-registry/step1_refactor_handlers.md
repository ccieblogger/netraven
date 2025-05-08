# Step 1: Refactor Job Handlers to Dynamic Modules

## Actions
- Moved reachability job logic from `executor.py` to `jobs/reachability.py` as a dynamic job module with `JOB_META` and `run()`.
- Reconstructed configuration backup job logic in `jobs/config_backup.py` as a dynamic job module with `JOB_META` and `run()`.
- Both modules now use the unified logger from `netraven.utils.unified_logger` for all logging, with required metadata (`log_type`, `source`, `job_id`, `device_id`).
- Removed the previous use of `JobLogger` to ensure all logs are routed through the NetRaven unified logging system.
- No changes yet to the static registry or handler removal (pending Step 2).

## Insights
- The backup handler in `executor.py` referenced `_legacy_backup_logic`, which was not defined. The new module reconstructs the backup logic using `netmiko_driver`, `redactor`, and `git_writer`.
- The reachability handler logic was directly migrated and refactored to use the unified logger.
- All job modules are now plug-and-play and auto-discovered by the dynamic registry.
- **Correction:** The initial refactor used a custom `JobLogger` class, but this was replaced with the unified logger to ensure consistency and compliance with NetRaven's logging standards.

## Next Steps
- Remove static handlers and registry from `executor.py`.
- Update dispatch logic to use the dynamic registry.
- Update tests and references as needed. 