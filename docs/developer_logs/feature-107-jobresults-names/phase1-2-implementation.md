# Developer Log: Feature 107 - job_name and device_name in /job-results/

## Phase 1: Discovery
- Located /job-results/ endpoint in netraven/api/routers/job_results.py.
- Confirmed JobResult model has relationships to Job and Device.
- Identified human-readable fields: Job.name and Device.hostname.
- No direct tests for /job-results/ found; new tests will be added.

## Phase 2: Implementation
- Added JobResultWithNamesRead schema (extends JobResultRead) with job_name and device_name fields.
- Updated PaginatedJobResultResponse to use JobResultWithNamesRead.
- Updated /job-results/ endpoint to join Job and Device, and return job_name and device_name in each result.
- Updated get_job_result endpoint to return job_name and device_name.
- Next: Add/extend tests for /job-results/ to verify new fields. 