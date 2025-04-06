import pytest
from unittest.mock import patch, ANY # Removed MagicMock, call

# Import the main runner function
from netraven.worker import runner
from netraven.db.models import Job, Device, JobLog, ConnectionLog, LogLevel # Import DB models
from sqlalchemy.orm import Session

# Import Exceptions for mocking
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Note: We rely on fixtures from conftest.py: db_session, create_test_device, create_test_job
# Note: We rely on config from dev.yaml being loaded by the actual loader

# --- Test Data (Keep relevant parts) --- 
MOCK_RAW_CONFIG = "hostname myrouter\nenable secret 5 $1$mERo$OSa.d8Ds.[...]\nusername admin privilege 15 password 7 082[...]\nsnmp-server community READONLY ro"
MOCK_COMMIT_HASH = "fedcba9876543210"

# --- Fixtures (Keep only non-DB mocks) --- 
@pytest.fixture
def mock_external_dependencies():
    """Mocks non-DB external dependencies for runner integration tests."""
    # Keep load_config mock for now, remove in Phase 4
    with patch('netraven.worker.runner.load_config') as mock_load_cfg:
        with patch('netraven.worker.backends.netmiko_driver.run_command') as mock_run_cmd:
            with patch('netraven.worker.git_writer.commit_configuration_to_git') as mock_commit_git:
                with patch('time.sleep') as mock_sleep:
                    
                    # Pre-configure the mock config loader
                    mock_config_data = {
                        "worker": {
                            "thread_pool_size": 1, # Use 1 worker for easier sequential assertions
                            "git_repo_path": "/tmp/test_integration_db_repo",
                            "retry_attempts": 1,
                            "retry_backoff": 0.1,
                            "redaction": {"patterns": ["secret", "password", "community"]}
                        },
                        "database": {"url": "placeholder_db_url"} # Add placeholder so loader doesn't fail
                    }
                    mock_load_cfg.return_value = mock_config_data

                    yield {
                        "load_config": mock_load_cfg,
                        "run_command": mock_run_cmd,
                        "commit_git": mock_commit_git,
                        "sleep": mock_sleep,
                        "config_data": mock_config_data # Pass loaded data for reference
                    }

# --- Helper to query DB within tests --- 
def get_job_logs(db: Session, job_id: int) -> list[JobLog]:
    return db.query(JobLog).filter(JobLog.job_id == job_id).order_by(JobLog.timestamp).all()

def get_connection_logs(db: Session, job_id: int) -> list[ConnectionLog]:
    return db.query(ConnectionLog).filter(ConnectionLog.job_id == job_id).order_by(ConnectionLog.timestamp).all()

def get_job(db: Session, job_id: int) -> Job:
     return db.query(Job).filter(Job.id == job_id).first()

# --- Test Cases (Refactored) --- 

def test_run_job_success_live_db(
    db_session: Session, 
    create_test_job,
    mock_external_dependencies
):
    """Test run_job success path with live DB interactions."""
    # --- Setup --- 
    # Create job and associated device in the test DB transaction
    test_job = create_test_job() 
    test_device = test_job.device # Device created by create_test_job fixture

    # Configure mocks
    mock_external_dependencies["run_command"].return_value = MOCK_RAW_CONFIG
    mock_external_dependencies["commit_git"].return_value = MOCK_COMMIT_HASH

    # --- Run --- 
    runner.run_job(test_job.id)

    # --- Assertions --- 
    # DB State Verification (query within the same transaction)
    db_session.flush() # Ensure updates are sent to DB before querying
    updated_job = get_job(db_session, test_job.id)
    assert updated_job is not None
    assert updated_job.status == "COMPLETED_SUCCESS"
    assert updated_job.started_at is not None
    assert updated_job.completed_at is not None

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 1
    assert job_logs[0].level == LogLevel.INFO
    assert job_logs[0].device_id == test_device.id
    assert f"Success. Commit: {MOCK_COMMIT_HASH}" in job_logs[0].message

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 1
    assert conn_logs[0].device_id == test_device.id
    assert "hostname myrouter" in conn_logs[0].log
    assert "[REDACTED LINE]" in conn_logs[0].log
    assert "password" not in conn_logs[0].log
    assert "secret" not in conn_logs[0].log
    assert "community" not in conn_logs[0].log

    # Mock Verification
    mock_external_dependencies["run_command"].assert_called_once_with(test_device)
    mock_external_dependencies["commit_git"].assert_called_once_with(
        device_id=test_device.id,
        config_data=MOCK_RAW_CONFIG,
        job_id=test_job.id,
        repo_path=mock_external_dependencies["config_data"]["worker"]["git_repo_path"]
    )
    mock_external_dependencies["sleep"].assert_not_called()

