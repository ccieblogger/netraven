# Developer Log: Unified Log Page Refactor (`/logs`)

**Feature Branch:** `issue/96-log-page-refactor`
**Issue:** [#96](https://github.com/ccieblogger/netraven/issues/96)

## Overview
This log documents the refactor of the `/logs` page to a unified, filterable, and sortable log viewer using PrimeVue DataTable, matching the Dashboard style and supporting deep-linking.

---

## Initial State
- The original `Logs.vue` used a custom table and only supported filtering by `job_id` and `device_id`.
- No support for log type, level, timestamp, source, or message filtering.
- No global search, column sorting, or full column set.
- No PrimeVue DataTable or Dashboard-style theming.

## Plan (Phase 2)
1. Refactor `Logs.vue` to use PrimeVue DataTable with all required columns and features.
2. Implement column filtering, sorting, pagination, and global search.
3. Add deep-linking and URL sync for filters/sort.
4. Add `/logs` to main navigation.
5. Document all work here and update the GitHub issue regularly.

## Progress

### [x] Step 1: PrimeVue DataTable Refactor
- Replaced custom table with PrimeVue DataTable in `Logs.vue`.
- Added columns: timestamp, log_type, level, job_id, device_id, source, message, meta.
- Enabled column filtering, sorting, pagination, and global search.
- Matched Dashboard style (header, row, spacing, color).
- Added loading and empty states.

**Next:**
- Implement deep-linking (route/query param sync).
- Add `/logs` to main navigation.
- Continue updating this log and the GitHub issue with progress and screenshots. 