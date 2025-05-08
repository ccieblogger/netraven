# NetRaven Dynamic Job Registry & Loader Specification

## Executive Summary

This document specifies the design and implementation plan for a dynamic, plug-and-play job registry and loader system for NetRaven. The goal is to allow new job types to be added simply by dropping a new Python module into the `netraven/worker/jobs/` directory, with no backend code changes required. The system will auto-discover, validate, and register job modules, exposing their metadata and logic to the worker, API, and UI.

---

## 1. Motivation & Goals

- **Zero-code-change extensibility:** Add new job types without modifying static registries or backend code.
- **Modular, maintainable, and DRY:** Each job is a self-contained module with its own metadata and logic.
- **Dynamic discovery:** The system auto-discovers job modules at startup.
- **Consistent metadata:** All job types expose a standard metadata structure for use in the API/UI.
- **Alignment with NetRaven principles:** Simple, extensible, and easy to test and maintain.

---

## 2. Folder & File Structure

```
netraven/
  worker/
    jobs/
      __init__.py
      config_backup.py
      reachability.py
      # ...future job modules
    job_registry.py   # <-- new dynamic loader/registry
    # ...other worker files
```

---

## 3. Job Module Interface

Each job module in `netraven/worker/jobs/` must provide:

- `JOB_META` (dict):
  - Required: `job_type` (string, unique)
  - Optional: `label`, `description`, `icon`, `default_schedule`, etc.
- `run(device, job_id, config, db)` (function):
  - The main job logic, same signature as current handlers.

**Example:**
```python
# netraven/worker/jobs/config_backup.py

JOB_META = {
    "job_type": "backup",
    "label": "Configuration Backup",
    "description": "Backs up device running-config and stores in Git.",
    "icon": "mdi-content-save",
    "default_schedule": "daily"
}

def run(device, job_id, config, db):
    # ...job logic...
    return {"success": True, ...}
```

---

## 4. Dynamic Loader & Registry Design

### Loader Logic (`job_registry.py`)

- On import, scan the `jobs/` folder for all `.py` files (excluding `__init__.py`).
- Import each module.
- Validate:
  - `JOB_META` exists and contains a unique `job_type`.
  - `run()` function exists.
- Build:
  - `JOB_TYPE_REGISTRY`: `{job_type: run_function}`
  - `JOB_TYPE_META`: `{job_type: JOB_META}`

**Pseudocode:**
```python
import importlib
import pkgutil
import os

JOBS_PATH = os.path.dirname(__file__) + "/jobs"

JOB_TYPE_REGISTRY = {}
JOB_TYPE_META = {}

for _, module_name, _ in pkgutil.iter_modules([JOBS_PATH]):
    if module_name == "__init__":
        continue
    module = importlib.import_module(f"netraven.worker.jobs.{module_name}")
    meta = getattr(module, "JOB_META", None)
    run_func = getattr(module, "run", None)
    if not meta or "job_type" not in meta or not callable(run_func):
        # Log warning and skip
        continue
    job_type = meta["job_type"]
    if job_type in JOB_TYPE_REGISTRY:
        # Log error: duplicate job_type
        continue
    JOB_TYPE_REGISTRY[job_type] = run_func
    JOB_TYPE_META[job_type] = meta
```

---

## 5. Usage in Worker & API

- In `executor.py` (or wherever job dispatch happens), import the registry:
  ```python
  from netraven.worker.job_registry import JOB_TYPE_REGISTRY
  ```
- To dispatch:
  ```python
  handler = JOB_TYPE_REGISTRY.get(job_type)
  if not handler:
      # Handle unknown job_type
      ...
  result = handler(device, job_id, config, db)
  ```
- Expose `JOB_TYPE_META` via an API endpoint for the UI to list available job types and their metadata.

---

## 6. Validation & Error Handling

- On startup, log and skip any job module that:
  - Lacks `JOB_META` or `run()`
  - Has a duplicate `job_type`
- Optionally, fail fast if there are critical errors (e.g., no valid job types found).

---

## 7. Testing & Extensibility

- Add tests to ensure:
  - All job modules are loaded and registered correctly.
  - Duplicate or invalid modules are handled gracefully.
- To add a new job type:
  1. Drop a new `.py` file in `jobs/` with the required interface.
  2. Restart the worker/API service.

---

## 8. Documentation

- Document the required job module interface and metadata in the developer docs.
- Provide a template for new job modules.

---

## 9. Developer Logging

- Log all registry loading actions, warnings, and errors to a dedicated developer log file and/or the unified logging system.

---

## 10. Standardized Job Logging for Jobs

To ensure all job execution logs are consistent, easily filterable, and maintainable, all job modules must use a standardized logging utility called `JobLogger`. This logger leverages the unified logging system, but enforces a consistent structure for job logs:

- `log_type='job'` for all job-related logs
- A `source` field following the convention: `worker.job.{job_type}` (where `job_type` is from the job module's `JOB_META`)
- Required metadata fields such as `job_id` and (optionally) `device_id`
- Optional additional metadata via the `meta` field

### JobLogger Utility

The `JobLogger` class is provided in the worker package. It wraps the unified logging system, automatically setting `log_type='job'` and the appropriate `source` value. It enforces the presence of `job_id` and `job_type` in all job logs.

**Example Implementation:**
```python
# netraven/worker/logging.py
class JobLogger:
    def __init__(self, job_id, job_type, device_id=None):
        self.job_id = job_id
        self.device_id = device_id
        self.source = f"worker.job.{job_type}"

    def log(self, level, message, meta=None):
        log_entry = {
            "log_type": "job",
            "level": level,
            "job_id": self.job_id,
            "device_id": self.device_id,
            "source": self.source,
            "message": message,
            "meta": meta or {},
        }
        unified_log(log_entry)  # Calls the existing unified logging system
```

### Usage in Job Modules

All job modules must use the `JobLogger` for all log output. This ensures logs are consistent and easily filterable by `log_type` and `source`.

**Example Usage:**
```python
from netraven.worker.logging import JobLogger

def run(device, job_id, config, db):
    logger = JobLogger(job_id=job_id, job_type=JOB_META["job_type"], device_id=device.id)
    logger.log("info", "Job started")
    # ...job logic...
    logger.log("info", "Job completed")
```

### Rationale
- **Simplicity:** No new tables or APIs; just a utility and a naming convention.
- **Consistency:** All job logs are easily filterable by `log_type` and `source`.
- **Maintainability:** Centralizes job logging logic for easy updates and enforcement.
- **Extensibility:** New job types automatically follow the pattern.

---

## 11. Example Job Module Template

```python
# netraven/worker/jobs/example_job.py

from netraven.worker.logging import JobLogger

JOB_META = {
    "job_type": "example",
    "label": "Example Job",
    "description": "This is an example job type.",
    "icon": "mdi-star",
    "default_schedule": "onetime"
}

def run(device, job_id, config, db):
    logger = JobLogger(job_id=job_id, job_type=JOB_META["job_type"], device_id=device.id)
    logger.log("info", "Example job started")
    # Implement job logic here
    logger.log("info", "Example job completed")
    return {"success": True, "details": "Example job completed."}
```

---

## 12. References
- [Plugin/Registry Patterns in Python](https://realpython.com/python-import/#importing-modules-programmatically)
- [NetRaven Architecture Statement of Truth](architecture_sot.md)
- [Job Lifecycle Spec](job_lifecycle_spec.md)

---

*For questions or to propose changes, please open a GitHub issue or enhancement request.* 