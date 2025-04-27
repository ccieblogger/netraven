# Development Log: Logging Audit & Refactor (Issue #64)

## Progress Update ([date])

### Completed
- Reformatted the logging audit table to include:
  - Line numbers for each log entry
  - Separate columns for Log Type, Category, Log Level, Message Content, Metadata, Current Destinations, Desired Destinations, and Notes
  - Initial mapping for the Category column (job_log, connection_log, system_log)
- Added a **Metadata** column specifying required contextual fields (e.g., job_id, device_id, user) for each log entry
- Updated all job_log and connection_log entries:
  - Message Content is user-friendly and only references names (job name, device name, etc.), not IDs
  - Metadata contains only IDs (job_id, device_id, etc.), not names
  - Improved clarity and readability of log messages
- All job_log entries now have `db` as a Desired Destination
- All connection_log entries for life cycle events (connect, authenticate, run command, disconnect, commit/save) now have `db` as a Desired Destination
- Added a placeholder for Netmiko session logs (debug/session events) with Desired Destination `redis channel` (not yet implemented)
- **All log entries now explicitly list `stdout` in Desired Destinations** for clarity, regardless of Current Destinations
- System_log entries checked to ensure `stdout` is present in Desired Destinations
- Added summary/implementation notes to the audit log for future reference

### Additions/Enhancements
- Policy: All log entries must always include `stdout` in Desired Destinations for clarity
- Policy: Metadata column must specify only IDs, not names, for UI lookup
- Policy: Message Content must be user-friendly and reference only names

### Outstanding/To Do
- Audit the codebase for missing connection_log calls for all device life cycle events and add as needed
- Implement routing of all job_log and connection_log (life cycle) logs to the DB
- Implement Netmiko session log streaming to Redis channel for real-time UI (requires new handler or Netmiko integration)
- Update logging configuration and documentation accordingly
- (Ongoing) Review and refine log message clarity as new log calls are added

---

**The audit log and developer documentation have been updated to reflect all of the above.** 