def test_run_job_auth_fail_live_db(
    db_session: Session,
    create_test_job,
    mock_external_dependencies
):
    """Test run_job with an authentication failure using live DB."""
    # --- Setup --- 
    test_job = create_test_job()
    test_device = test_job.device

    # Configure mocks
    error_msg = "Authentication failed - bad password"
    mock_external_dependencies["run_command"].side_effect = NetmikoAuthenticationException(error_msg)

    # --- Run --- 
    runner.run_job(test_job.id)

    # --- Assertions --- 
    db_session.flush()
    updated_job = get_job(db_session, test_job.id)
    assert updated_job.status == "COMPLETED_FAILURE"
    assert updated_job.started_at is not None
    assert updated_job.completed_at is not None

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 1
    assert job_logs[0].level == LogLevel.ERROR
    assert job_logs[0].device_id == test_device.id
    assert "Authentication error" in job_logs[0].message
    assert error_msg in job_logs[0].message

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 0 # No connection log on auth fail

    # Mock Verification
    mock_external_dependencies["run_command"].assert_called_once_with(test_device)
    mock_external_dependencies["commit_git"].assert_not_called()
    mock_external_dependencies["sleep"].assert_not_called()

def test_run_job_timeout_retry_success_live_db(
    db_session: Session,
    create_test_job,
    mock_external_dependencies
):
    """Test run_job with a timeout, successful retry, using live DB."""
    # --- Setup --- 
    test_job = create_test_job()
    test_device = test_job.device
    retry_backoff = mock_external_dependencies["config_data"]["worker"]["retry_backoff"]

    # Configure mocks to fail first, then succeed
    mock_external_dependencies["run_command"].side_effect = [
        NetmikoTimeoutException("Timed out connecting"), # First call fails
        MOCK_RAW_CONFIG # Second call succeeds
    ]
    mock_external_dependencies["commit_git"].return_value = MOCK_COMMIT_HASH

    # --- Run --- 
    runner.run_job(test_job.id)

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
    assert "[REDACTED LINE]" in conn_logs[0].log # Check redaction still works

    # Mock Verification
    assert mock_external_dependencies["run_command"].call_count == 2
    mock_external_dependencies["run_command"].assert_called_with(test_device)
    mock_external_dependencies["commit_git"].assert_called_once()
    mock_external_dependencies["sleep"].assert_called_once_with(retry_backoff)

def test_run_job_no_device_found(db_session: Session, mock_external_dependencies):
    """Test run_job when the job exists but has no associated device."""
    # --- Setup --- 
    # Create a job manually without using the fixture that creates a device
    test_job = Job(status='pending', device_id=None) # Or link to non-existent device ID
    db_session.add(test_job)
    db_session.commit()
    db_session.refresh(test_job)

    # --- Run --- 
    runner.run_job(test_job.id)

    # --- Assertions --- 
    db_session.flush()
    updated_job = get_job(db_session, test_job.id)
    assert updated_job.status == "FAILED_NO_DEVICE"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 0 # No job logs expected

    # Mock Verification
    mock_external_dependencies["run_command"].assert_not_called()
    mock_external_dependencies["commit_git"].assert_not_called()

# Note: test_run_job_loader_exception is removed as we assume loader works
# or is tested separately. run_job now expects load_config to succeed or raise.
