# NetRaven Job Plugin Static Form (WS-04B)

## Overview
NetRaven jobs now use a static form for job input, supporting only text and markdown (no dynamic JSON schema forms). This simplifies the UI and backend, and improves maintainability.

## How to Use
- When running a job, you will see a textarea for parameters (accepts JSON or Markdown) and a simple schedule input.
- The backend will attempt to parse the input as JSON. If parsing fails, it will treat the input as Markdown/text and route it to the plugin's `execute_with_markdown` method.
- If the job does not require parameters, you can run it directly without input.

## Developer Notes
- The `/jobs/metadata/{name}` endpoint now returns only `name`, `description`, and `has_parameters`.
- The `/jobs/execute` endpoint accepts `raw_parameters` (string) and `schedule`.
- Plugin authors can override `execute_with_markdown` in their job class for custom Markdown handling.

## Migration Notes
- All dynamic form and JSON schema logic has been removed from the job run UI and backend.
- See developer log: `docs/developer_logs/issue-145-static-job-form/phase1_backend_frontend_refactor.md` for details.

## Example
```
POST /jobs/execute
{
  "name": "backup",
  "raw_parameters": "# Backup job\nDevice: core-sw-01",
  "schedule": "@daily"
}
```

---
For more information, contact the NetRaven development team.
