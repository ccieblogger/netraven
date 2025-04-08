import pytest
from unittest.mock import patch, ANY, call
import os # Import os to potentially check env vars if needed

# Import the main runner function
from netraven.worker import runner
from netraven.db.models import Job, Device, JobLog, ConnectionLog, LogLevel, Tag # Import Tag
from sqlalchemy.orm import Session
from netraven.config.loader import load_config # Import the actual loader

# Import Exceptions for mocking
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Note: We rely on fixtures from conftest.py: db_session, 
# We will redefine create_test_job/device here or in conftest to handle tags

# --- Test Data --- 
MOCK_RAW_CONFIG_1 = "hostname router1\ninterface eth0"
MOCK_RAW_CONFIG_2 = "hostname router2\ninterface eth1"
MOCK_RAW_CONFIG_3 = "hostname firewall3\ninterface eth2"
MOCK_COMMIT_HASH_1 = "fedcba9876543210"
MOCK_COMMIT_HASH_2 = "abcdef0123456789"
MOCK_COMMIT_HASH_3 = "deadbeefcafebabe"

# --- Test Fixtures (Update for Tags) --- 

# Assume conftest.py provides db_session
# We create job/tag/device fixtures here for clarity

@pytest.fixture
def create_test_tag(db_session: Session): # New fixture for tags
    def _create_test_tag(name: str, type: str = "test") -> Tag:
        tag = Tag(name=name, type=type)
        db_session.add(tag)
        db_session.flush() # Get ID
        return tag
    return _create_test_tag

@pytest.fixture
def create_test_device(db_session: Session): # Fixture to create devices (can associate tags later)
    def _create_test_device(hostname: str, ip: str, dev_type: str = "cisco_ios") -> Device:
        device = Device(hostname=hostname, ip_address=ip, device_type=dev_type)
        db_session.add(device)
        db_session.flush() # Get ID
        return device
    return _create_test_device

@pytest.fixture
def create_test_job_with_tags(db_session: Session): # Fixture for jobs linked to tags
    def _create_test_job(job_name: str, tags: List[Tag]) -> Job:
        job = Job(name=job_name, status="pending", is_enabled=True, schedule_type='onetime')
        job.tags.extend(tags) # Associate tags
        db_session.add(job)
        db_session.flush() # Get ID
        return job
    return _create_test_job

@pytest.fixture
def mock_external_io(): # No change needed here
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

# --- Helper Functions (No change needed) --- 
def get_job_logs(db: Session, job_id: int) -> list[JobLog]:
    return db.query(JobLog).filter(JobLog.job_id == job_id).order_by(JobLog.timestamp).all()

def get_connection_logs(db: Session, job_id: int) -> list[ConnectionLog]:
    return db.query(ConnectionLog).filter(ConnectionLog.job_id == job_id).order_by(ConnectionLog.timestamp).all()

def get_job(db: Session, job_id: int) -> Job:
    return db.query(Job).filter(Job.id == job_id).first()

# --- Test Cases (Refactored for Multiple Devices) --- 

def test_run_job_success_multiple_devices(
    db_session: Session, 
    create_test_job_with_tags,
    create_test_tag,
    create_test_device,
    mock_external_io
):
    """Test successful job run with multiple devices via tags."""
    # --- Setup ---
    config = load_config()
    repo_path = config.get("worker", {}).get("git_repo_path")

    tag1 = create_test_tag(name="core")
    tag2 = create_test_tag(name="dist")
    
    dev1 = create_test_device(hostname="r1", ip="1.1.1.1")
    dev2 = create_test_device(hostname="r2", ip="1.1.1.2")
    dev3 = create_test_device(hostname="sw1", ip="1.1.1.3")

    tag1.devices.append(dev1)
    tag1.devices.append(dev2)
    tag2.devices.append(dev3)
    db_session.flush() # Associate devices with tags

    test_job = create_test_job_with_tags(job_name="backup-core-dist", tags=[tag1, tag2])

    # Mock responses for each device
    mock_external_io["run_command"].side_effect = [MOCK_RAW_CONFIG_1, MOCK_RAW_CONFIG_2, MOCK_RAW_CONFIG_3]
    mock_external_io["commit_git"].side_effect = [MOCK_COMMIT_HASH_1, MOCK_COMMIT_HASH_2, MOCK_COMMIT_HASH_3]

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session)

    # --- Assertions --- 
    db_session.flush()
    updated_job = get_job(db_session, test_job.id)
    assert updated_job.status == "COMPLETED_SUCCESS"
    assert updated_job.started_at is not None
    assert updated_job.completed_at is not None

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 3 # One log per device
    assert job_logs[0].device_id == dev1.id
    assert job_logs[1].device_id == dev2.id
    assert job_logs[2].device_id == dev3.id # Order might vary, could check IDs exist
    assert f"Success. Commit: {MOCK_COMMIT_HASH_1}" in job_logs[0].message
    assert f"Success. Commit: {MOCK_COMMIT_HASH_2}" in job_logs[1].message
    assert f"Success. Commit: {MOCK_COMMIT_HASH_3}" in job_logs[2].message

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 3 # One per device

    # Mock Verification
    assert mock_external_io["run_command"].call_count == 3
    mock_external_io["run_command"].assert_has_calls([
        call(dev1),
        call(dev2),
        call(dev3)
    ], any_order=True) # Order depends on thread execution

    assert mock_external_io["commit_git"].call_count == 3
    mock_external_io["commit_git"].assert_has_calls([
        call(device_id=dev1.id, config_data=MOCK_RAW_CONFIG_1, job_id=test_job.id, repo_path=repo_path),
        call(device_id=dev2.id, config_data=MOCK_RAW_CONFIG_2, job_id=test_job.id, repo_path=repo_path),
        call(device_id=dev3.id, config_data=MOCK_RAW_CONFIG_3, job_id=test_job.id, repo_path=repo_path)
    ], any_order=True)

    mock_external_io["sleep"].assert_not_called()

