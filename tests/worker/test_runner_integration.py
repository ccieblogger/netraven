import pytest
from unittest.mock import patch, MagicMock, call, ANY

# Import the main runner function
from netraven.worker import runner
from netraven.worker.backends import netmiko_driver
from netraven.worker import redactor
from netraven.worker import log_utils
from netraven.worker import git_writer
from netraven.worker.executor import DEFAULT_GIT_REPO_PATH, DEFAULT_RETRY_ATTEMPTS, DEFAULT_RETRY_BACKOFF

# Exceptions to simulate
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from git import GitCommandError

# --- Test Data --- 
TEST_JOB_ID = 101
MOCK_CONFIG = {
    "worker": {
        "thread_pool_size": 2, # Test with a small pool
        "git_repo_path": "/tmp/test_integration_repo",
        "retry_attempts": 1, # Test with 1 retry
        "retry_backoff": 0.1, # Short backoff for testing
        "redaction": {
            "patterns": ["secret", "password", "community"]
        }
    }
}

# Mock Devices (using a simple MagicMock or similar could also work)
# Using the placeholder class from runner for convenience during development
# Ensure this is adapted if runner.MockDevice is removed
class MockDeviceRunner:
    """Placeholder matching runner.MockDevice structure for tests."""
    def __init__(self, id, device_type, ip_address, username, password, hostname=None):
        self.id = id
        self.device_type = device_type
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.hostname = hostname if hostname else ip_address

MOCK_DEVICE_SUCCESS = MockDeviceRunner(
    id=1, device_type="cisco_ios", ip_address="1.1.1.1", username="user", password="pass1", hostname="device-ok"
)
MOCK_DEVICE_TIMEOUT = MockDeviceRunner(
    id=2, device_type="cisco_ios", ip_address="2.2.2.2", username="user", password="pass2", hostname="device-timeout"
)
MOCK_DEVICE_AUTH = MockDeviceRunner(
    id=3, device_type="cisco_ios", ip_address="3.3.3.3", username="user", password="wrong", hostname="device-auth-fail"
)
MOCK_DEVICE_GIT_FAIL = MockDeviceRunner(
    id=4, device_type="cisco_ios", ip_address="4.4.4.4", username="user", password="pass4", hostname="device-git-fail"
)
MOCK_DEVICE_LIST_ALL = [
    MOCK_DEVICE_SUCCESS,
    MOCK_DEVICE_TIMEOUT,
    MOCK_DEVICE_AUTH,
    MOCK_DEVICE_GIT_FAIL
]

MOCK_RAW_CONFIG = "hostname myrouter\nenable secret 5 $1$mERo$OSa.d8Ds.[...]\nusername admin privilege 15 password 7 082[...]\nsnmp-server community READONLY ro"
MOCK_REDACTED_CONFIG = "hostname myrouter\n[REDACTED LINE]\n[REDACTED LINE]\n[REDACTED LINE]"
MOCK_COMMIT_HASH = "fedcba9876543210"


# --- Fixtures --- 
@pytest.fixture
def mock_dependencies():
    """Mocks all external dependencies for runner integration tests."""
    # Nesting the 'with' statements is the standard way
    with patch('netraven.worker.runner.load_config', return_value=MOCK_CONFIG) as mock_load_cfg:
        with patch('netraven.worker.runner.load_devices_for_job') as mock_load_dev:
            with patch('netraven.worker.runner.update_job_status') as mock_update_stat:
                with patch('netraven.worker.backends.netmiko_driver.run_command') as mock_run_cmd:
                    with patch('netraven.worker.log_utils.save_connection_log') as mock_save_conn:
                        with patch('netraven.worker.log_utils.save_job_log') as mock_save_job:
                            with patch('netraven.worker.git_writer.commit_configuration_to_git') as mock_commit_git:
                                with patch('time.sleep') as mock_sleep: # Mock sleep during retries
                                    yield {
                                        "load_config": mock_load_cfg,
                                        "load_devices": mock_load_dev,
                                        "update_status": mock_update_stat,
                                        "run_command": mock_run_cmd,
                                        "save_conn_log": mock_save_conn,
                                        "save_job_log": mock_save_job,
                                        "commit_git": mock_commit_git,
                                        "sleep": mock_sleep
                                    }

