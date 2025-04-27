# Development Log: issue/15-dedup-device-creds

**Date:** $(date +'%Y-%m-%d %H:%M:%S')

**Developer:** Nova (AI Assistant)

**Branch:** issue/15-dedup-device-creds

**Goal:** Ensure no device can exist without credentials, deduplicate credentials in frontend defensively, and optimize API calls (GitHub issue #15).

---

## Initial Analysis
- Reviewed issue #15 and related backend work in issue #14 (which confirmed backend deduplication and credential enforcement).
- Confirmed backend blocks device creation/update if no credentials would be associated (via tags/default tag logic).
- Frontend did not enforce tag selection (and thus credential association) on device creation/edit.
- Frontend fetched device credentials on every popover hover, causing redundant API calls.
- UI could display a dash or 'No credentials' for a device, which should not be possible.

## Implementation Plan
1. Add frontend validation to require at least one tag (and thus credential) for device creation/edit.
2. Cache device credentials per device in the store to avoid redundant API calls.
3. Deduplicate credentials by ID in the frontend as a defensive measure.
4. Remove 'No credentials' UI; show an error if this state is somehow reached.
5. Document all changes and update tests as needed.

## Phase 1: Validation & Enforcement Review
- Backend: Confirmed strong enforcement of the invariant (no device without credentials).
- Frontend: Identified need for tag selection validation.

## Phase 2: UI/UX Improvements & Defensive Coding
- Device form now requires at least one tag before submission; validation error shown if not met.
- Device credentials are cached per device in the store; redundant API calls avoided.
- Credentials are deduplicated by ID in the frontend.
- UI no longer displays a dash or 'No credentials'; if this state is reached, an error is shown.

## Phase 3: Testing & Documentation
- To be completed: Add/verify tests for frontend validation and credential caching.
- This log will be updated with test results and any further changes.

## Phase 4: Seed Script Audit & Correction
- Audited scripts/seed_dev_data.py and found test-router was created with the 'test' tag but no credential for that tag.
- Added a credential (username: testuser, password: testpass) for the 'test' tag so test-router is always created with a credential, matching system rules.
- All seeded devices now have at least one credential associated via tags.

## Related Work
- See [issue #14 development log](../issue-14-dedup-device-creds/development_log.md) for backend deduplication details.

---

**Next Steps:**
- Complete and document frontend tests for validation and caching.
- Finalize and close issue #15 if all acceptance criteria are met. 