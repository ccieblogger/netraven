# Phase 4: Job Type Registry & Extensible Log Views

## Overview
This document explains the extensible job type registry and log view system implemented for NetRaven UI (issue #47). It covers how to add new job types, result components, and log views for future extensibility.

---

## Job Type Registry (`frontend/src/jobTypeRegistry.js`)
- Centralizes job type metadata for the UI.
- Maps each `job_type` to:
  - `label`: Human-friendly name
  - `icon`: Icon name/component (for future use)
  - `resultComponent`: Name of the result display component
  - `logComponents`: Object mapping log types (e.g., `job`, `connection`) to component names

**Example:**
```js
export const jobTypeRegistry = {
  reachability: {
    label: 'Check Reachability',
    icon: 'NetworkCheckIcon',
    resultComponent: 'ReachabilityResults',
    logComponents: {
      job: 'JobLogTable',
      connection: 'ConnectionLogTable'
    }
  },
  backup: {
    label: 'Device Backup',
    icon: 'BackupIcon',
    resultComponent: 'BackupResults',
    logComponents: {
      job: 'JobLogTable'
    }
  }
}
```

---

## How to Add a New Job Type
1. **Create result and log components** (if needed):
   - Example: `BackupResults.vue`, `JobLogTable.vue`, etc.
2. **Register the new job type** in `jobTypeRegistry.js`:
   ```js
   backup: {
     label: 'Device Backup',
     icon: 'BackupIcon',
     resultComponent: 'BackupResults',
     logComponents: {
       job: 'JobLogTable'
     }
   }
   ```
3. **(Optional) Add icons and badges** for the new job type in the UI.
4. **No changes needed in JobMonitor.vue**—it will pick up the new type automatically.

---

## Log View Integration
- For each job type, you can specify which log views (job, connection, etc.) are available.
- The UI will show the correct log buttons and modals based on the registry.
- Log table components accept `jobId` and `deviceId` as props for filtering.

---

## Accessibility & UX
- All log action buttons have tooltips and accessible labels.
- Modals are keyboard accessible and closeable with ESC.
- Icons and colors are consistent and accessible.

---

## Example: Adding a Device Backup Job Type
1. Create `BackupResults.vue` for backup job results.
2. Register in the registry:
   ```js
   backup: {
     label: 'Device Backup',
     icon: 'BackupIcon',
     resultComponent: 'BackupResults',
     logComponents: {
       job: 'JobLogTable'
     }
   }
   ```
3. (Optional) Add a badge/icon for backup jobs in the UI.

---

## References
- `frontend/src/jobTypeRegistry.js`
- `frontend/src/components/JobMonitor.vue`
- `frontend/src/components/JobLogTable.vue`, `ConnectionLogTable.vue` 