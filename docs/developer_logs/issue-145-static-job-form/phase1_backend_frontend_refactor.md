# WS-04B: Static Job Form Refactor — Phase 1 Log

**Date:** 2025-05-21

## Summary
- Refactored backend `/jobs/metadata/{name}` endpoint to return only name, description, and has_parameters.
- Added `/jobs/execute` endpoint to accept raw_parameters (JSON or markdown) and schedule, routing to the correct job method.
- Updated `BaseJob` to support `execute_with_markdown` for plugin authors.
- Refactored frontend `JobForm.vue` and `JobRun.vue` to use a static textarea for parameters and match the new backend contract.
- Removed all dynamic form and JSON schema dependencies from the job run UI.

## Acceptance
- UI now displays a simple textarea and schedule input for jobs.
- Backend correctly parses JSON or markdown and routes to the appropriate job method.
- All changes committed to feature branch `issue/139-job-plugin-ws4`.

## Next Steps
- Update user and developer documentation.
- Remove any remaining legacy dynamic form code if found.
- QA and request review.