# --- Test Cases --- 

def test_run_job_all_success(mock_dependencies):
    """Test run_job where all devices succeed."""
    mock_dependencies["load_devices"].return_value = [MOCK_DEVICE_SUCCESS]
    mock_dependencies["run_command"].return_value = MOCK_RAW_CONFIG
    mock_dependencies["commit_git"].return_value = MOCK_COMMIT_HASH

    # --- Run --- 
    runner.run_job(TEST_JOB_ID)

    # --- Assertions --- 
    # Config Loading
    mock_dependencies["load_config"].assert_called_once()
    # DB Interactions
    mock_dependencies["load_devices"].assert_called_once_with(TEST_JOB_ID)
    status_calls = [
        call(TEST_JOB_ID, "RUNNING", start_time=ANY),
        call(TEST_JOB_ID, "COMPLETED_SUCCESS", start_time=ANY, end_time=ANY)
    ]
    mock_dependencies["update_status"].assert_has_calls(status_calls)
    # Netmiko Call
    mock_dependencies["run_command"].assert_called_once_with(MOCK_DEVICE_SUCCESS)
    # Redaction (implicitly tested via connection log)
    # Logging Calls
    mock_dependencies["save_conn_log"].assert_called_once_with(
        MOCK_DEVICE_SUCCESS.id, TEST_JOB_ID, MOCK_REDACTED_CONFIG
    )
    mock_dependencies["save_job_log"].assert_called_once_with(
        MOCK_DEVICE_SUCCESS.id, TEST_JOB_ID, f"Success. Commit: {MOCK_COMMIT_HASH}", success=True
    )
    # Git Call
    mock_dependencies["commit_git"].assert_called_once_with(
        device_id=MOCK_DEVICE_SUCCESS.id,
        config_data=MOCK_RAW_CONFIG,
        job_id=TEST_JOB_ID,
        repo_path=MOCK_CONFIG["worker"]["git_repo_path"]
    )
    # Sleep should not be called
    mock_dependencies["sleep"].assert_not_called()

