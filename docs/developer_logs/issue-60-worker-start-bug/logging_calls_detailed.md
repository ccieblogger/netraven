# Detailed Logging Calls Audit (2025)

This document contains full, context-rich logger.log, print, save_log, and log_runner_error statements from the NetRaven codebase. Each entry includes the file, function/context, and the full statement (multi-line if needed).

---

## netraven/db/init_data.py

**Function:** create_admin_user
```python
logger.log(
    f"Admin user '{DEFAULT_ADMIN['username']}' already exists with ID: {existing_admin.id}",
    level="INFO",
    destinations=["stdout"],
    source="db_init_data",
)
logger.log(
    f"Admin user '{DEFAULT_ADMIN['username']}' created with ID: {new_admin.id}",
    level="INFO",
    destinations=["stdout"],
    source="db_init_data",
)
```

**Function:** create_default_tags
```python
logger.log(
    f"Tag '{tag_data['name']}' already exists with ID: {existing_tag.id}",
    level="INFO",
    destinations=["stdout"],
    source="db_init_data",
)
logger.log(
    f"Tag '{tag_data['name']}' created with ID: {new_tag.id}",
    level="INFO",
    destinations=["stdout"],
    source="db_init_data",
)
```

**Function:** create_default_credentials
```python
logger.log(
    f"Credential with username '{cred_data['username']}' already exists with ID: {result[0]}",
    level="INFO",
    destinations=["stdout"],
    source="db_init_data",
)
logger.log(
    f"System credential '{cred_data['username']}' created with ID: {new_cred.id}",
    level="INFO",
    destinations=["stdout"],
    source="db_init_data",
)
logger.log(
    f"Error creating credential: {e}",
    level="ERROR",
    destinations=["stdout"],
    source="db_init_data",
)
```

**Function:** associate_default_tag_with_devices
```python
logger.log(
    "Default tag not found, cannot associate with devices",
    level="WARNING",
    destinations=["stdout"],
    source="db_init_data",
)
# ... and similar for association and errors
```

**ImportError handler (module-level):**
```python
logger.log(
    f"Failed to import required modules: {e}",
    level="ERROR",
    destinations=["stdout"],
    source="db_init_data",
)
```

---

## netraven/worker/executor.py

**Function:** reachability_handler
```python
logger.log(
    f"Entered reachability_handler for job_id={job_id}, device_id={getattr(device, 'id', None)}",
    level="INFO",
    destinations=["stdout", "db"],
    job_id=job_id,
    device_id=getattr(device, 'id', None),
    source="executor",
)
# ... and similar for success/failure logs
```

**Function:** handle_device
```python
logger.log(
    f"handle_device called for job_id={job_id}, resolved job_type={job_type}",
    level="INFO",
    destinations=["stdout", "db"],
    job_id=job_id,
    source="executor",
)
# ... and similar for handler dispatch and errors
```

---

## netraven/api/routers/auth_router.py

**Function:** authenticate_user
```python
logger.log(
    f"Authentication failed: User not found: {username}",
    level="WARNING",
    destinations=["stdout"],
    source="auth_router",
)
# ... and similar for password verification, success, etc.
```

**Function:** login_for_access_token
```python
logger.log(
    f"Login attempt for user: {form_data.username}",
    level="INFO",
    destinations=["stdout"],
    source="auth_router",
)
# ... and similar for token generation, inactive user, etc.
```
**Prints:**
```python
print(f"DEBUG: /auth/token called with username={form_data.username}")
print(f"ERROR in /auth/token: {e}")
```

---

## netraven/scheduler/job_definitions.py

**Function:** run_device_job
```python
logger.log(
    "Executing scheduled job via worker",
    level="INFO",
    destinations=["stdout"],
    job_id=job_id,
    source="job_definitions"
)
# ... and similar for job completion and error
```

---

## netraven/worker/device_capabilities.py

**Function:** get_device_commands
```python
logger.log(f"Unknown device type: {device_type}, using default commands", level="WARNING", destinations=["stdout"], source="device_capabilities")
```

**Function:** get_command
```python
logger.log(f"Unknown command type: {command_type} for device: {device_type}", level="WARNING", destinations=["stdout"], source="device_capabilities")
logger.log(f"No default found for command type: {command_type}", level="ERROR", destinations=["stdout"], source="device_capabilities")
```

**Function:** get_command_timeout
```python
logger.log(
    f"No timeout defined for {device_type}/{command_type}, "
    f"using default: {default_timeout}s",
    level="WARNING", destinations=["stdout"], source="device_capabilities"
)
```

**Function:** parse_device_capabilities
```python
logger.log(f"No capability patterns defined for {device_type}, using limited detection", level="WARNING", destinations=["stdout"], source="device_capabilities")
logger.log(f"[Job: {job_id}] Could not parse {capability} from output for {device_name}", level="WARNING", destinations=["stdout"], source="device_capabilities", job_id=job_id)
```

**Function:** get_static_capabilities
```python
logger.log(f"No capability flags defined for {device_type}, using defaults", level="WARNING", destinations=["stdout"], source="device_capabilities")
```

---