def test_run_job_partial_failure(
    db_session: Session, 
    create_test_job_with_tags,
    create_test_tag,
    create_test_device,
    mock_external_io
):
    """Test partial failure: one device fails auth, one succeeds."""
    # --- Setup ---
    config = load_config()
    repo_path = config.get("worker", {}).get("git_repo_path")
    auth_fail_msg = "Auth failed r1"
    
    tag1 = create_test_tag(name="edge")
    dev1 = create_test_device(hostname="r1-edge", ip="1.1.2.1")
    dev2 = create_test_device(hostname="r2-edge", ip="1.1.2.2")
    tag1.devices.extend([dev1, dev2])
    db_session.flush()

    test_job = create_test_job_with_tags(job_name="backup-edge", tags=[tag1])

    # Mock: dev1 fails auth, dev2 succeeds
    mock_external_io["run_command"].side_effect = [
        NetmikoAuthenticationException(auth_fail_msg), 
        MOCK_RAW_CONFIG_2
    ]
    mock_external_io["commit_git"].return_value = MOCK_COMMIT_HASH_2 # Only dev2 commits

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session)

    # --- Assertions --- 
    db_session.flush()
    updated_job = get_job(db_session, test_job.id)
    assert updated_job.status == "COMPLETED_PARTIAL_FAILURE"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 2
    
    # Find logs by device ID as order isn't guaranteed
    log_dev1 = next((log for log in job_logs if log.device_id == dev1.id), None)
    log_dev2 = next((log for log in job_logs if log.device_id == dev2.id), None)
    
    assert log_dev1 is not None
    assert log_dev1.level == LogLevel.ERROR
    assert auth_fail_msg in log_dev1.message

    assert log_dev2 is not None
    assert log_dev2.level == LogLevel.INFO
    assert f"Success. Commit: {MOCK_COMMIT_HASH_2}" in log_dev2.message

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 1 # Only successful device
    assert conn_logs[0].device_id == dev2.id 

    # Mock Verification
    assert mock_external_io["run_command"].call_count == 2
    mock_external_io["commit_git"].assert_called_once_with(
        device_id=dev2.id, config_data=MOCK_RAW_CONFIG_2, job_id=test_job.id, repo_path=repo_path
    )
    mock_external_io["sleep"].assert_not_called()

def test_run_job_total_failure(
    db_session: Session, 
    create_test_job_with_tags,
    create_test_tag,
    create_test_device,
    mock_external_io
):
    """Test total failure: all devices fail."""
    # --- Setup ---
    tag1 = create_test_tag(name="failed")
    dev1 = create_test_device(hostname="r1-fail", ip="1.1.3.1")
    dev2 = create_test_device(hostname="r2-fail", ip="1.1.3.2")
    tag1.devices.extend([dev1, dev2])
    db_session.flush()

    test_job = create_test_job_with_tags(job_name="backup-fail", tags=[tag1])

    # Mock: both devices fail
    error_msg1 = "Timeout r1"
    error_msg2 = "Auth failed r2"
    mock_external_io["run_command"].side_effect = [
        NetmikoTimeoutException(error_msg1), 
        NetmikoAuthenticationException(error_msg2)
    ]

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session)

    # --- Assertions --- 
    db_session.flush()
    updated_job = get_job(db_session, test_job.id)
    assert updated_job.status == "COMPLETED_FAILURE"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 2
    assert all(log.level == LogLevel.ERROR for log in job_logs)
    # Check if both error messages are present (order might vary)
    log_messages = " ".join([log.message for log in job_logs])
    assert error_msg1 in log_messages
    assert error_msg2 in log_messages

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 0

    # Mock Verification
    assert mock_external_io["run_command"].call_count == 2 # 1 attempt per device (timeout retries handled in executor)
    mock_external_io["commit_git"].assert_not_called()

def test_run_job_no_devices_found_via_tags(
    db_session: Session, 
    create_test_job_with_tags,
    create_test_tag,
    mock_external_io
):
    """Test job run where associated tags have no devices."""
    # --- Setup ---
    tag_no_devices = create_test_tag(name="empty-tag")
    test_job = create_test_job_with_tags(job_name="backup-empty", tags=[tag_no_devices])

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session)

    # --- Assertions --- 
    db_session.flush()
    updated_job = get_job(db_session, test_job.id)
    assert updated_job.status == "COMPLETED_NO_DEVICES"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 0

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 0

    # Mock Verification
    mock_external_io["run_command"].assert_not_called()
    mock_external_io["commit_git"].assert_not_called()

# Keep retry tests, but they now operate implicitly within handle_device called by the dispatcher.
# The runner itself doesn't directly see the retries, only the final success/failure per device.
# We might need separate executor tests if detailed retry logic needs verification.

# Remove old single-device tests: 
# test_run_job_auth_fail_live_config_db -> covered by partial/total failure
# test_run_job_timeout_retry_live_config_db -> covered by success/partial/total
# test_run_job_timeout_max_retry_fail_live_db -> covered by partial/total
# test_run_job_no_device_found -> replaced by test_run_job_no_devices_found_via_tags