def test_run_job_mixed_results(mock_dependencies):
    """Test run_job with a mix of success, timeout (with retry), auth fail, git fail."""
    mock_dependencies["load_devices"].return_value = MOCK_DEVICE_LIST_ALL

    # Use a counter within the side effect to track calls for retry logic
    run_command_calls = {"count": 0}
    def side_effect_run_command(device):
        run_command_calls["count"] += 1
        if device == MOCK_DEVICE_SUCCESS or device == MOCK_DEVICE_GIT_FAIL:
            return MOCK_RAW_CONFIG
        elif device == MOCK_DEVICE_TIMEOUT:
            # Fail first time (call count 1 for this device), succeed second time (call count 2)
            # This requires careful tracking if tests run in parallel or order changes.
            # A more robust mock might track calls per device_id.
            # Assuming simple sequential execution for this mock:
            if run_command_calls["count"] <= 1: # Approximation for first call to this device
                 raise NetmikoTimeoutException("Connection timed out")
            else:
                 return MOCK_RAW_CONFIG # Success on retry
        elif device == MOCK_DEVICE_AUTH:
            raise NetmikoAuthenticationException("Authentication failed")
        else:
            raise Exception(f"Unknown device in mock: {device.hostname}")

    mock_dependencies["run_command"].side_effect = side_effect_run_command

    def side_effect_commit_git(device_id, config_data, job_id, repo_path):
        if device_id == MOCK_DEVICE_GIT_FAIL.id:
            return None # Simulate Git commit failure
        else:
            return MOCK_COMMIT_HASH # Success for others

    mock_dependencies["commit_git"].side_effect = side_effect_commit_git

    # --- Run --- 
    runner.run_job(TEST_JOB_ID)

    # --- Assertions --- 
    # Status Update
    status_calls = [
        call(TEST_JOB_ID, "RUNNING", start_time=ANY),
        call(TEST_JOB_ID, "COMPLETED_PARTIAL_FAILURE", start_time=ANY, end_time=ANY)
    ]
    mock_dependencies["update_status"].assert_has_calls(status_calls)

    # Check run_command calls (1 success + 2 timeout + 1 auth + 1 git_fail = 5 total calls)
    assert mock_dependencies["run_command"].call_count == 5
    mock_dependencies["run_command"].assert_any_call(MOCK_DEVICE_SUCCESS)
    mock_dependencies["run_command"].assert_any_call(MOCK_DEVICE_TIMEOUT) # Called twice
    mock_dependencies["run_command"].assert_any_call(MOCK_DEVICE_AUTH)
    mock_dependencies["run_command"].assert_any_call(MOCK_DEVICE_GIT_FAIL)

    # Check sleep called for the retry
    mock_dependencies["sleep"].assert_called_once_with(MOCK_CONFIG["worker"]["retry_backoff"])

    # Check Job Logs (2 success, 2 fail)
    log_calls = mock_dependencies["save_job_log"].call_args_list
    assert len(log_calls) == 4
    success_logs = [c for c in log_calls if c.kwargs['success'] is True]
    fail_logs = [c for c in log_calls if c.kwargs['success'] is False]
    assert len(success_logs) == 2
    assert len(fail_logs) == 2

    # Verify specific failure messages (optional, depends on exact format)
    assert any("Authentication failed" in str(c) for c in fail_logs)
    assert any("Failed to commit" in str(c) for c in fail_logs)

    # Check Connection Logs (3 logs: success, retry success, git fail success)
    assert mock_dependencies["save_conn_log"].call_count == 3
    mock_dependencies["save_conn_log"].assert_any_call(MOCK_DEVICE_SUCCESS.id, TEST_JOB_ID, MOCK_REDACTED_CONFIG)
    mock_dependencies["save_conn_log"].assert_any_call(MOCK_DEVICE_TIMEOUT.id, TEST_JOB_ID, MOCK_REDACTED_CONFIG)
    mock_dependencies["save_conn_log"].assert_any_call(MOCK_DEVICE_GIT_FAIL.id, TEST_JOB_ID, MOCK_REDACTED_CONFIG)

    # Check Git Commits (3 attempts: success, retry success, git fail)
    assert mock_dependencies["commit_git"].call_count == 3

def test_run_job_no_devices(mock_dependencies):
    """Test run_job when no devices are loaded."""
    mock_dependencies["load_devices"].return_value = []

    # --- Run --- 
    runner.run_job(TEST_JOB_ID)

    # --- Assertions --- 
    mock_dependencies["load_devices"].assert_called_once_with(TEST_JOB_ID)
    # Dispatcher should not be called
    # Status should be RUNNING then COMPLETED_NO_DEVICES
    status_calls = [
        call(TEST_JOB_ID, "RUNNING", start_time=ANY),
        call(TEST_JOB_ID, "COMPLETED_NO_DEVICES", start_time=ANY, end_time=ANY)
    ]
    mock_dependencies["update_status"].assert_has_calls(status_calls)
    mock_dependencies["run_command"].assert_not_called()
    mock_dependencies["commit_git"].assert_not_called()
    mock_dependencies["save_job_log"].assert_not_called()

def test_run_job_loader_exception(mock_dependencies):
    """Test run_job when device loading raises an exception."""
    mock_dependencies["load_devices"].side_effect = Exception("DB connection error")

    # --- Run --- 
    runner.run_job(TEST_JOB_ID)

    # --- Assertions --- 
    mock_dependencies["load_devices"].assert_called_once_with(TEST_JOB_ID)
    # Status should be RUNNING then FAILED_UNEXPECTED
    status_calls = [
        call(TEST_JOB_ID, "RUNNING", start_time=ANY),
        call(TEST_JOB_ID, "FAILED_UNEXPECTED", start_time=ANY, end_time=ANY)
    ]
    mock_dependencies["update_status"].assert_has_calls(status_calls)
    # Other core functions should not be called
    mock_dependencies["run_command"].assert_not_called()
    mock_dependencies["commit_git"].assert_not_called()
    mock_dependencies["save_job_log"].assert_not_called()
