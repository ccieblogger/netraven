import pytest
from unittest.mock import patch, ANY
import os # Import os to potentially check env vars if needed

# Import the main runner function
from netraven.worker import runner
from netraven.db.models import Job, Device, JobLog, ConnectionLog, LogLevel
from sqlalchemy.orm import Session
from netraven.config.loader import load_config # Import the actual loader

# Import Exceptions for mocking
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Note: We rely on fixtures from conftest.py: db_session, create_test_device, create_test_job

# --- Test Data --- 
MOCK_RAW_CONFIG = "hostname myrouter\nenable secret 5 $1$mERo$OSa.d8Ds.[...]\nusername admin privilege 15 password 7 082[...]\nsnmp-server community READONLY ro"
MOCK_COMMIT_HASH = "fedcba9876543210"

# --- Fixtures (Mock only external IO) --- 
@pytest.fixture
def mock_external_io():
    """Mocks external IO dependencies: Netmiko, Git, time.sleep."""
    # Correctly nested patches
    with patch('netraven.worker.backends.netmiko_driver.run_command') as mock_run_cmd:
        with patch('netraven.worker.git_writer.commit_configuration_to_git') as mock_commit_git:
            with patch('time.sleep') as mock_sleep:
                yield {
                    "run_command": mock_run_cmd,
                    "commit_git": mock_commit_git,
                    "sleep": mock_sleep
                }

# --- Helper to query DB within tests --- 
def get_job_logs(db: Session, job_id: int) -> list[JobLog]:
    return db.query(JobLog).filter(JobLog.job_id == job_id).order_by(JobLog.timestamp).all()

def get_connection_logs(db: Session, job_id: int) -> list[ConnectionLog]:
    return db.query(ConnectionLog).filter(ConnectionLog.job_id == job_id).order_by(ConnectionLog.timestamp).all()

def get_job(db: Session, job_id: int) -> Job:
     return db.query(Job).filter(Job.id == job_id).first()

# --- Test Cases (Refactored for Live Config) --- 

def test_run_job_success_live_config_db(
    db_session: Session, 
    create_test_job,
    mock_external_io # Use updated fixture name
):
    """Test run_job success path using live config and DB."""
    # --- Setup --- 
    # Load expected config values from dev.yaml for assertions
    actual_config = load_config() # Load dev config
    expected_repo_path = actual_config.get("worker", {}).get("git_repo_path", "/tmp/netraven_git_repo") # Use same default as loader
    expected_redact_patterns = actual_config.get("worker", {}).get("redaction", {}).get("patterns", [])

    test_job = create_test_job()
    test_device = test_job.device

    # Configure mocks
    mock_external_io["run_command"].return_value = MOCK_RAW_CONFIG
    mock_external_io["commit_git"].return_value = MOCK_COMMIT_HASH

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session)

    # --- Assertions --- 
    db_session.flush() 
    updated_job = get_job(db_session, test_job.id)
    assert updated_job.status == "COMPLETED_SUCCESS"
    assert updated_job.started_at is not None
    assert updated_job.completed_at is not None

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 1
    assert job_logs[0].level == LogLevel.INFO
    assert f"Success. Commit: {MOCK_COMMIT_HASH}" in job_logs[0].message

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 1
    # Check redaction based on dev.yaml patterns
    assert "hostname myrouter" in conn_logs[0].log
    for pattern in expected_redact_patterns:
         assert pattern not in conn_logs[0].log.lower() # Check content NOT present
    if expected_redact_patterns: # Ensure redaction marker is present if patterns exist
         assert "[REDACTED LINE]" in conn_logs[0].log

    # Mock Verification (Check correct repo_path from config is used)
    mock_external_io["run_command"].assert_called_once_with(test_device)
    mock_external_io["commit_git"].assert_called_once_with(
        device_id=test_device.id,
        config_data=MOCK_RAW_CONFIG,
        job_id=test_job.id,
        repo_path=expected_repo_path # Assert path loaded from config
    )
    mock_external_io["sleep"].assert_not_called()

def test_run_job_auth_fail_live_config_db(
    db_session: Session,
    create_test_job,
    mock_external_io
):
    """Test auth failure using live config and DB (retry shouldn't happen)."""
    # --- Setup --- 
    test_job = create_test_job()
    test_device = test_job.device

    error_msg = "Authentication failed - bad password"
    mock_external_io["run_command"].side_effect = NetmikoAuthenticationException(error_msg)

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session)

    # --- Assertions --- 
    db_session.flush()
    updated_job = get_job(db_session, test_job.id)
    assert updated_job.status == "COMPLETED_FAILURE"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 1
    assert job_logs[0].level == LogLevel.ERROR
    # Check for the actual prefix logged by log_utils
    assert "Connection/Auth error:" in job_logs[0].message
    # Ensure the original Netmiko message is included
    assert error_msg in job_logs[0].message

    # Mock Verification
    mock_external_io["run_command"].assert_called_once_with(test_device)
    mock_external_io["commit_git"].assert_not_called()
    mock_external_io["sleep"].assert_not_called() # No retry on auth fail

