# Implementation Log: Device Must Always Have Default Tag

**Issue Reference:** [GitHub Issue #4](https://github.com/ccieblogger/netraven/issues/4)
**Status:** In Progress

---

## Summary
This log tracks the implementation of the plan to ensure all devices always have the default tag, both in backend and frontend, and to prevent users from removing the default tag in the UI.

---

## Implementation Plan (from Issue)

### Phase 1: Backend Enforcement of Default Tag
- Update `update_device` endpoint in `netraven/api/routers/devices.py` to always add the default tag if missing.
- If tag list is empty/missing, set to `[default_tag.id]`.
- Return clear error if default tag does not exist.
- Extend backend tests for all update scenarios.
- Consider migration for legacy devices missing the default tag.

### Phase 2: Frontend Tag Selector UX
- In `DeviceFormModal.vue`, always include default tag in selected tags and payload.
- In `TagSelector.vue`, visually lock and distinguish the default tag.
- Extend tag selector to support non-removable tags if needed.
- Manual testing to ensure default tag cannot be removed.

### Phase 3: Documentation and Dev Log
- Document process and rationale.
- Maintain this log with changes, decisions, and issues.

---

## Current Status
- Issue marked as **in progress** in GitHub.
- Awaiting branch creation and initial code changes.

---

## Next Steps
1. Create feature branch for backend and frontend changes.
2. Implement backend logic in `update_device` endpoint.
3. Update/add backend tests for tag enforcement.
4. Update frontend components to lock default tag.
5. Manual and automated testing.
6. Update this log with progress and decisions.

---

## Notes
- Confirm default tag's name/ID in DB and frontend.
- Consider migration for legacy data if needed.
- Reference this log and issue in all related PRs. 