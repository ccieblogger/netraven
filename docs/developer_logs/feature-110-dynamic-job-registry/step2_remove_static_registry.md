# Step 2: Remove Static Handlers and Registry, Update Dispatch Logic

## Actions
- Removed `backup_device_handler` and `reachability_handler` from `executor.py`.
- Removed the static `JOB_TYPE_HANDLERS` dictionary from `executor.py`.
- Updated the `handle_device` function to use the dynamic registry (`JOB_TYPE_REGISTRY`) from `job_registry.py` for job dispatch.
- All job dispatching is now fully dynamic and plug-and-play, supporting new job types without backend code changes.

## Insights
- The codebase is now aligned with the dynamic job registry architecture, reducing maintenance overhead and risk of handler duplication.
- All job modules must be present in `netraven/worker/jobs/` and follow the required interface to be discoverable and dispatchable.

## Next Steps
- Update or add tests to ensure dynamic dispatch works as expected.
- Continue with API and UI integration as described in the work stream plan. 