def test_run_job_timeout_retry_live_config_db(
    db_session: Session,
    create_test_job,
    mock_external_io
):
    """Test timeout and retry based on live config and DB."""
    # --- Setup --- 
    actual_config = load_config() # Load dev config
    expected_retries = actual_config.get("worker", {}).get("retry_attempts", 2) # Get actual retry count
    expected_backoff = actual_config.get("worker", {}).get("retry_backoff", 2) # Get actual backoff
    expected_repo_path = actual_config.get("worker", {}).get("git_repo_path", "/tmp/netraven_git_repo")

    test_job = create_test_job()
    test_device = test_job.device

    # Configure mocks to fail N times (expected_retries), then succeed
    side_effects = [NetmikoTimeoutException("Timed out")] * expected_retries + [MOCK_RAW_CONFIG]
    mock_external_io["run_command"].side_effect = side_effects
    mock_external_io["commit_git"].return_value = MOCK_COMMIT_HASH

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session)

    # --- Assertions --- 
    db_session.flush()
    updated_job = get_job(db_session, test_job.id)
    assert updated_job.status == "COMPLETED_SUCCESS"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 1
    assert job_logs[0].level == LogLevel.INFO
    assert f"Success. Commit: {MOCK_COMMIT_HASH}" in job_logs[0].message

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 1

    # Mock Verification (Check calls based on config)
    assert mock_external_io["run_command"].call_count == expected_retries + 1
    mock_external_io["run_command"].assert_called_with(test_device)
    mock_external_io["commit_git"].assert_called_once_with(
         device_id=test_device.id,
         config_data=MOCK_RAW_CONFIG,
         job_id=test_job.id,
         repo_path=expected_repo_path
    )
    assert mock_external_io["sleep"].call_count == expected_retries
    mock_external_io["sleep"].assert_called_with(expected_backoff)

def test_run_job_timeout_max_retry_fail_live_db(
    db_session: Session,
    create_test_job,
    mock_external_io
):
    """Test timeout failure after max retries based on live config."""
    # --- Setup --- 
    actual_config = load_config()
    expected_retries = actual_config.get("worker", {}).get("retry_attempts", 2)
    expected_backoff = actual_config.get("worker", {}).get("retry_backoff", 2)
    error_msg = "Timed out connecting - final attempt"

    test_job = create_test_job()
    test_device = test_job.device

    # Configure mocks to fail N+1 times
    side_effects = [NetmikoTimeoutException("Timed out")] * expected_retries + [NetmikoTimeoutException(error_msg)]
    mock_external_io["run_command"].side_effect = side_effects

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session)

    # --- Assertions --- 
    db_session.flush()
    updated_job = get_job(db_session, test_job.id)
    assert updated_job.status == "COMPLETED_FAILURE"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 1
    assert job_logs[0].level == LogLevel.ERROR
    assert error_msg in job_logs[0].message # Check final error is logged

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 0 # No connection log on failure

    # Mock Verification
    assert mock_external_io["run_command"].call_count == expected_retries + 1
    mock_external_io["commit_git"].assert_not_called()
    assert mock_external_io["sleep"].call_count == expected_retries
    if expected_retries > 0:
        mock_external_io["sleep"].assert_called_with(expected_backoff)

def test_run_job_no_device_found(db_session: Session, create_test_job, mock_external_io):
    """Test run_job when the job's device lookup fails."""
    # --- Setup --- 
    # Create a valid job with a device first
    test_job = create_test_job() 
    
    # Now, mock the load_device_for_job function specifically for this test
    # to simulate the device not being found *after* the job is created.
    with patch('netraven.worker.runner.load_device_for_job', return_value=None) as mock_load:
        # --- Run --- 
        runner.run_job(test_job.id, db=db_session)

    # --- Assertions --- 
    db_session.flush()
    updated_job = get_job(db_session, test_job.id)
    # The status should be FAILED_NO_DEVICE as set by the runner
    assert updated_job.status == "FAILED_NO_DEVICE"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 0 # No job logs expected for device processing failure

    # Mock Verification
    mock_load.assert_called_once_with(test_job.id, ANY) # Check loader was called
    mock_external_io["run_command"].assert_not_called()
    mock_external_io["commit_git"].assert_not_called()
