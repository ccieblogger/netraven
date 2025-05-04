# Phase 4 Developer Log: Device Table Data & Row Status (issue/99)

## Date Started: [AUTO-FILL]

### Initial Analysis
- Located `DeviceTable.vue` and confirmed it receives device data, loading state, and filter model as props.
- Device actions (edit, delete, check-reachability, credential-check, view-configs) are emitted to the parent (`Dashboard.vue`).
- `Dashboard.vue` wires up all device actions to backend via Pinia stores and API methods.
- Device data is loaded from the backend using `deviceStore.fetchDevices(params)` with pagination, sorting, and filters.
- All device actions (edit, delete, check reachability, credential check, view configs) are already implemented and call backend endpoints via the store.
- The device table supports loading, error, and empty states.

### Findings
- The device table is already wired to backend data and actions, but:
  - Pagination and total record count are not surfaced in the UI (only current page of devices is shown).
  - There is no explicit loading spinner for the table (relies on prop).
  - Status icons and action buttons are mapped to backend fields.
  - All device actions are handled in `Dashboard.vue` and call backend endpoints.
- The API client and store support all required device CRUD and job actions.

### Plan for Phase 4
1. **Paginated Device Data:**
   - Ensure the device table supports and displays pagination (total records, current page, page size).
   - Update the store and table to handle total record count from backend.
2. **Loading/Error/Empty States:**
   - Confirm loading and error states are displayed in the table.
   - Add or improve UI feedback if needed.
3. **Status Icons/Colors:**
   - Map device/job status fields to correct icons/colors in the table.
   - Ensure these reflect real backend state.
4. **Action Buttons:**
   - Confirm all action buttons (edit, delete, run job, view configs) are functional and call backend.
   - Add modals/confirmation dialogs as needed.
   - Display success/error feedback for all actions.
5. **Testing:**
   - Test all device table interactions with real backend data.
   - Document any issues or edge cases found.

---

## [Update: Step 1 Start]

### Additional Issues (from user):
1. Device DataTable not displaying any device when page is refreshed even though devices exist
2. Status icons do not appear or look incorrect.
3. Action icons also do not look correct.
4. Page size number not centered in paginator dropdown.

### Updated Plan
- A. Device Data Loading: Ensure device data is fetched on every page load/refresh. Debug Pinia store and API call for device list to ensure reliability.
- B. Status Icons: Review and fix the logic for mapping backend status to icons/colors. Ensure the ServiceDot (or equivalent) renders the correct status.
- C. Action Icons: Check icon imports and usage in the action column. Fix any rendering or slot issues so all action buttons display correct icons.
- D. Pagination Dropdown: Inspect paginator dropdown CSS. Fix centering of the page size number.
- E. Testing & Logging: Test all changes with real backend data. Update the developer log with findings, fixes, and any edge cases.

---

**Step 1: Device Data Loading on Refresh**
- Reviewing onMounted logic and Pinia store for device data fetch reliability.
- Will update log with findings and fixes before proceeding to next step.

**Next Steps:**
- Implement paginated device data and total record count in the table and store.
- Review and improve loading/error/empty states.
- Update this log as work progresses. 