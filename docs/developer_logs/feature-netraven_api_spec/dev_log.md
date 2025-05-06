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
- Identified redundancy: per-device job status is stored in both `job_results` and the unified `logs` table; both `/job-results/` and `/jobs/{job_id}/devices` provide per-device job results, but from different sources. `/jobs/{job_id}/devices` is now marked as **DEPRECATED** in the API docs, with migration guidance to use `/job-results/?job_id=...` instead.
- `/logs/` endpoint is the canonical unified log table, supporting rich filtering and streaming.
- `/job-logs/` endpoint is not implemented in backend and is now marked as **REMOVED** in the API docs. All references should be removed from frontend and documentation. `/logs/` is the canonical log/event endpoint.
- Documentation in `netraven_api_spec.md` and `job_lifecycle_spec.md` does not clearly explain the relationship or distinction between these endpoints, leading to confusion.
- Plan: Update API spec to clarify the purpose, data model, and intended use of each endpoint; mark deprecated/legacy endpoints; add diagrams and migration notes for frontend/backend alignment.
- Next: Edit `netraven_api_spec.md` and `job_lifecycle_spec.md` for clarity and accuracy, then request review before proceeding to Workstream 2. 

[2024-06-09] Updated API documentation to deprecate `/jobs/{job_id}/devices` and remove `/job-logs/`. Added migration notes clarifying canonical data sources for per-device job status and logs.

[2024-06-09] Workstream 1 complete: Deprecated `/jobs/{job_id}/devices` in API and architecture docs, removed `/job-logs/` references, clarified canonical endpoints, and added migration notes. Updated: `netraven_api_spec.md`, `job_lifecycle_spec.md`, `MyNotes.md`, and relevant developer logs. 