## netraven/worker/dispatcher.py

**Function:** dispatch_tasks
```python
print(f"[DEBUG dispatcher] Submitting device_id={device_id} device_name={device_name} job_id={job_id}")
logger.log(
    f"Submitting task for device '{device_name}' in job '{job_id}'",
    level="INFO",
    destinations=["stdout", "db"],
    job_id=job_id,
    device_id=device_id,
    source="dispatcher",
)
# ... and similar for task completion, errors, and summary
```

**Function:** task_with_retry
```python
print(f"[DEBUG dispatcher] task_with_retry ENTRY: device_id={device_id} device_name={device_name} job_id={job_id}")
print(f"[DEBUG dispatcher] task_with_retry SUCCESS: device_id={device_id} device_name={device_name} job_id={job_id} retries=0")
print(f"[DEBUG dispatcher] task_with_retry: All credentials exhausted for device_id={device_id} device_name={device_name} job_id={job_id}. Not retrying.")
print(f"[DEBUG dispatcher] Scheduling retry for device_id={device_id} device_name={device_name} job_id={job_id} attempt={retry_count}/{max_retries} in {backoff_time}s")
logger.log(
    f"Retrying device '{device_name}' in {backoff_time}s (attempt {retry_count}/{max_retries})",
    level="INFO",
    destinations=["stdout", "db"],
    job_id=job_id,
    device_id=device_id,
    source="dispatcher",
)
```

---

## netraven/db/log_utils.py

**Function:** save_log
```python
try:
    entry = Log(
        message=message,
        log_type=log_type,
        level=level,
        job_id=job_id,
        device_id=device_id,
        source=source,
        meta=meta
    )
    db.add(entry)
    db.commit()
except Exception as e:
    print(f"[LOGGER EXCEPTION] {e}")
    db.rollback()
    raise
finally:
    db.close()
```

---

## netraven/worker/runner.py

**Function:** run_job
```python
logger.log(
    "Job started.",
    level="INFO",
    destinations=["stdout", "db"],
    job_id=job_id,
    source="runner",
    log_type="job"
)
# ... and similar for configuration, device loading, credential resolution, dispatcher, and final status
log_runner_error(job_id, error_msg_for_log, db_to_use, error_type="CREDENTIAL")
log_runner_error(job_id, error_msg, db_to_use)
```

---

## netraven/api/routers/jobs.py

**Function:** get_jobs_status
```python
logger.log(f"Failed to get Redis info: {e}", level="ERROR", destinations=["stdout"], source="jobs_router")
logger.log(f"Failed to get RQ queue info: {e}", level="ERROR", destinations=["stdout"], source="jobs_router")
logger.log(f"Failed to get worker info: {e}", level="ERROR", destinations=["stdout"], source="jobs_router")
```
**Prints:**
```python
print("Successfully connected to Redis for RQ.")
print(f"ERROR: Could not connect to Redis at {redis_url} for RQ. Job trigger endpoint will fail.")
print(f"Error details: {e}")
```

---

## netraven/worker/git_writer.py

**Function:** commit_configuration_to_git
```python
print(f"Repo path {repo_path} does not exist. Creating...")
print(f"Initializing Git repository at {repo_path}...")
print("Repository initialized.")
print(f"Error opening existing repository at {repo_path}: {e}. Attempting to initialize.")
print(f"Writing configuration for device {device_id} to {config_file_path}")
print(f"Staging file: {config_file_name}")
print(f"Committing with message: '{commit_message}'")
print(f"Commit successful. Hash: {commit.hexsha}")
print(f"Git command error occurred: {git_err}")
print(f"An unexpected error occurred during Git operation: {e}")
```

---

## netraven/config/loader.py

**Function:** load_config
```python
print(f"Environment not specified, using NETRAVEN_ENV or default: {env}")
print(f"Loaded base configuration from {base_config_path}")
print(f"Failed to load base config {base_config_path}: {e}")
print(f"Loaded environment configuration from {env_config_path}")
print(f"Failed to load environment config {env_config_path}: {e}")
print(f"Environment config file not found: {env_config_path}")
print(f"Applied environment variable overrides: {env_overrides}")
print("Configuration result is empty. Check config files and environment.")
print("Loaded Configuration:")
print(json.dumps(loaded_config, indent=2))
```

---

## netraven/services/credential_metrics.py

**Function:** record_credential_attempt
```python
print(f"[DEBUG REAL] record_credential_attempt called: pid={os.getpid()} thread={threading.current_thread().name} device_id={device_id} credential_id={credential_id} job_id={job_id} success={success} error={error}")
```

---

## netraven/worker/redactor.py

**Function:** redact
```python
print(f"Using redaction keywords from config: {keywords}")
print("Config provided empty redaction keywords list, using defaults.")
print(f"Using default redaction keywords: {keywords}")
```

---

## netraven/worker/backends/netmiko_driver.py

**Function:** run_command
```python
print(f"[DEBUG netmiko_driver] REAL run_command CALLED: device={getattr(device, 'hostname', None)}, username={getattr(device, 'username', None)}, job_id={job_id}")
# ... and similar for test/demo code
``` 