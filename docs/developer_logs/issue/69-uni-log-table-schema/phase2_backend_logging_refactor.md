# Development Log: Phase 2 - Backend Logging Refactor (Issue #69)

## Summary
Refactored all logging utility functions and the central UnifiedLogger to use the new unified `logs` table and model. Removed all references to the old `JobLog` and `ConnectionLog` models in logging utilities. All DB log events are now routed through the unified log model, supporting all log types.

## Rationale
- Ensures all logs (job, connection, session, system, etc.) are stored in a single, extensible table.
- Simplifies log handling and future-proofs the system for new log types and features.
- Aligns with the unified logging architecture and requirements in issues #68 and #69.

## Files Changed
- `netraven/db/log_utils.py`: Refactored to provide a single `save_log` function for all log types.
- `netraven/utils/unified_logger.py`: Updated to use `save_log` for all DB log events; removed legacy logic.

## Next Steps
- Refactor API endpoints and schemas to use the unified log model (Phase 3).
- Update worker, scheduler, and service logic to use the new logging utilities throughout.
- Remove any remaining references to old log models in the codebase.
- Update and expand tests for unified logging.

---
**Commit:** refactor(logging): route all DB log events through unified logs table and model; update utilities and logger (#69)
**Date:** $(date) 