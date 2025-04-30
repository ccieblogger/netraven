"""Git-based configuration storage and versioning.

This module provides functionality to store network device configurations in a
Git repository, enabling version control and history tracking of device configs.
It handles repository initialization, file creation/updates, and commit operations.

The Git repository serves as a source of truth for device configurations, allowing
for historical review, change detection, and configuration rollback capabilities.
"""

import os
from typing import Optional
from git import Repo, GitCommandError
from netraven.utils.unified_logger import get_unified_logger

logger = get_unified_logger()

def commit_configuration_to_git(
    device_id: int, # Consider using hostname or IP if available for filename
    config_data: str,
    job_id: int,
    repo_path: str # Should be loaded from config
) -> Optional[str]:
    """Commits a device configuration to a local Git repository.

    This function manages the storage of device configurations in a Git repository,
    providing version control for configuration changes. It handles the entire process
    including repository initialization (if needed), file writing, staging, and committing.
    
    The function uses the device ID to create a unique filename for each device's
    configuration, and includes job information in the commit message for traceability.

    Args:
        device_id: Unique identifier for the device (used in the filename)
        config_data: The raw configuration data retrieved from the device
        job_id: Identifier for the job that retrieved this configuration
        repo_path: Absolute or relative path to the local Git repository

    Returns:
        The commit hexsha (str) if successful, None if an error occurred

    Raises:
        No exceptions are raised; errors are caught and returned as None
    """
    try:
        # Ensure the base repository directory exists
        if not os.path.exists(repo_path):
            logger.log(f"Repo path {repo_path} does not exist. Creating...", level="INFO", destinations=["stdout", "file", "db"], source="git_writer")
            os.makedirs(repo_path)
            logger.log(f"Initializing Git repository at {repo_path}...", level="INFO", destinations=["stdout", "file", "db"], source="git_writer")
            repo = Repo.init(repo_path)
            logger.log("Repository initialized.", level="INFO", destinations=["stdout", "file", "db"], source="git_writer")
        else:
            try:
                repo = Repo(repo_path)
            except Exception as e:
                logger.log(f"Error opening existing repository at {repo_path}: {e}. Attempting to initialize.", level="WARNING", destinations=["stdout", "file", "db"], source="git_writer")
                # Handle cases where the directory exists but isn't a valid repo
                repo = Repo.init(repo_path)

        # Define the path for the configuration file
        # Using device_id as per SOT. Consider device hostname/IP for better readability.
        config_file_name = f"{device_id}_config.txt"
        config_file_path = os.path.join(repo.working_tree_dir, config_file_name)
        logger.log(f"Writing configuration for device {device_id} to {config_file_path}", level="INFO", destinations=["stdout", "file", "db"], source="git_writer")

        # Write the configuration data to the file
        # Ensure the directory exists if repo path is nested deeper
        os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
        with open(config_file_path, 'w', encoding='utf-8') as config_file:
            config_file.write(config_data)

        # Stage the file
        logger.log(f"Staging file: {config_file_name}", level="INFO", destinations=["stdout", "file", "db"], source="git_writer")
        repo.index.add([config_file_path])

        # Create a commit message with metadata
        commit_message = f"Config backup for device {device_id} | Job ID: {job_id}"
        logger.log(f"Committing with message: '{commit_message}'", level="INFO", destinations=["stdout", "file", "db"], source="git_writer")

        # Commit the changes
        commit = repo.index.commit(commit_message)
        logger.log(f"Commit successful. Hash: {commit.hexsha}", level="INFO", destinations=["stdout", "file", "db"], source="git_writer")

        return commit.hexsha

    except GitCommandError as git_err:
        logger.log(f"Git command error occurred: {git_err}", level="ERROR", destinations=["stdout", "file", "db"], source="git_writer")
        # Consider logging the error more formally
        return None
    except Exception as e:
        logger.log(f"An unexpected error occurred during Git operation: {e}", level="ERROR", destinations=["stdout", "file", "db"], source="git_writer")
        # Consider logging the error more formally
        return None
