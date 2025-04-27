# Device Edit Modal: Error Handling and Update Failures — Implementation Plan

## 1. Overview

**Problem:**
- Editing a device via the UI sometimes results in a generic error ("Failed to update device"), with insufficient feedback for users or developers.
- The frontend does not always display backend error messages clearly, making troubleshooting difficult.

**Goal:**
- Provide clear, actionable error messages for device update failures.
- Ensure the frontend displays backend error messages directly to the user.
- Improve developer and user experience for troubleshooting device update issues.

---

## 2. Phases & Tasks

### Phase 1: Backend Error Handling Improvements
**Objective:** Ensure all backend error responses are specific and actionable.

**Tasks:**
1. In `netraven/api/routers/devices.py`, review and refactor error handling in the `update_device` endpoint:
   - Ensure all error responses are specific (e.g., "Tag not found: [id]", "Default tag missing", "Hostname already exists").
   - Log errors with sufficient detail for debugging.
2. Review other device-related endpoints for consistency in error messaging.

**Testing/Validation:**
- Simulate common error scenarios (e.g., missing tag, duplicate hostname) via API and verify that the error messages are clear and specific.
- Check backend logs for detailed error information.

**Notes:**
- Review current error messages returned by the backend for device update failures.
- Optionally, request user to reproduce the error and provide the full error response from the browser's network tab or backend logs.

---

### Phase 2: Frontend Error Display and Feedback
**Objective:** Ensure the frontend displays backend error messages directly to the user and provides actionable feedback.

**Tasks:**
1. In the device store (`frontend/src/store/device.js`) and modal (`frontend/src/components/DeviceFormModal.vue`):
   - Display backend error messages in the UI when device update fails.
   - If the error is generic, provide a fallback message with instructions to contact support.
2. Ensure error messages are visible and styled for clarity (e.g., alert box, modal, or inline message).
3. Test error handling for both device creation and update flows.

**Testing/Validation:**
- Simulate errors (e.g., missing tag, duplicate hostname) and verify UI feedback.
- Check browser network tab for error responses and ensure they are surfaced to the user.
- Manually test device creation and editing in the UI to ensure error messages are clear and actionable.

**Notes:**
- If possible, provide a screenshot or the full error response from the browser's network tab when the device update fails.

---

### Phase 3: Documentation and Dev Log
**Objective:** Document the process and rationale for future reference.

**Tasks:**
1. Write this implementation plan in `/docs/developer/device-edit-modal-error-handling.md` (this file).
2. If changes are made, maintain a dev log in `/docs/development_log/<feature-branch>/` summarizing:
   - What was changed
   - Why it was changed
   - Any issues encountered

**Testing/Validation:**
- Ensure documentation is clear, complete, and up to date.

**Notes:**
- Reference this plan in all related pull requests and code reviews.

---

## 3. Discovery/Inputs Needed
- **UI Error Details:** If possible, provide a screenshot or the full error response from the browser's network tab when the device update fails.
- **Backend Error Messages:** Review and confirm the specificity of current backend error messages for device update failures.

---

## 4. Appendix
- **Backend:** `netraven/api/routers/devices.py`, `netraven/api/schemas/device.py`
- **Frontend:** `frontend/src/pages/Devices.vue`, `frontend/src/components/DeviceFormModal.vue`, `frontend/src/store/device.js`
- **Testing:** Use Docker-based pytest command for backend; manual/automated tests for frontend.
- **Documentation:** `/docs/developer/device-edit-modal-error-handling.md`, `/docs/development_log/<feature-branch>/` 