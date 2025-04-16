# Device Must Always Have Default Tag: Implementation Plan

## 1. Overview

**Problem:**
- Devices must always be associated with the default tag. This is not enforced on device updates, and the frontend allows users to remove the default tag.

**Goal:**
- Guarantee that all devices always have the default tag, both in the backend and frontend.
- Prevent users from removing the default tag in the UI.
- Ensure robust testing and documentation for future maintainers.

---

## 2. Phases & Tasks

### Phase 1: Backend Enforcement of Default Tag
**Objective:** Guarantee all devices always have the default tag, regardless of frontend input.

**Tasks:**
1. In `netraven/api/routers/devices.py`, update the `update_device` endpoint:
   - After extracting tag IDs from the update payload, always add the default tag if missing.
   - If the tag list is empty or missing, set it to `[default_tag.id]`.
   - If the default tag does not exist in the DB, return a clear error (e.g., "Default tag not found. Please contact an administrator.").
2. Add/extend backend tests to cover:
   - Device update with no tags provided (should still have default tag).
   - Device update with tags provided, but missing default tag (should be added).
   - Device update with tags including default tag (should succeed).
   - Device update with empty tag list (should still have default tag).
3. If legacy devices exist without the default tag, consider writing a migration script to associate the default tag with all devices.

**Testing/Validation:**
- Run backend pytests for device CRUD using:
  ```
  docker exec -it netraven-api-dev bash -c "cd /app && PYTHONPATH=/app poetry run pytest <test name>"
  ```
- Manually test via API (e.g., with curl or Postman) to ensure the default tag is always present after updates.

**Notes:**
- Confirm the default tag's name/ID in the DB (usually "default").
- If a migration is needed, document and test it separately.

---

### Phase 2: Frontend Tag Selector UX
**Objective:** Prevent users from removing the default tag in the UI.

**Tasks:**
1. In `DeviceFormModal.vue`, ensure the default tag is always selected and cannot be removed:
   - On modal open, always include the default tag in the selected tags.
   - On form submit, always include the default tag ID in the payload.
2. In `TagSelector.vue`, visually distinguish and lock the default tag:
   - Make the default tag visually distinct (e.g., badge, lock icon, or disabled checkbox).
   - Prevent users from deselecting the default tag (disable its removal in the UI).
3. If necessary, extend the tag selector component to support "locked" or "non-removable" tags.
4. Manually test device creation and editing to ensure the default tag cannot be removed and is always present in the device list and edit modal.

**Testing/Validation:**
- Manually test device creation/edit in the UI.
- Try to remove all tags—default tag should remain.

**Notes:**
- Confirm how the default tag is identified in the frontend (by name or ID).
- Ensure the tag selector supports disabling/removing options, or extend it as needed.

---

### Phase 3: Documentation and Dev Log
**Objective:** Document the process and rationale for future reference.

**Tasks:**
1. Write this implementation plan in `/docs/developer/device-default-tag-enforcement.md` (this file).
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
- **Default Tag Details:** Confirm the default tag's name and ID in both backend and frontend.
- **Legacy Data:** Are there devices in the database without the default tag? If so, should a migration script be run?
- **Frontend TagSelector:** Confirm if the tag selector supports disabling/removing options, or if it needs to be extended.

---

## 4. Appendix
- **Backend:** `netraven/api/routers/devices.py`, `netraven/api/schemas/device.py`
- **Frontend:** `frontend/src/pages/Devices.vue`, `frontend/src/components/DeviceFormModal.vue`, `frontend/src/components/TagSelector.vue`, `frontend/src/store/device.js`
- **Testing:** Use Docker-based pytest command for backend; manual/automated tests for frontend.
- **Documentation:** `/docs/developer/device-default-tag-enforcement.md`, `/docs/development_log/<feature-branch>/` 