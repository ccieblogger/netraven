# Phase 2: Deduplication Logic & Database-Only Config Backup

**Date:** 2025-05-09

## Summary
- Refactored the config backup job to store configuration snapshots only in the database (Postgres), removing all Git logic.
- Added SHA-256 deduplication: new snapshots are only stored if the config content has changed.
- Added a utility for SHA-256 hashing (`netraven/utils/hash_utils.py`).
- Updated the SQLAlchemy model and initialization migration for the new `data_hash` column and FTS index.
- All changes committed to feature branch `issue/112-refactor-config-bkp-ws1`.

## Next Steps
- Implement the Python script for processing old snapshots and scheduling via RQ/Redis.
- Begin work on API endpoints for config retrieval, search, and diff.

---

**Commit:** feat(config-backup): refactor to database-only versioned store with deduplication and FTS index (issue #112)
