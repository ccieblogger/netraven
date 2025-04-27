# Development Log: Issue #29 - Missing Add Tag Modal

## Phase 5: Minimal Patch for Update Tag API Call

**Date:** [auto-fill on commit]
**Branch:** issue/29-missing-add-tag-modal

### Summary
- Updated only the `updateTag` method in `frontend/src/store/tag.js` to use an absolute URL to the root path, bypassing the Axios interceptor and avoiding the `/api` prefix.
- This ensures the update tag call works with the backend's current routing, without affecting other API calls or UI elements.

### Rationale
- All backend routers are mounted at the root (no `/api` prefix), but the frontend Axios interceptor prepends `/api` to all requests.
- Most UI elements work due to proxy rewrites or because their endpoints are handled correctly.
- The update tag call failed because the proxy did not rewrite `/api/tags/{id}/` for PUT requests.
- Per project coding principles, only the broken call was changed to minimize risk and avoid introducing new patterns.

### Verification
- Tested updating a tag and confirmed the request now succeeds and the UI updates as expected.

---

**What and Why:**
- What: Patched only the update tag API call to use the correct backend path.
- Why: This resolves the update bug without impacting other working features.

---

*End of Phase 5 log entry.* 