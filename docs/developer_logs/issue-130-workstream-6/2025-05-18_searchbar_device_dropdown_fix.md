# Developer Log: Fix for Device Dropdown in ConfigSnapshots.vue (SearchBar.vue)

**Date:** 2025-05-18

## Summary
Resolved Vue warnings and fixed the device dropdown in `SearchBar.vue` so that devices are now displayed correctly by hostname, and the dropdown no longer throws warnings about `active` or `selected` properties. This also ensures the dropdown is populated when devices exist in the database.

## Details
- Updated the ListboxOption template to use the correct v-slot destructuring for `active` and `selected`.
- Changed device display to use `device.hostname` (with fallback to `device.name` for mock/dev data).
- Ensured `selectedDevice` is set by device id and updates reactively when the devices prop changes.
- Committed changes to feature branch `issue/130-workstream-6`.

## Testing
- Verified that the dropdown now displays all devices from the API.
- Confirmed that Vue warnings are no longer present in the console.
- Dropdown selection and search functionality work as expected.

---
