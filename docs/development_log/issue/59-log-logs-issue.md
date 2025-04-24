# Development Log: Issue 59 - Job Handler Dispatch Refactor (Job Logs Not Written)

## Summary
This log documents the investigation and resolution of issue #59, where job logs (especially for reachability jobs) were not being written to the database. The root cause was identified as the job handler dispatch mechanism not using the `JOB_TYPE_HANDLERS` registry, resulting in the wrong code path for non-backup jobs.

## Root Cause
- The `handle_device` function in `netraven/worker/executor.py` did not dispatch to the correct handler based on job type.
- The `JOB_TYPE_HANDLERS` registry was defined but never used in the device execution path.
- As a result, reachability jobs did not call `reachability_handler`, and no job logs were written for those jobs.

## Solution Plan
1. Refactor `handle_device` to dispatch to the correct handler using `JOB_TYPE_HANDLERS`.
2. Move all job-type-specific logic into their respective handler functions.
3. Ensure all handlers call `save_job_log` as appropriate.
4. Test reachability and backup jobs to confirm job logs are written.

## Progress Log
- [x] Refactor `handle_device` to use `JOB_TYPE_HANDLERS`.
- [ ] Move backup logic into `backup_device_handler` if not already done.
- [ ] Test reachability job execution and confirm job logs in DB.
- [ ] Commit and push changes after each phase.

---

This log will be updated as work progresses on this issue. 