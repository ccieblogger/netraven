# NetRaven Logging and Print Calls Table (2025)

| # | File & Line | Log Type | Category | Log Level | Message Content | Metadata | Current Destinations | Desired Destinations | Actually in DB? | Safe for DB/File? | Notes |
|---|-------------|----------|----------|-----------|-----------------|----------|----------------------|----------------------|-----------------|-------------------|-------|
| 1 | db/init_data.py:31 | logger.log | system_log | ERROR | Failed to import required modules: {e} | e | stdout | stdout |  | No | ImportError handler: occurs before DB init |
| 2 | db/init_data.py:91 | logger.log | system_log | INFO | Admin user '{DEFAULT_ADMIN['username']}' already exists with ID: {existing_admin.id} | existing_admin.id | stdout | stdout |  | Yes |  |
| 3 | db/init_data.py:112 | logger.log | system_log | INFO | Admin user '{DEFAULT_ADMIN['username']}' created with ID: {new_admin.id} | new_admin.id | stdout | stdout |  | Yes |  |
| 4 | db/init_data.py:129 | logger.log | system_log | INFO | Tag '{tag_data['name']}' already exists with ID: {existing_tag.id} | tag_data['name'], existing_tag.id | stdout | stdout |  | Yes |  |
| 5 | db/init_data.py:146 | logger.log | system_log | INFO | Tag '{tag_data['name']}' created with ID: {new_tag.id} | tag_data['name'], new_tag.id | stdout | stdout |  | Yes |  |
| 6 | db/init_data.py:168 | logger.log | system_log | INFO | Credential with username '{cred_data['username']}' already exists with ID: {result[0]} | cred_data['username'], result[0] | stdout | stdout |  | Yes |  |
| 7 | db/init_data.py:196 | logger.log | system_log | INFO | System credential '{cred_data['username']}' created with ID: {new_cred.id} | cred_data['username'], new_cred.id | stdout | stdout |  | Yes |  |
| 8 | db/init_data.py:205 | logger.log | system_log | ERROR | Error creating credential: {e} | e | stdout | stdout |  | Yes |  |
| 9 | db/init_data.py:223 | logger.log | system_log | WARNING | Default tag not found, cannot associate with devices |  | stdout | stdout |  | Yes |  |
| 10 | db/init_data.py:239 | logger.log | system_log | INFO | All existing devices already have the default tag |  | stdout | stdout |  | Yes |  |
| 11 | db/init_data.py:250 | logger.log | system_log | INFO | Associated default tag with device: {device.hostname} | device.hostname | stdout | stdout |  | Yes |  |
| 12 | db/init_data.py:258 | logger.log | system_log | INFO | Default tag associated with {len(devices_without_tag)} device(s) | len(devices_without_tag) | stdout | stdout |  | Yes |  |
| 13 | db/init_data.py:265 | logger.log | system_log | ERROR | Error associating default tag with devices: {e} | e | stdout | stdout |  | Yes |  |
| 14 | db/init_data.py:278 | logger.log | system_log | WARNING | Default tag not found, cannot associate with credential |  | stdout | stdout |  | Yes |  |
| 15 | db/init_data.py:289 | logger.log | system_log | WARNING | Default credential not found, cannot associate with tag |  | stdout | stdout |  | Yes |  |
| 16 | db/init_data.py:299 | logger.log | system_log | INFO | Default credential is already associated with default tag |  | stdout | stdout |  | Yes |  |
| 17 | db/init_data.py:311 | logger.log | system_log | INFO | Successfully associated default credential (ID: {default_cred.id}) with default tag (ID: {default_tag.id}) | default_cred.id, default_tag.id | stdout | stdout |  | Yes |  |
| 18 | db/init_data.py:318 | logger.log | system_log | ERROR | Error associating default credential with default tag: {e} | e | stdout | stdout |  | Yes |  |
| 19 | db/init_data.py:331 | logger.log | system_log | INFO | System reachability job already exists with ID: {job.id} | job.id | stdout | stdout |  | Yes |  |
| 20 | db/init_data.py:341 | logger.log | system_log | WARNING | Default tag not found, cannot create system reachability job |  | stdout | stdout |  | Yes |  |
| 21 | db/init_data.py:360 | logger.log | system_log | INFO | System reachability job created with ID: {job.id} | job.id | stdout | stdout |  | Yes |  |
| 22 | scheduler/job_definitions.py:18 | logger.log | job_log | INFO | Executing scheduled job via worker | job_id | stdout | stdout |  | Yes | run_device_job |
| 23 | scheduler/job_definitions.py:27 | logger.log | job_log | INFO | Worker job execution finished | job_id | stdout | stdout |  | Yes | run_device_job |
| 24 | scheduler/job_definitions.py:36 | logger.log | job_log | ERROR | Worker job execution failed: {e} | job_id, e | stdout | stdout |  | Yes | run_device_job |
| 25 | scheduler/scheduler_runner.py:22 | logger.log | system_log | INFO | Starting NetRaven Scheduler | redis_url, poll_interval | stdout | stdout |  | Maybe | __main__: May run before DB is ready, but usually after config load |
| 26 | scheduler/scheduler_runner.py:33 | logger.log | system_log | INFO | Successfully connected to Redis. |  | stdout | stdout |  | Yes | __main__ |
| 27 | scheduler/scheduler_runner.py:41 | logger.log | system_log | ERROR | Failed to connect to Redis or initialize scheduler: {e} | e, redis_url | stdout | stdout |  | Maybe | __main__: If Redis/DB not up, may not be safe |
| 28 | scheduler/scheduler_runner.py:51 | logger.log | system_log | INFO | Scheduler polling for jobs... |  | stdout | stdout |  | Yes | __main__ |
| 29 | scheduler/scheduler_runner.py:60 | logger.log | system_log | DEBUG | Job sync process completed. |  | stdout | stdout |  | Yes | __main__ |
| 30 | scheduler/scheduler_runner.py:67 | logger.log | system_log | ERROR | Error during job synchronization: {e} | e | stdout | stdout |  | Yes | __main__ |
| 31 | scheduler/scheduler_runner.py:74 | logger.log | system_log | DEBUG | Scheduler sleeping for {polling_interval} seconds. | polling_interval | stdout | stdout |  | Yes | __main__ |
| 32 | scheduler/job_registration.py:25 | logger.log | system_log | DEBUG | Starting job synchronization from database... |  | stdout | stdout |  | Yes |  |
| 33 | scheduler/job_registration.py:35 | logger.log | system_log | INFO | Found {len(jobs_to_schedule)} enabled jobs in DB. | len(jobs_to_schedule) | stdout | stdout |  | Yes |  |
| 34 | scheduler/job_registration.py:47 | logger.log | system_log | DEBUG | {len(existing_rq_job_ids)} jobs currently in RQ-Scheduler. | len(existing_rq_job_ids) | stdout | stdout |  | Yes |  |
| 35 | scheduler/job_registration.py:67 | logger.log | system_log | DEBUG | Job already scheduled in RQ-Scheduler, skipping. {job_log_details} | job_log_details | stdout | stdout |  | Yes |  |
| 36 | scheduler/job_registration.py:79 | logger.log | system_log | DEBUG | Job is disabled, skipping. {job_log_details} | job_log_details | stdout | stdout |  | Yes |  |
| 37 | scheduler/job_registration.py:99 | logger.log | job_log | INFO | Scheduled interval job '{db_job.name}' (interval: {db_job.interval_seconds}s) | db_job.name, db_job.interval_seconds, db_job.id | stdout, db | stdout, db |  | Yes |  |
| 38 | scheduler/job_registration.py:118 | logger.log | job_log | INFO | Scheduled cron job '{db_job.name}' (cron: {db_job.cron_string}) | db_job.name, db_job.cron_string, db_job.id | stdout, db | stdout, db |  | Yes |  |
| 39 | scheduler/job_registration.py:139 | logger.log | job_log | INFO | Scheduled one-time job '{db_job.name}' for {run_time} | db_job.name, run_time, db_job.id | stdout, db | stdout, db |  | Yes |  |
| 40 | scheduler/job_registration.py:148 | logger.log | job_log | WARNING | One-time job '{db_job.name}' scheduled in the past for {run_time}, skipping | db_job.name, run_time, db_job.id | stdout, db | stdout, db |  | Yes |  |
| 41 | scheduler/job_registration.py:158 | logger.log | job_log | WARNING | Job '{db_job.name}' has no valid schedule type/params, skipping | db_job.name, db_job.id | stdout, db | stdout, db |  | Yes |  |
| 42 | scheduler/job_registration.py:168 | logger.log | job_log | ERROR | Failed to schedule job '{db_job.name}': {schedule_e} | db_job.name, schedule_e, db_job.id | stdout, db | stdout, db |  | Yes |  |
| 43 | scheduler/job_registration.py:177 | logger.log | job_log | INFO | Finished job synchronization. Total enabled: {len(jobs_to_schedule)}, newly scheduled: {scheduled_count}, skipped: {skipped_count}, errors: {error_count} | len(jobs_to_schedule), scheduled_count, skipped_count, error_count | stdout, db | stdout, db |  | Yes |  |
| 44 | scheduler/job_registration.py:185 | logger.log | system_log | ERROR | Error during database query or setup: {e} | e | stdout | stdout |  | Yes |  |
| 45 | scheduler/job_registration.py:194 | logger.log | system_log | DEBUG | Database session closed. |  | stdout | stdout |  | Yes |  |
| 46 | api/routers/auth_router.py:45 | logger.log | system_log | WARNING | Authentication failed: User not found: {username} | username | stdout | stdout |  | Yes | authenticate_user |
| 47 | api/routers/auth_router.py:54 | logger.log | system_log | INFO | Attempting password verification for user: {username} | username | stdout | stdout |  | Yes | authenticate_user |
| 48 | api/routers/auth_router.py:60 | logger.log | system_log | DEBUG | Password provided length: {len(password)} | len(password), username | stdout | stdout |  | Yes | authenticate_user |
| 49 | api/routers/auth_router.py:66 | logger.log | system_log | DEBUG | Stored hash: {user.hashed_password[:10]}... | user.hashed_password, username | stdout | stdout |  | Yes | authenticate_user |
| 50 | api/routers/auth_router.py:74 | logger.log | system_log | WARNING | Authentication failed: Invalid password for user: {username} | username | stdout | stdout |  | Yes | authenticate_user |
| 51 | api/routers/auth_router.py:82 | logger.log | system_log | INFO | Authentication successful for user: {username} | username | stdout | stdout |  | Yes | authenticate_user |
| 52 | api/routers/auth_router.py:116 | logger.log | system_log | INFO | Login attempt for user: {form_data.username} | form_data.username | stdout | stdout |  | Yes | login_for_access_token |
| 53 | api/routers/auth_router.py:131 | logger.log | system_log | WARNING | Login attempt for inactive user: {form_data.username} | form_data.username | stdout | stdout |  | Yes | login_for_access_token |
| 54 | api/routers/auth_router.py:146 | logger.log | system_log | INFO | Token generated successfully for user: {form_data.username} | form_data.username | stdout | stdout |  | Yes | login_for_access_token |
| 55 | api/routers/devices.py:104 | logger.log | system_log | WARNING | Device creation failed: {msg} (request: {request.url if request else 'N/A'}) | msg, request.url | stdout | stdout |  | Yes | create_device |
| 56 | api/routers/devices.py:133 | logger.log | system_log | ERROR | Device creation failed: {e.detail} (request: {request.url if request else 'N/A'}) | e.detail, request.url | stdout | stdout |  | Yes | create_device |
| 57 | api/routers/devices.py:152 | logger.log | system_log | ERROR | Device creation failed: {msg} (request: {request.url if request else 'N/A'}) | msg, request.url | stdout | stdout |  | Yes | create_device |
| 58 | api/routers/devices.py:166 | logger.log | system_log | ERROR | Device creation failed: {msg} (request: {request.url if request else 'N/A'}) | msg, request.url | stdout | stdout |  | Yes | create_device |
| 59 | api/routers/devices.py:351 | logger.log | system_log | WARNING | Device update failed: {msg} (request: {request.url if request else 'N/A'}) | msg, request.url | stdout | stdout |  | Yes | update_device |
| 60 | api/routers/devices.py:366 | logger.log | system_log | ERROR | Device update failed: {e.detail} (request: {request.url if request else 'N/A'}) | e.detail, request.url | stdout | stdout |  | Yes | update_device |
| 61 | api/routers/devices.py:377 | logger.log | system_log | ERROR | Device update failed: {msg} (request: {request.url if request else 'N/A'}) | msg, request.url | stdout | stdout |  | Yes | update_device |
| 62 | api/routers/devices.py:399 | logger.log | system_log | ERROR | Device update failed: {msg} (request: {request.url if request else 'N/A'}) | msg, request.url | stdout | stdout |  | Yes | update_device |
| 63 | api/routers/devices.py:415 | logger.log | system_log | ERROR | Device update failed: {msg} (request: {request.url if request else 'N/A'}) | msg, request.url | stdout | stdout |  | Yes | update_device |
| 64 | worker/executor.py:85 | logger.log | job_log | INFO | Entered reachability_handler for job_id={job_id}, device_id={getattr(device, 'id', None)} | job_id, device_id | stdout, db | stdout, db |  | Yes | reachability_handler |
| 65 | worker/executor.py:132 | logger.log | job_log | INFO | Reachability check completed successfully. | job_id, device_id | stdout, db | stdout, db |  | Yes | reachability_handler |
| 66 | worker/executor.py:141 | logger.log | job_log | INFO | save_job_log (success) completed for job_id={job_id}, device_id={device_id} | job_id, device_id | stdout, db | stdout, db |  | Yes | reachability_handler |
| 67 | worker/executor.py:158 | logger.log | job_log | WARNING | Reachability check failed: ... | job_id, device_id | stdout, db | stdout, db |  | Yes | reachability_handler |
| 68 | worker/executor.py:167 | logger.log | job_log | INFO | save_job_log (failure) completed for job_id={job_id}, device_id={device_id} | job_id, device_id | stdout, db | stdout, db |  | Yes | reachability_handler |
| 69 | worker/executor.py:177 | logger.log | job_log | ERROR | Exception in reachability logging for job_id={job_id}, device_id={device_id}: {log_exc} | job_id, device_id, log_exc | stdout, db | stdout, db |  | Yes | reachability_handler |
| 70 | worker/executor.py:209 | logger.log | job_log | INFO | handle_device called for job_id={job_id}, resolved job_type={job_type} | job_id, job_type | stdout, db | stdout, db |  | Yes | handle_device |
| 71 | worker/executor.py:218 | logger.log | job_log | ERROR | No handler registered for job type: {job_type} | job_id, job_type | stdout, db | stdout, db |  | Yes | handle_device |
| 72 | worker/executor.py:226 | logger.log | job_log | INFO | Dispatching job_id={job_id} (type={job_type}) to handler: {handler.__name__} | job_id, job_type, handler.__name__ | stdout, db | stdout, db |  | Yes | handle_device |
| 73 | api/auth.py:19 | print | print | print | [DEBUG] JWT SECRET_KEY: {SECRET_KEY} | SECRET_KEY, ALGORITHM | stdout | stdout |  | No | Debug secret print: before DB init |
| 74 | api/routers/auth_router.py:113 | print | print | print | DEBUG: /auth/token called with username={form_data.username} | form_data.username | stdout | stdout |  | Yes | login_for_access_token |
| 75 | api/routers/auth_router.py:154 | print | print | print | ERROR in /auth/token: {e} | e | stdout | stdout |  | Yes | login_for_access_token |
| 76 | api/routers/jobs.py:477 | print | print | print | Successfully connected to Redis for RQ. |  | stdout | stdout |  | Yes | jobs endpoint |
| 77 | api/routers/jobs.py:479 | print | print | print | ERROR: Could not connect to Redis at {redis_url} for RQ. Job trigger endpoint will fail. | redis_url | stdout | stdout |  | Maybe | jobs endpoint: may be before DB/Redis ready |
| 78 | api/routers/jobs.py:480 | print | print | print | Error details: {e} | e | stdout | stdout |  | Maybe | jobs endpoint: may be before DB/Redis ready |
| 79 | db/log_utils.py:31 | print | print | print | [LOGGER EXCEPTION] {e} | e | stdout | stdout |  | Maybe | save_log: may be during DB error |
| 80 | db/session.py:12 | print | print | print | [DB SESSION] Database session configured: {db_url} | db_url | stdout | stdout |  | Yes | session config |
| 81 | config/loader.py:64 | print | print | print | Environment not specified, using NETRAVEN_ENV or default: {env} | env | stdout | stdout |  | No | load_config: before config/DB init |
| 82 | config/loader.py:80 | print | print | print | Loaded base configuration from {base_config_path} | base_config_path | stdout | stdout |  | No | load_config: before config/DB init |
| 83 | config/loader.py:82 | print | print | print | Failed to load base config {base_config_path}: {e} | base_config_path, e | stdout | stdout |  | No | load_config: before config/DB init |
| 84 | config/loader.py:91 | print | print | print | Loaded environment configuration from {env_config_path} | env_config_path | stdout | stdout |  | No | load_config: before config/DB init |
| 85 | config/loader.py:93 | print | print | print | Failed to load environment config {env_config_path}: {e} | env_config_path, e | stdout | stdout |  | No | load_config: before config/DB init |
| 86 | config/loader.py:95 | print | print | print | Environment config file not found: {env_config_path} | env_config_path | stdout | stdout |  | No | load_config: before config/DB init |
| 87 | config/loader.py:101 | print | print | print | Applied environment variable overrides: {env_overrides} | env_overrides | stdout | stdout |  | No | load_config: before config/DB init |
| 88 | config/loader.py:104 | print | print | print | Configuration result is empty. Check config files and environment. |  | stdout | stdout |  | No | load_config: before config/DB init |
| 89 | config/loader.py:115 | print | print | print | Loaded Configuration: |  | stdout | stdout |  | No | load_config: before config/DB init |
| 90 | config/loader.py:117 | print | print | print | json.dumps(loaded_config, indent=2) | loaded_config | stdout | stdout |  | No | load_config: before config/DB init |
| 91 | worker/git_writer.py:44 | print | print | print | Repo path {repo_path} does not exist. Creating... | repo_path | stdout | stdout |  | Maybe | commit_configuration_to_git: may be before repo init |
| 92 | worker/git_writer.py:46 | print | print | print | Initializing Git repository at {repo_path}... | repo_path | stdout | stdout |  | Maybe | commit_configuration_to_git: may be before repo init |
| 93 | worker/git_writer.py:48 | print | print | print | Repository initialized. |  | stdout | stdout |  | Yes | commit_configuration_to_git |
| 94 | worker/git_writer.py:53 | print | print | print | Error opening existing repository at {repo_path}: {e}. Attempting to initialize. | repo_path, e | stdout | stdout |  | Maybe | commit_configuration_to_git: may be before repo init |
| 95 | worker/git_writer.py:61 | print | print | print | Writing configuration for device {device_id} to {config_file_path} | device_id, config_file_path | stdout | stdout |  | Yes | commit_configuration_to_git |
| 96 | worker/git_writer.py:70 | print | print | print | Staging file: {config_file_name} | config_file_name | stdout | stdout |  | Yes | commit_configuration_to_git |
| 97 | worker/git_writer.py:75 | print | print | print | Committing with message: '{commit_message}' | commit_message | stdout | stdout |  | Yes | commit_configuration_to_git |
| 98 | worker/git_writer.py:79 | print | print | print | Commit successful. Hash: {commit.hexsha} | commit.hexsha | stdout | stdout |  | Yes | commit_configuration_to_git |
| 99 | worker/git_writer.py:84 | print | print | print | Git command error occurred: {git_err} | git_err | stdout | stdout |  | Yes | commit_configuration_to_git |
| 100 | worker/git_writer.py:88 | print | print | print | An unexpected error occurred during Git operation: {e} | e | stdout | stdout |  | Yes | commit_configuration_to_git |

<!-- Table rows will be filled in below, one per print or log call, using the detailed and raw audit data. --> 