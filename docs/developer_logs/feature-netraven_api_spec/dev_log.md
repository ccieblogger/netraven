# Developer Log: NetRaven API Spec Documentation

## 2024-06-09
- Started work on comprehensive NetRaven API endpoint documentation.
- Inventorying all endpoints from routers and main FastAPI app.
- Will document each endpoint with method, path, description, parameters, authentication, and example usage. 

## 2024-06-09 (Phase 2)
- Proceeding to add detailed endpoint documentation.
- Will include real request/response JSON, field explanations, and UI integration notes for frontend developers. 

## 2025-05-06 (Workstream 1: Documentation Alignment & Cleanup)
- Audited all job, job-results, and logs endpoints in code and documentation.
- Identified redundancy: per-device job status is stored in both `job_results` and the unified `logs` table; both `/job-results/` and `/jobs/{job_id}/devices` provide per-device job results, but from different sources.
- `/logs/` endpoint is the canonical unified log table, supporting rich filtering and streaming.
- `/job-logs/` endpoint is not implemented in backend; frontend should use `/logs/`.
- Documentation in `netraven_api_spec.md` and `job_lifecycle_spec.md` does not clearly explain the relationship or distinction between these endpoints, leading to confusion.
- Plan: Update API spec to clarify the purpose, data model, and intended use of each endpoint; mark deprecated/legacy endpoints; add diagrams and migration notes for frontend/backend alignment.
- Next: Edit `netraven_api_spec.md` and `job_lifecycle_spec.md` for clarity and accuracy, then request review before proceeding to Workstream 2. 

## 2025-05-07 (Workstream 2: API Integration for JobsDashboard.vue)
- Started Workstream 2: Wire up JobsDashboard.vue to backend API endpoints.
- Reviewed GitHub issue #101 and confirmed requirements for dashboard metrics, job runs, and unified logs.
- Audited current JobsDashboard.vue and subcomponents: all use mock data; filters and pagination are local.
- Identified required endpoints from netraven_api_spec.md:
  - `/jobs/` for job summary and job runs (with filters/pagination)
  - `/logs/` for unified logs (with filters/pagination)
- Located Pinia stores and jobsDashboardService for API calls; will leverage and extend as needed.
- Plan:
  1. Replace mock data in JobsDashboard.vue with real API calls for jobs and logs.
  2. Wire up filters and pagination to backend queries.
  3. Add loading and error states.
  4. Remove all mock data.
- Correction: Job summary cards and job runs table now fetch data from `/job-results/` endpoint (not `/jobs/`), as per canonical data model. Created new Pinia store `job_results.js` for this purpose. All mock data and jobStore usage for job runs/summary removed.
- Reason: `/job-results/` is the canonical source for per-device job run history and status, as clarified in the API spec and project requirements.
- Next: Integrate unified logs table with `/logs/`
- Proceeding with Unified Logs table integration (Phase 2b) and all other non-blocked UI elements in JobDashboard.vue. Job/device name display in job results table will use fallback until backend enhancement #107 is implemented.