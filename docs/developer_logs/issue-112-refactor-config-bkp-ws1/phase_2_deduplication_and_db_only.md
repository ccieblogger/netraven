# Phase 2: Deduplication Logic & Database-Only Config Backup

**Date:** 2025-05-09

## Summary
- Refactored the config backup job to store configuration snapshots only in the database (Postgres), removing all Git logic.
- Added SHA-256 deduplication: new snapshots are only stored if the config content has changed.
- Added a utility for SHA-256 hashing (`netraven/utils/hash_utils.py`).
- Updated the SQLAlchemy model and initialization migration for the new `data_hash` column and FTS index.
- All changes committed to feature branch `issue/112-refactor-config-bkp-ws1`.

## Phase 2: Retention Job Registration & Scheduling

- Implemented `prune_old_device_configs` in `netraven/scheduler/job_definitions.py` to prune old config snapshots per device, keeping the N most recent (configurable).
- Registered and scheduled the retention job in the scheduler via `schedule_retention_job` in `netraven/scheduler/scheduler_runner.py`.
    - The job is scheduled to run at a configurable interval (default: daily) and is registered only once.
    - Logging is performed for job registration and execution.
- No changes required in `job_registration.py` as the scheduling logic is handled in `scheduler_runner.py`.
- Next: Expand `/api/configs` endpoints and add/expand tests as per the plan.

## Next Steps
- Implement the Python script for processing old snapshots and scheduling via RQ/Redis.
- Begin work on API endpoints for config retrieval, search, and diff.

---

**Commit:** feat(config-backup): refactor to database-only versioned store with deduplication and FTS index (issue #112)
