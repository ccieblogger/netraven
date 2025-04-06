import pytest
import os
import shutil
from unittest.mock import patch, MagicMock, call
from git import Repo, GitCommandError

# Import the function to test
from netraven.worker.git_writer import commit_configuration_to_git

# Define constants for testing
TEST_DEVICE_ID = 123
TEST_CONFIG_DATA = "hostname test-router\ninterface Loopback0\n ip address 1.1.1.1 255.255.255.255"
TEST_JOB_ID = 987
TEST_REPO_PATH = "/tmp/test_netraven_git_repo" # Use a temporary path
EXPECTED_FILENAME = f"{TEST_DEVICE_ID}_config.txt"
EXPECTED_COMMIT_MSG = f"Config backup for device {TEST_DEVICE_ID} | Job ID: {TEST_JOB_ID}"
EXPECTED_COMMIT_HASH = "abcdef1234567890"

@pytest.fixture(autouse=True)
def cleanup_test_repo():
    """Fixture to automatically clean up the test repo directory if created."""
    if os.path.exists(TEST_REPO_PATH):
        shutil.rmtree(TEST_REPO_PATH)
    yield # Run the test
    if os.path.exists(TEST_REPO_PATH):
        shutil.rmtree(TEST_REPO_PATH)

@patch('netraven.worker.git_writer.Repo')
@patch('netraven.worker.git_writer.os.path.exists')
@patch('netraven.worker.git_writer.os.makedirs')
@patch('builtins.open', new_callable=MagicMock)
def test_commit_new_repo(mock_open, mock_makedirs, mock_exists, mock_Repo):
    """Test committing to a non-existent repository (initialization)."""
    mock_exists.return_value = False # Repo path doesn't exist

    # Mock the Repo object and its methods
    mock_repo_instance = MagicMock()
    mock_repo_instance.working_tree_dir = TEST_REPO_PATH
    mock_commit = MagicMock()
    mock_commit.hexsha = EXPECTED_COMMIT_HASH
    mock_repo_instance.index.commit.return_value = mock_commit

    # Set Repo.init to return our mocked instance
    mock_Repo.init.return_value = mock_repo_instance

    # --- Call the function --- 
    commit_hash = commit_configuration_to_git(
        TEST_DEVICE_ID, TEST_CONFIG_DATA, TEST_JOB_ID, TEST_REPO_PATH
    )

    # --- Assertions ---
    assert commit_hash == EXPECTED_COMMIT_HASH
    mock_exists.assert_called_once_with(TEST_REPO_PATH)
    mock_makedirs.assert_any_call(TEST_REPO_PATH) # Called for repo path
    mock_Repo.init.assert_called_once_with(TEST_REPO_PATH)
    mock_Repo.assert_not_called() # Don't call Repo() constructor directly

    expected_file_path = os.path.join(TEST_REPO_PATH, EXPECTED_FILENAME)
    # Check makedirs called for file path directory
    mock_makedirs.assert_any_call(os.path.dirname(expected_file_path), exist_ok=True)
    # Check file open/write
    mock_open.assert_called_once_with(expected_file_path, 'w', encoding='utf-8')
    mock_open().__enter__().write.assert_called_once_with(TEST_CONFIG_DATA)
    # Check git add
    mock_repo_instance.index.add.assert_called_once_with([expected_file_path])
    # Check git commit
    mock_repo_instance.index.commit.assert_called_once_with(EXPECTED_COMMIT_MSG)

@patch('netraven.worker.git_writer.Repo')
@patch('netraven.worker.git_writer.os.path.exists')
@patch('netraven.worker.git_writer.os.makedirs') # Keep patching makedirs
@patch('builtins.open', new_callable=MagicMock)
def test_commit_existing_repo(mock_open, mock_makedirs, mock_exists, mock_Repo):
    """Test committing to an existing repository."""
    mock_exists.return_value = True # Repo path exists

    # Mock the Repo object and its methods (similar to above)
    mock_repo_instance = MagicMock()
    mock_repo_instance.working_tree_dir = TEST_REPO_PATH
    mock_commit = MagicMock()
    mock_commit.hexsha = EXPECTED_COMMIT_HASH
    mock_repo_instance.index.commit.return_value = mock_commit

    # Set Repo() constructor to return our mocked instance
    mock_Repo.return_value = mock_repo_instance

    # --- Call the function --- 
    commit_hash = commit_configuration_to_git(
        TEST_DEVICE_ID, TEST_CONFIG_DATA, TEST_JOB_ID, TEST_REPO_PATH
    )

    # --- Assertions ---
    assert commit_hash == EXPECTED_COMMIT_HASH
    mock_exists.assert_called_once_with(TEST_REPO_PATH)
    mock_Repo.init.assert_not_called() # Don't initialize
    mock_Repo.assert_called_once_with(TEST_REPO_PATH) # Call Repo() constructor

    expected_file_path = os.path.join(TEST_REPO_PATH, EXPECTED_FILENAME)
    mock_makedirs.assert_called_once_with(os.path.dirname(expected_file_path), exist_ok=True)
    mock_open.assert_called_once_with(expected_file_path, 'w', encoding='utf-8')
    mock_open().__enter__().write.assert_called_once_with(TEST_CONFIG_DATA)
    mock_repo_instance.index.add.assert_called_once_with([expected_file_path])
    mock_repo_instance.index.commit.assert_called_once_with(EXPECTED_COMMIT_MSG)

@patch('netraven.worker.git_writer.Repo')
@patch('netraven.worker.git_writer.os.path.exists')
def test_git_command_error(mock_exists, mock_Repo):
    """Test handling of GitCommandError during commit."""
    mock_exists.return_value = True
    mock_repo_instance = MagicMock()
    mock_repo_instance.working_tree_dir = TEST_REPO_PATH
    # Simulate GitCommandError on commit
    mock_repo_instance.index.commit.side_effect = GitCommandError("commit", "fatal error")
    mock_Repo.return_value = mock_repo_instance

    # --- Call the function --- 
    commit_hash = commit_configuration_to_git(
        TEST_DEVICE_ID, TEST_CONFIG_DATA, TEST_JOB_ID, TEST_REPO_PATH
    )

    # --- Assertions ---
    assert commit_hash is None
    mock_repo_instance.index.commit.assert_called_once()

@patch('netraven.worker.git_writer.Repo')
@patch('netraven.worker.git_writer.os.path.exists')
def test_other_exception(mock_exists, mock_Repo):
    """Test handling of a generic Exception."""
    mock_exists.return_value = True
    # Simulate generic error on Repo instantiation
    mock_Repo.side_effect = Exception("Something went wrong")

    # --- Call the function --- 
    commit_hash = commit_configuration_to_git(
        TEST_DEVICE_ID, TEST_CONFIG_DATA, TEST_JOB_ID, TEST_REPO_PATH
    )

    # --- Assertions ---
    assert commit_hash is None
    mock_Repo.assert_called_once_with(TEST_REPO_PATH)
