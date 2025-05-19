# Dev Log: Config Diff Page Sidebar & Navigation Refactor (May 18, 2025)

## Summary
- Migrated Config Diff from a top-level sidebar entry to a sub-page under Backups.
- Updated all navigation, routes, and sidebar config to reflect this change.
- Removed modal-based diff logic from ConfigSnapshots.
- Added a test for DiffViewer accessibility and ARIA compliance.

## Key Changes
- `navConfig.js`: Removed top-level Config Diff, added as child under Backups.
- `DefaultLayout.vue`: Removed Config Diff from navigation array.
- `router/index.js`: Config Diff is now a child route of `/backups`.
- `SnapshotsTable.vue`: Diff action links to `/backups/diff` with correct params.
- `ConfigSnapshots.vue`: Removed modal diff logic.
- `ConfigDiff.vue`: Supports both manual and param-based selection.
- `DiffViewer.test.js`: Added accessibility and ARIA tests for diff viewer.

## Manual QA
- Sidebar now only shows Config Diff under Backups.
- All navigation paths (sidebar, direct URL, Snapshots table) work as expected.
- Diff page always shows selection UI, never blank.

## Update (May 18, 2025)
- Changed sidebar navigation text from 'Diff' to 'Diff Viewer' under Backups for clarity and consistency.
- All navigation and routing remain unchanged; only the display name is updated.

## Next Steps
- Further UI/UX polish or test automation if required.
- Await user feedback for additional improvements.

---
