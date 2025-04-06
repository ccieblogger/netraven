import time # Import time for sleep
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session # Add Session

# Import worker components
from netraven.worker.backends import netmiko_driver
from netraven.worker import redactor
from netraven.worker import log_utils
from netraven.worker import git_writer

# Import specific exceptions if needed for finer control
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from git import GitCommandError

# Default values if not found in config
DEFAULT_GIT_REPO_PATH = "/data/git-repo/" # As per SOT example
DEFAULT_RETRY_ATTEMPTS = 2
DEFAULT_RETRY_BACKOFF = 2 # seconds

def handle_device(
    device: Any,
    job_id: int,
    config: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None # Accept optional db session
) -> Dict[str, Any]:
    """Handles the entire process for a single device, including retries.

    Connects to the device (with retries), executes 'show running-config',
    redacts sensitive information, logs output, commits config, logs status.
    Uses the provided DB session for logging.

    Args:
        device: A device object with attributes like id, device_type,
                ip_address, username, password.
        job_id: The ID of the parent job.
        config: The loaded application configuration dictionary.
        db: The SQLAlchemy session to use for database operations.

    Returns:
        A dictionary containing:
        - success (bool): True if all steps completed successfully, False otherwise.
        - result (str | None): The Git commit hash if successful, otherwise None.
        - error (str | None): An error message if success is False, otherwise None.
    """
    device_identifier = getattr(device, 'ip_address', getattr(device, 'hostname', f'Device_{getattr(device, "id", "Unknown")}'))
    device_id = getattr(device, 'id', 0) # Use 0 if no id? Needs refinement.

    # --- Load Configurable Values --- 
    repo_path = DEFAULT_GIT_REPO_PATH
    retry_attempts = DEFAULT_RETRY_ATTEMPTS
    retry_backoff = DEFAULT_RETRY_BACKOFF

    if config:
        repo_path = config.get("worker", {}).get("git_repo_path", DEFAULT_GIT_REPO_PATH)
        retry_attempts = config.get("worker", {}).get("retry_attempts", DEFAULT_RETRY_ATTEMPTS)
        retry_backoff = config.get("worker", {}).get("retry_backoff", DEFAULT_RETRY_BACKOFF)
        # Ensure types are correct (simple check for now)
        if not isinstance(retry_attempts, int) or retry_attempts < 0:
            print(f"[Job: {job_id}, Device: {device_identifier}] Warning: Invalid retry_attempts ({retry_attempts}), using default {DEFAULT_RETRY_ATTEMPTS}")
            retry_attempts = DEFAULT_RETRY_ATTEMPTS
        if not isinstance(retry_backoff, (int, float)) or retry_backoff < 0:
             print(f"[Job: {job_id}, Device: {device_identifier}] Warning: Invalid retry_backoff ({retry_backoff}), using default {DEFAULT_RETRY_BACKOFF}")
             retry_backoff = DEFAULT_RETRY_BACKOFF

    # --- Initialize --- 
    result: Dict[str, Any] = {"success": False, "result": None, "error": None}
    raw_output: str | None = None
    commit_hash: str | None = None
    last_connection_error: Exception | None = None

    try:
        # print(f"[Job: {job_id}, Device: {device_identifier}] Starting processing.") # Removed

        # 1. Connect and get config (with retries)
        # print(f"[Job: {job_id}, Device: {device_identifier}] Attempting connection (Retries: {retry_attempts}, Backoff: {retry_backoff}s)...") # Removed
        for attempt in range(retry_attempts + 1):
            try:
                # TODO: Add connection timeout from config to netmiko_driver call if needed
                raw_output = netmiko_driver.run_command(device)
                # print(f"[Job: {job_id}, Device: {device_identifier}] Connection successful on attempt {attempt + 1}.") # Removed
                last_connection_error = None # Clear last error on success
                break # Exit retry loop on success
            except (NetmikoTimeoutException) as e: # Only retry specific connection errors
                last_connection_error = e
                print(f"[Job: {job_id}, Device: {device_identifier}] Connection attempt {attempt + 1} failed: {e}") # Keep failure prints
                if attempt < retry_attempts:
                    print(f"[Job: {job_id}, Device: {device_identifier}] Retrying in {retry_backoff}s...") # Keep retry prints
                    time.sleep(retry_backoff)
                else:
                    print(f"[Job: {job_id}, Device: {device_identifier}] Max retries reached.") # Keep max retry prints
            except NetmikoAuthenticationException as auth_e:
                 # Do NOT retry on authentication failure
                 print(f"[Job: {job_id}, Device: {device_identifier}] Authentication failed: {auth_e}. Not retrying.") # Keep auth fail prints
                 last_connection_error = auth_e
                 break # Exit loop, will raise later if needed
            except Exception as conn_e: # Catch other potential connection errors, maybe retry?
                 # For now, treat other exceptions as non-retryable
                 print(f"[Job: {job_id}, Device: {device_identifier}] Non-retryable connection error: {conn_e}") # Keep other conn error prints
                 last_connection_error = conn_e
                 break # Exit loop

        # If connection failed after retries (or non-retryable error) raise the last error
        if last_connection_error is not None:
            raise last_connection_error
        
        # If raw_output is still None after loop (shouldn't happen if break logic is right, but check)
        if raw_output is None:
            raise Exception("Connection loop finished without success or explicit error.")

        # print(f"[Job: {job_id}, Device: {device_identifier}] Successfully retrieved config.") # Removed

        # 2. Redact output
        redacted_output = redactor.redact(raw_output, config=config) # Pass config

        # 3. Log redacted output to connection log
        log_utils.save_connection_log(device_id, job_id, redacted_output, db=db)

        # 4. Commit raw config to Git
        commit_hash = git_writer.commit_configuration_to_git(
            device_id=device_id,
            config_data=raw_output, # Commit the original, unredacted data
            job_id=job_id,
            repo_path=repo_path # Use path determined from config or default
        )

        if commit_hash:
            result["success"] = True
            result["result"] = commit_hash
            log_message = f"Success. Commit: {commit_hash}"
            log_utils.save_job_log(device_id, job_id, log_message, success=True, db=db)
        else:
            result["error"] = "Failed to commit configuration to Git repository."
            log_utils.save_job_log(device_id, job_id, result["error"], success=False, db=db)

    # --- Exception Handling --- 
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        error_message = f"Connection/Auth error: {e}"
        result["error"] = error_message
        log_utils.save_job_log(device_id, job_id, error_message, success=False, db=db)

    except GitCommandError as e:
        error_message = f"Git command error: {e}"
        print(f"[Job: {job_id}, Device: {device_identifier}] {error_message}") # Keep specific error prints
        result["error"] = error_message
        log_utils.save_job_log(device_id, job_id, error_message, success=False, db=db)

    except Exception as e:
        # Includes connection errors not caught above, or errors during redaction/logging etc.
        error_message = f"Unexpected error: {e}"
        print(f"[Job: {job_id}, Device: {device_identifier}] {error_message}") # Keep specific error prints
        result["error"] = error_message
        log_utils.save_job_log(device_id, job_id, error_message, success=False, db=db)
        # Log partial output if possible
        if raw_output is not None and result["success"] is False:
            try:
                partial_redacted = redactor.redact(raw_output, config=config)
                log_utils.save_connection_log(device_id, job_id, f"PARTIAL LOG DUE TO ERROR:\n{partial_redacted}", db=db)
            except Exception as log_e:
                print(f"[Job: {job_id}, Device: {device_identifier}] Error saving partial connection log: {log_e}") # Keep log error prints

    return result
