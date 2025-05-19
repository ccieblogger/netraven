# Developer Log: Frontend–Backend Integration Documentation

**Date:** 2025-05-17

**Summary:**
Added and updated `docs/architecture/frontend_backend_integration.md` to provide clear guidance for frontend developers on wiring up UI/UX to backend API endpoints, with a dedicated section on NGINX proxying and the `/api` prefix requirement.

## Key Changes
- Added section explaining NGINX proxying, `/api` prefix, and troubleshooting tips.
- Clarified that all API calls must go through NGINX and use relative paths.
- Provided best practices, code examples, and references to API spec and service modules.

## Rationale
- Prevents common mistakes with direct backend calls or missing prefixes.
- Ensures all environments (dev/prod/container) work consistently.
- Supports maintainability and onboarding for new developers.

## Next Steps
- Monitor for developer questions or confusion and update documentation as needed.
- Reference this doc in onboarding and code review checklists.

---
