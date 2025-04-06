from typing import Any, Dict, Optional

# Import worker components
from netraven.worker.backends import netmiko_driver
from netraven.worker import redactor
from netraven.worker import log_utils
from netraven.worker import git_writer

# Import specific exceptions if needed for finer control
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from git import GitCommandError

# Default path if not found in config
DEFAULT_GIT_REPO_PATH = "/data/git-repo/" # As per SOT example

def handle_device(
    device: Any,
    job_id: int,
    config: Optional[Dict[str, Any]] = None # Accept loaded config
) -> Dict[str, Any]:
    """Handles the entire process for a single device.

    Connects to the device, executes 'show running-config', redacts sensitive
    information (using config), logs the redacted output, commits the raw
    configuration to Git (using repo_path from config), and logs the final
    job status for the device.

    Args:
        device: A device object with attributes like id, device_type,
                ip_address, username, password.
        job_id: The ID of the parent job.
        config: The loaded application configuration dictionary.

    Returns:
        A dictionary containing:
        - success (bool): True if all steps completed successfully, False otherwise.
        - result (str | None): The Git commit hash if successful, otherwise None.
        - error (str | None): An error message if success is False, otherwise None.
    """
    # Assume device has an 'id' attribute for logging/git
    device_identifier = getattr(device, 'ip_address', getattr(device, 'hostname', f'Device_{getattr(device, "id", "Unknown")}'))
    device_id = getattr(device, 'id', 0) # Use 0 if no id? Needs refinement.

    # Get repo path from config, fallback to default
    repo_path = DEFAULT_GIT_REPO_PATH
    if config and isinstance(config.get("worker", {}).get("git_repo_path"), str):
         repo_path = config["worker"]["git_repo_path"]
         print(f"[Job: {job_id}, Device: {device_identifier}] Using Git repo path from config: {repo_path}")
    else:
         print(f"[Job: {job_id}, Device: {device_identifier}] Using default Git repo path: {repo_path}")


    result: Dict[str, Any] = {"success": False, "result": None, "error": None}
    raw_output: str | None = None
    commit_hash: str | None = None

    try:
        print(f"[Job: {job_id}, Device: {device_identifier}] Starting processing.")

        # 1. Connect and get config
        print(f"[Job: {job_id}, Device: {device_identifier}] Connecting and running command...")
        # TODO: Add connection timeout from config to netmiko_driver call if needed
        raw_output = netmiko_driver.run_command(device)
        print(f"[Job: {job_id}, Device: {device_identifier}] Successfully retrieved config.")

        # 2. Redact output
        print(f"[Job: {job_id}, Device: {device_identifier}] Redacting output...")
        redacted_output = redactor.redact(raw_output, config=config) # Pass config

        # 3. Log redacted output to connection log
        print(f"[Job: {job_id}, Device: {device_identifier}] Saving connection log...")
        log_utils.save_connection_log(device_id, job_id, redacted_output)

        # 4. Commit raw config to Git
        print(f"[Job: {job_id}, Device: {device_identifier}] Committing raw config to Git (Repo: {repo_path})...")
        commit_hash = git_writer.commit_configuration_to_git(
            device_id=device_id,
            config_data=raw_output, # Commit the original, unredacted data
            job_id=job_id,
            repo_path=repo_path # Use path determined from config or default
        )

        if commit_hash:
            print(f"[Job: {job_id}, Device: {device_identifier}] Git commit successful: {commit_hash}")
            result["success"] = True
            result["result"] = commit_hash
            log_message = f"Successfully retrieved config and committed to Git. Commit: {commit_hash}"
            log_utils.save_job_log(device_id, job_id, log_message, success=True)
        else:
            # Git commit failed (error already printed by git_writer)
            result["error"] = "Failed to commit configuration to Git repository."
            log_utils.save_job_log(device_id, job_id, result["error"], success=False)

    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        error_message = f"Connection/Auth error for {device_identifier}: {e}"
        print(error_message)
        result["error"] = error_message
        # Log only job error, not connection log as connection failed
        log_utils.save_job_log(device_id, job_id, error_message, success=False)

    except GitCommandError as e:
        error_message = f"Git command error for {device_identifier}: {e}"
        print(error_message)
        result["error"] = error_message
        # Attempt to log job error even if Git failed
        log_utils.save_job_log(device_id, job_id, error_message, success=False)
        # If raw_output was retrieved, maybe still log connection?
        # For now, we only log connection on success *before* git commit attempt.

    except Exception as e:
        error_message = f"Unexpected error processing {device_identifier}: {e}"
        print(error_message)
        result["error"] = error_message
        # Log generic error
        log_utils.save_job_log(device_id, job_id, error_message, success=False)
        # Potentially log partial redacted output if available?
        if raw_output is not None and result["success"] is False: # Check if output was fetched before error
            try:
                print(f"[Job: {job_id}, Device: {device_identifier}] Logging potentially partial redacted output due to error...")
                partial_redacted = redactor.redact(raw_output, config=config) # Pass config here too
                log_utils.save_connection_log(device_id, job_id, f"PARTIAL LOG DUE TO ERROR:\n{partial_redacted}")
            except Exception as log_e:
                print(f"[Job: {job_id}, Device: {device_identifier}] Error saving partial connection log: {log_e}")

    print(f"[Job: {job_id}, Device: {device_identifier}] Finished processing. Success: {result['success']}")
    return result
