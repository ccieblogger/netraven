# Feature 110: Required Job Results Enforcement

## Summary

This feature enforces that every job module in NetRaven must return a result dict from its `run()` function, and that result must include at least the following fields:
- `success` (bool): Indicates if the job succeeded for the device.
- `device_id` (int): The device's unique identifier.

If a job module does not comply:
- It will not be registered by the dynamic job loader (see `netraven/worker/job_registry.py`).
- If a job's `run()` returns `None` or an invalid result at runtime, the dispatcher will generate a failure result and log an error (see `netraven/worker/dispatcher.py`).

## Implementation Details
- **Job Registry Contract Enforcement:**
  - The loader calls each job's `run()` with dummy arguments and checks for the required fields.
  - Non-compliant modules are skipped and logged.
- **Dispatcher Hardening:**
  - At runtime, if a job returns an invalid result, a failure result is generated and written to the `job_results` table.

## Example Job Module Template

```python
def run(device, job_id, config, db):
    # ... job logic ...
    return {
        "success": True,  # or False
        "device_id": device.id,
        # ... other fields ...
    }
```

## Developer Notes
- Always ensure your job's `run()` returns a dict with at least `success` and `device_id`.
- See enforcement logic in:
  - `netraven/worker/job_registry.py`
  - `netraven/worker/dispatcher.py`

## Standardizing Job Result Details

All job modules should return a dict with at least 'success' (bool), 'device_id' (int), and (if needed) a 'details' key containing all extra/ad-hoc/structured data. This ensures that all extra information is stored in the 'details' JSONB column in the database and is available for the UI.

### Example Job Module Return

```python
return {
    "success": True,
    "device_id": device_id,
    "details": {
        "commit_hash": commit_hash,  # For config backups
        "meta": {
            "lines_saved": 123,
            "config_size": 4096
        }
    }
}
```

- The dispatcher will store all keys not mapped to top-level columns inside the 'details' JSONB field.
- For ad-hoc or structured data, always use the 'details' key. 