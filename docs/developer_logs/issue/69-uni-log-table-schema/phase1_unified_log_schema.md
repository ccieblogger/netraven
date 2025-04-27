# Development Log: Phase 1 - Unified Log Table Schema (Issue #69)

## Summary
Implemented the unified `logs` table and SQLAlchemy model as specified in [issue #69](https://github.com/ccieblogger/netraven/issues/69), replacing the previous `job_logs` and `connection_logs` tables. Updated the initial Alembic migration, removed deprecated models, and updated model imports.

## Rationale
- Simplifies log storage and future-proofs the system for additional log types (session, system, etc.).
- Enables robust filtering and extensibility via a single schema.
- Aligns with the parent epic ([issue #68](https://github.com/ccieblogger/netraven/issues/68)).

## Files Changed
- `netraven/db/models/log.py`: New unified log model.
- `netraven/db/models/__init__.py`: Updated imports for new model, removed deprecated ones.
- `alembic/versions/a3992da91329_initial_schema_definition.py`: Added `logs` table, removed `job_logs` and `connection_logs`.
- `netraven/db/models/job_log.py`: Deleted.
- `netraven/db/models/connection_log.py`: Deleted.

## Next Steps
- Refactor backend logging logic to use the new `Log` model (Phase 2).
- Update API endpoints and tests to use the unified log table.
- Remove any remaining references to old log models.
- Implement real-time log streaming and retention (future phases).

---
**Commit:** feat(logging): implement unified logs table, model, and migration per #69; remove job_log and connection_log models and tables
**Date:** $(date) 