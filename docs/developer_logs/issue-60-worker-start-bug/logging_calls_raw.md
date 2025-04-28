# Raw Logging Calls Export (2025)

This document lists all logger.log, save_log, log_runner_error, and print calls found in the NetRaven codebase as of 2025. Each entry includes the file, line number, and the full line of code. Grouped by function type for review.

---

## logger.log Calls

- [scheduler/job_definitions.py:18] logger.log(
- [scheduler/job_definitions.py:27] logger.log(
- [scheduler/job_definitions.py:36] logger.log(
- [scheduler/scheduler_runner.py:22] logger.log(
- [scheduler/scheduler_runner.py:33] logger.log(
- [scheduler/scheduler_runner.py:41] logger.log(
- [scheduler/scheduler_runner.py:51] logger.log(
- [scheduler/scheduler_runner.py:60] logger.log(
- [scheduler/scheduler_runner.py:67] logger.log(
- [scheduler/scheduler_runner.py:74] logger.log(
- [scheduler/job_registration.py:25] logger.log(
- [scheduler/job_registration.py:35] logger.log(
- [scheduler/job_registration.py:47] logger.log(
- [scheduler/job_registration.py:67] logger.log(
- [scheduler/job_registration.py:79] logger.log(
- [scheduler/job_registration.py:99] logger.log(
- [scheduler/job_registration.py:118] logger.log(
- [scheduler/job_registration.py:139] logger.log(
- [scheduler/job_registration.py:148] logger.log(
- [scheduler/job_registration.py:158] logger.log(
- [scheduler/job_registration.py:168] logger.log(
- [scheduler/job_registration.py:177] logger.log(
- [scheduler/job_registration.py:185] logger.log(
- [scheduler/job_registration.py:194] logger.log(
- [api/routers/auth_router.py:45] logger.log(
- [api/routers/auth_router.py:54] logger.log(
- [api/routers/auth_router.py:60] logger.log(
- [api/routers/auth_router.py:66] logger.log(
- [api/routers/auth_router.py:74] logger.log(
- [api/routers/auth_router.py:82] logger.log(
- [api/routers/auth_router.py:116] logger.log(
- [api/routers/auth_router.py:131] logger.log(
- [api/routers/auth_router.py:146] logger.log(
- [api/routers/devices.py:104] logger.log(
- [api/routers/devices.py:133] logger.log(
- [api/routers/devices.py:152] logger.log(
- [api/routers/devices.py:166] logger.log(
- [api/routers/devices.py:351] logger.log(
- [api/routers/devices.py:366] logger.log(
- [api/routers/devices.py:377] logger.log(
- [api/routers/devices.py:399] logger.log(
- [api/routers/devices.py:415] logger.log(
- [api/routers/jobs.py:296] logger.log(f"Failed to get Redis info: {e}", level="ERROR", destinations=["stdout"], source="jobs_router")
- [api/routers/jobs.py:319] logger.log(f"Failed to get RQ queue info: {e}", level="ERROR", destinations=["stdout"], source="jobs_router")
- [api/routers/jobs.py:332] logger.log(f"Failed to get worker info: {e}", level="ERROR", destinations=["stdout"], source="jobs_router")
- [utils/unified_logger.py:184] self.file_logger.log(level, msg)
- [utils/unified_logger.py:192] self.stdout_logger.log(level, msg, extra=extra)
- [db/init_data.py:31] logger.log(
- [db/init_data.py:72] logger.log(f"Standard DB session failed: {e}", level="WARNING", destinations=["stdout"], source="db_init_data")
- [db/init_data.py:73] logger.log("Trying to connect using localhost instead...", level="INFO", destinations=["stdout"], source="db_init_data")
- [db/init_data.py:91] logger.log(
- [db/init_data.py:112] logger.log(
- [db/init_data.py:129] logger.log(
- [db/init_data.py:146] logger.log(
- [db/init_data.py:168] logger.log(
- [db/init_data.py:196] logger.log(
- [db/init_data.py:205] logger.log(
- [db/init_data.py:223] logger.log(
- [db/init_data.py:239] logger.log(
- [db/init_data.py:250] logger.log(
- [db/init_data.py:258] logger.log(
- [db/init_data.py:265] logger.log(
- [db/init_data.py:278] logger.log(
- [db/init_data.py:289] logger.log(
- [db/init_data.py:299] logger.log(
- [db/init_data.py:311] logger.log(
- [db/init_data.py:318] logger.log(
- [db/init_data.py:331] logger.log(
- [db/init_data.py:341] logger.log(
- [db/init_data.py:360] logger.log(
- [db/init_data.py:374] logger.log("Connected to database using standard session", level="INFO", destinations=["stdout"], source="db_init_data")
- [db/init_data.py:376] logger.log(f"Standard DB session failed: {e}", level="WARNING", destinations=["stdout"], source="db_init_data")
- [db/init_data.py:377] logger.log("Trying to connect using localhost instead...", level="INFO", destinations=["stdout"], source="db_init_data")
- [db/init_data.py:379] logger.log("Connected to database using localhost", level="INFO", destinations=["stdout"], source="db_init_data")
- [db/init_data.py:399] logger.log("Database initialization completed successfully", level="INFO", destinations=["stdout"], source="db_init_data")
- [db/init_data.py:402] logger.log(f"Database initialization failed: {e}", level="ERROR", destinations=["stdout"], source="db_init_data")
- [worker/executor.py:85] logger.log(
- [worker/executor.py:132] logger.log(
- [worker/executor.py:141] logger.log(
- [worker/executor.py:158] logger.log(
- [worker/executor.py:167] logger.log(
- [worker/executor.py:177] logger.log(
- [worker/executor.py:209] logger.log(
- [worker/executor.py:218] logger.log(
- [worker/executor.py:226] logger.log(
- [worker/device_capabilities.py:315] logger.log(f"Unknown device type: {device_type}, using default commands", level="WARNING", destinations=["stdout"], source="device_capabilities")
- [worker/device_capabilities.py:346] logger.log(f"Unknown command type: {command_type} for device: {device_type}", level="WARNING", destinations=["stdout"], source="device_capabilities")
- [worker/device_capabilities.py:352] logger.log(f"No default found for command type: {command_type}", level="ERROR", destinations=["stdout"], source="device_capabilities")
- [worker/device_capabilities.py:391] logger.log(
- [worker/device_capabilities.py:432] logger.log(f"No capability patterns defined for {device_type}, using limited detection", level="WARNING", destinations=["stdout"], source="device_capabilities")
- [worker/device_capabilities.py:442] logger.log(f"[Job: {job_id}] Could not parse {capability} from output for {device_name}", level="WARNING", destinations=["stdout"], source="device_capabilities", job_id=job_id)
- [worker/device_capabilities.py:472] logger.log(f"No capability flags defined for {device_type}, using defaults", level="WARNING", destinations=["stdout"], source="device_capabilities")
- [worker/device_capabilities.py:693] logger.log(f"[Job: {job_id}] Detecting capabilities for {device_name} using '{version_cmd}'", level="INFO", destinations=["stdout"], source="device_capabilities", job_id=job_id)

## save_log Calls

- [utils/unified_logger.py:212] save_log(
- [db/log_utils.py:5] def save_log(

## log_runner_error Calls

- [worker/runner.py:386] log_runner_error(job_id, error_msg_for_log, db_to_use, error_type="CREDENTIAL")
- [worker/runner.py:403] log_runner_error(job_id, error_msg, db_to_use)

## print Calls

- [api/auth.py:19] print(f"[DEBUG] JWT SECRET_KEY: {SECRET_KEY} | ALGORITHM: {ALGORITHM}")
- [api/routers/auth_router.py:113] print(f"DEBUG: /auth/token called with username={form_data.username}")
- [api/routers/auth_router.py:154] print(f"ERROR in /auth/token: {e}")
- [api/routers/jobs.py:477] print("Successfully connected to Redis for RQ.")
- [api/routers/jobs.py:479] print(f"ERROR: Could not connect to Redis at {redis_url} for RQ. Job trigger endpoint will fail.")
- [api/routers/jobs.py:480] print(f"Error details: {e}")
- [db/log_utils.py:31] print(f"[LOGGER EXCEPTION] {e}")
- [db/session.py:12] print(f"[DB SESSION] Database session configured: {db_url}")
- [config/loader.py:64] print(f"Environment not specified, using NETRAVEN_ENV or default: {env}")
- [config/loader.py:80] print(f"Loaded base configuration from {base_config_path}")
- [config/loader.py:82] print(f"Failed to load base config {base_config_path}: {e}")
- [config/loader.py:91] print(f"Loaded environment configuration from {env_config_path}")
- [config/loader.py:93] print(f"Failed to load environment config {env_config_path}: {e}")
- [config/loader.py:95] print(f"Environment config file not found: {env_config_path}")
- [config/loader.py:101] print(f"Applied environment variable overrides: {env_overrides}")
- [config/loader.py:104] print("Configuration result is empty. Check config files and environment.")
- [config/loader.py:115] print("Loaded Configuration:")
- [config/loader.py:117] print(json.dumps(loaded_config, indent=2))
- [worker/git_writer.py:44] print(f"Repo path {repo_path} does not exist. Creating...")
- [worker/git_writer.py:46] print(f"Initializing Git repository at {repo_path}...")
- [worker/git_writer.py:48] print("Repository initialized.")
- [worker/git_writer.py:53] print(f"Error opening existing repository at {repo_path}: {e}. Attempting to initialize.")
- [worker/git_writer.py:61] print(f"Writing configuration for device {device_id} to {config_file_path}")
- [worker/git_writer.py:70] print(f"Staging file: {config_file_name}")
- [worker/git_writer.py:75] print(f"Committing with message: '{commit_message}'")
- [worker/git_writer.py:79] print(f"Commit successful. Hash: {commit.hexsha}")
- [worker/git_writer.py:84] print(f"Git command error occurred: {git_err}")
- [worker/git_writer.py:88] print(f"An unexpected error occurred during Git operation: {e}")
- [worker/device_capabilities.py:672] >>> print(f"Device model: {capabilities['model']}, version: {capabilities['version']}")
- [worker/redactor.py:56] print(f"Using redaction keywords from config: {keywords}")
- [worker/redactor.py:58] print("Config provided empty redaction keywords list, using defaults.")
- [worker/redactor.py:60] print(f"Using default redaction keywords: {keywords}")
- [worker/dispatcher.py:147] print(f"[DEBUG dispatcher] Submitting device_id={device_id} device_name={device_name} job_id={job_id}")
- [worker/dispatcher.py:310] print(f"[DEBUG dispatcher] task_with_retry ENTRY: device_id={device_id} device_name={device_name} job_id={job_id}")
- [worker/dispatcher.py:319] print(f"[DEBUG dispatcher] task_with_retry SUCCESS: device_id={device_id} device_name={device_name} job_id={job_id} retries=0")
- [worker/dispatcher.py:329] print(f"[DEBUG dispatcher] task_with_retry: All credentials exhausted for device_id={device_id} device_name={device_name} job_id={job_id}. Not retrying.")
- [worker/dispatcher.py:373] print(f"[DEBUG dispatcher] Scheduling retry for device_id={device_id} device_name={device_name} job_id={job_id} attempt={retry_count}/{max_retries} in {backoff_time}s")
- [worker/backends/netmiko_driver.py:90] print(f"[DEBUG netmiko_driver] REAL run_command CALLED: device={getattr(device, 'hostname', None)}, username={getattr(device, 'username', None)}, job_id={job_id}") 