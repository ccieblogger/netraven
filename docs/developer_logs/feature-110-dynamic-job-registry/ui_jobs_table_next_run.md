# UI Jobs Table: Add Next Run Column (Issue 110, Work Stream 3)

## Date
2025-05-08

## Summary
- Updated the jobs management page (`Jobs.vue`) to include a **Next Run** column in the jobs table.
- The page now fetches scheduled jobs from the `/jobs/scheduled` API endpoint and joins this data with the main jobs list by job ID.
- The `Next Run` column displays the next scheduled execution time for each job, or `-` if not scheduled.
- This improves clarity for users by showing both the schedule and the next run time for all jobs, supporting both ad-hoc and recurring jobs.

## Rationale
- Users need to see not just the job schedule, but also when the next execution will occur, especially for recurring jobs.
- This aligns the UI with best practices for job management and monitoring.

## Next Steps
- Further UI/UX polish and advanced filtering can be added in future workstreams. 