# Issue: Tag Edit Modal Not Functional

**Location:** `/frontend/src/pages/Tags.vue`

---

## Summary

The "Edit" button for tags in the Tags management page currently triggers a placeholder alert/modal rather than a functional edit form. There is no `TagFormModal.vue` component implemented, and the modal logic in `Tags.vue` is commented out and incomplete. This prevents users from editing tag details via the UI.

---

## Root Cause

- The edit modal logic in `Tags.vue` is a placeholder (uses `alert()`).
- The intended `TagFormModal` component does not exist.
- Modal state management and integration with the tag store for editing are not implemented.

---

## Implementation Plan

### 1. Preparation

- **Branch:** Create a feature branch (e.g., `feature/tag-edit-modal`).
- **Development Log:** Start a log at `/docs/development_log/feature-tag-edit-modal/`.

---

### 2. Frontend Implementation

#### 2.1. Create `TagFormModal.vue`

- **Location:** `/frontend/src/components/TagFormModal.vue`
- **Functionality:**
  - Reusable modal for both creating and editing tags.
  - Use `BaseModal.vue` for consistent modal styling.
  - Accept props: `tag` (object or null), `isEditMode` (boolean), `isOpen` (boolean).
  - Emit events: `close`, `save`.
  - Form fields: `name` (required), `type` (optional).
  - Validation: Prevent empty name, show error if duplicate name (surface backend error).

#### 2.2. Integrate Modal in `Tags.vue`

- **Import and register** `TagFormModal`.
- **Replace** placeholder `alert()` logic in `openEditModal` and `openCreateModal` with modal state management.
- **Pass** the selected tag and mode (edit/create) to the modal.
- **Handle** `save` event: Call `tagStore.updateTag` or `tagStore.createTag` as appropriate.
- **Handle** `close` event: Reset modal state.

#### 2.3. User Feedback

- Show loading state and error messages in the modal.
- Show success notification on save (optional: use notification store).

---

### 3. Backend/API Review

- **Confirm** the `/tags/{tag_id}` `PUT` endpoint is functional (already present).
- **Test** with API client (e.g., Postman) if needed to verify update works as expected.

---

### 4. Testing

#### 4.1. Frontend

- **Manual Testing:**  
  - Edit a tag and verify changes persist and errors are handled.
  - Try to edit a tag to a duplicate name and confirm error is shown.
- **Automated Testing:**  
  - If frontend tests exist, add/extend tests for the modal and tag editing.

#### 4.2. Backend

- **Run backend tag tests:**  
  - Use:  
    ```
    docker exec -it netraven-api-dev bash -c "cd /app && PYTHONPATH=/app poetry run pytest tests/api/test_tags.py"
    ```
  - Ensure all tag update tests pass.

---

### 5. Documentation & Logging

- **Update** the development log with:
  - Steps taken
  - Decisions made
  - Any issues encountered and how they were resolved

---

### 6. Version Control

- **Commit** changes in logical increments.
- **Push** the feature branch to the repository.
- **Open a pull request** for review and integration.

---

## What & Why

- **What:** Implement a working tag edit modal in the frontend, using existing backend support.
- **Why:** Enables users to edit tags via the UI, improving usability and aligning with system requirements.

---

## References
- `frontend/src/pages/Tags.vue`
- `frontend/src/components/BaseModal.vue`
- `frontend/src/store/tag.js`
- `netraven/api/routers/tags.py`

---

**Prepared by:** Nova (AI Assistant)
**Date:** [Insert Date] 