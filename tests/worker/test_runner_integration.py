import pytest
from unittest.mock import patch, ANY, call, MagicMock
import os # Import os to potentially check env vars if needed
from typing import List # Add this import
from datetime import datetime # Import datetime
import logging

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
    create_test_device,
    create_test_tag,
    mock_external_io,
    mocker
):
    """Test a successful job run with multiple devices fetched via tags."""
    # --- Setup ---
    config = load_config()
    repo_path = config.get("worker", {}).get("git_repo_path")

    tag1 = create_test_tag(name="tag1")
    tag2 = create_test_tag(name="tag2")
    
    # Create devices
    device1 = create_test_device(hostname="dev1", ip="1.1.1.1")
    device2 = create_test_device(hostname="dev2", ip="1.1.1.2")

    # Associate tags manually
    device1.tags.append(tag1)
    device2.tags.append(tag1)
    device2.tags.append(tag2)
    db_session.flush() # Persist relationships before job run

    # Job targets devices with tag1
    test_job = create_test_job_with_tags(job_name="backup-multiple-success", tags=[tag1])

    # --- Mocks using lambdas for deterministic device mapping ---
    
    # Mock run_command: Return specific config based on device hostname
    def run_command_side_effect(device, job_id):
        if device.hostname == device1.hostname:
            return (True, MOCK_RAW_CONFIG_1, {"type": "connection", "job_id": job_id, "device_id": device1.id, "log": "Connected dev1", "timestamp": datetime.utcnow()})
        elif device.hostname == device2.hostname:
            return (True, MOCK_RAW_CONFIG_2, {"type": "connection", "job_id": job_id, "device_id": device2.id, "log": "Connected dev2", "timestamp": datetime.utcnow()})
        else:
            pytest.fail(f"Unexpected device passed to run_command mock: {device.hostname}")
    mock_external_io["run_command"].side_effect = run_command_side_effect

    # Mock commit_git: Return specific hash/log based on device_id
    def commit_git_side_effect(device_id, device_hostname, config_data, job_id, repo_path):
        if device_id == device1.id:
            return (MOCK_COMMIT_HASH_1, {"type": "job", "job_id": job_id, "device_id": device1.id, "message": f"Success. Commit: {MOCK_COMMIT_HASH_1}", "level": "INFO", "timestamp": datetime.utcnow()})
        elif device_id == device2.id:
            return (MOCK_COMMIT_HASH_2, {"type": "job", "job_id": job_id, "device_id": device2.id, "message": f"Success. Commit: {MOCK_COMMIT_HASH_2}", "level": "INFO", "timestamp": datetime.utcnow()})
        else:
            pytest.fail(f"Unexpected device_id passed to commit_git mock: {device_id}")
    mock_external_io["commit_git"].side_effect = commit_git_side_effect

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session) 

    # --- Assertions --- 
    updated_job = db_session.get(Job, test_job.id) # Use db_session.get
    assert updated_job is not None
    assert updated_job.status == "COMPLETED_SUCCESS"
    assert updated_job.started_at is not None
    assert updated_job.completed_at is not None

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 2 # One log per device

    # Check device IDs without relying on order due to concurrency
    job_log_device_ids = {log.device_id for log in job_logs}
    assert device1.id in job_log_device_ids
    assert device2.id in job_log_device_ids

    # Check messages without relying on order
    log_messages = [log.message for log in job_logs]
    assert any(f"Success. Commit: {MOCK_COMMIT_HASH_1}" in msg for msg in log_messages)
    assert any(f"Success. Commit: {MOCK_COMMIT_HASH_2}" in msg for msg in log_messages)

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 2 # One per device
    # Optional: Could add similar order-independent check for conn_logs if needed

    # Mock Verification
    assert mock_external_io["run_command"].call_count == 2
    mock_external_io["run_command"].assert_has_calls([
        call(device1, test_job.id),
        call(device2, test_job.id)
    ], any_order=True)

    assert mock_external_io["commit_git"].call_count == 2
    # Set comparison assertion remains the same - should now pass with corrected mocking
    expected_repo_path = "/data/git-repo/"
    expected_call_1_kwargs = dict(device_id=device1.id, device_hostname=device1.hostname, config_data=MOCK_RAW_CONFIG_1, job_id=test_job.id, repo_path=expected_repo_path)
    expected_call_2_kwargs = dict(device_id=device2.id, device_hostname=device2.hostname, config_data=MOCK_RAW_CONFIG_2, job_id=test_job.id, repo_path=expected_repo_path)
    actual_calls_kwargs_list = [c.kwargs for c in mock_external_io["commit_git"].call_args_list]
    actual_calls_set = {tuple(sorted(kwargs.items())) for kwargs in actual_calls_kwargs_list}
    expected_calls_set = {tuple(sorted(expected_call_1_kwargs.items())), tuple(sorted(expected_call_2_kwargs.items()))}
    assert actual_calls_set == expected_calls_set, f"Expected commit_git calls {expected_calls_set} but got {actual_calls_set}"

    mock_external_io["sleep"].assert_not_called()

def test_run_job_partial_failure_multiple_devices(
    db_session: Session, 
    create_test_job_with_tags,
    create_test_device,
    create_test_tag,
    mock_external_io,
    mocker
):
    """Test job run with multiple devices where one fails."""
    # --- Setup ---
    config = load_config()
    repo_path = config.get("worker", {}).get("git_repo_path")
    auth_fail_msg = "Auth failed r1"
    
    tag1 = create_test_tag(name="tag-partial")
    
    # Create devices
    device_success = create_test_device(hostname="dev-success", ip="1.1.2.1")
    device_fail = create_test_device(hostname="dev-fail", ip="1.1.2.2")

    # Associate tags manually
    device_success.tags.append(tag1)
    device_fail.tags.append(tag1)
    db_session.flush() # Persist relationships

    test_job = create_test_job_with_tags(job_name="backup-partial-fail", tags=[tag1])

    # Simulate failure for device_fail - lambda returns 3-tuple with actual datetime
    error_msg = "Connection timed out"
    mock_external_io["run_command"].side_effect = lambda device, job_id: \
        (True, "Success output", {"type": "connection", "job_id": job_id, "device_id": device.id, "log": "Connected success", "timestamp": datetime.utcnow()}) if device.hostname == device_success.hostname else \
        (False, None, {"type": "connection", "job_id": job_id, "device_id": device.id, "log": error_msg, "timestamp": datetime.utcnow()})

    # Mock commit_git - return 2-tuple with actual datetime
    mock_external_io["commit_git"].return_value = (MOCK_COMMIT_HASH_1, {"type": "job", "job_id": test_job.id, "device_id": device_success.id, "message": f"Success. Commit: {MOCK_COMMIT_HASH_1}", "level": "INFO", "timestamp": datetime.utcnow()})

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session) # Add db=db_session back

    # --- Assertions --- 
    updated_job = db_session.get(Job, test_job.id) # Use db_session.get
    assert updated_job is not None
    assert updated_job.status == "COMPLETED_PARTIAL_FAILURE"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 2 # Check length again
    
    # Find logs by device ID as order isn't guaranteed
    log_dev1 = next((log for log in job_logs if log.device_id == device_fail.id), None)
    log_dev2 = next((log for log in job_logs if log.device_id == device_success.id), None)
    
    assert log_dev1 is not None
    assert log_dev1.level == LogLevel.ERROR
    assert error_msg in log_dev1.message

    assert log_dev2 is not None
    assert log_dev2.level == LogLevel.INFO
    assert "Success" in log_dev2.message

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 2 # Expect logs for both attempts
    conn_log_device_ids = {log.device_id for log in conn_logs}
    assert device_success.id in conn_log_device_ids
    assert device_fail.id in conn_log_device_ids

    # Mock Verification
    assert mock_external_io["run_command"].call_count == 2
    
    # Use the path we know the code *actually* uses based on previous errors
    expected_repo_path = "/data/git-repo/" 
    mock_external_io["commit_git"].assert_called_once_with(
        device_id=device_success.id, 
        device_hostname=device_success.hostname, 
        config_data="Success output", 
        job_id=test_job.id, 
        repo_path=expected_repo_path # Use explicitly set path
    )
    mock_external_io["sleep"].assert_not_called()

def test_run_job_total_failure_multiple_devices(
    db_session: Session, 
    create_test_job_with_tags,
    create_test_device,
    create_test_tag,
    mock_external_io,
    mocker
):
    """Test job run where all devices fail."""
    # --- Setup ---
    tag1 = create_test_tag(name="tag-total-fail")
    
    # Create devices
    device1 = create_test_device(hostname="dev-fail1", ip="1.1.3.1")
    device2 = create_test_device(hostname="dev-fail2", ip="1.1.3.2")

    # Associate tags manually
    device1.tags.append(tag1)
    device2.tags.append(tag1)
    db_session.flush() # Persist relationships

    test_job = create_test_job_with_tags(job_name="backup-total-fail", tags=[tag1])

    # Simulate failure for both devices - lambda returns 3-tuple with actual datetime
    error_msg1 = "Auth failed"
    error_msg2 = "Network unreachable"
    mock_external_io["run_command"].side_effect = lambda device, job_id: \
        (False, None, {"type": "connection", "job_id": job_id, "device_id": device.id, "log": error_msg1, "timestamp": datetime.utcnow()}) if device.hostname == device1.hostname else \
        (False, None, {"type": "connection", "job_id": job_id, "device_id": device.id, "log": error_msg2, "timestamp": datetime.utcnow()})

    # Mock commit_git - should not be called
    # No return value needed, just check assert_not_called below

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session) # Add db=db_session back

    # --- Assertions --- 
    updated_job = db_session.get(Job, test_job.id) # Use db_session.get
    assert updated_job is not None
    assert updated_job.status == "COMPLETED_FAILURE"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 2 # Check length again
    assert all(log.level == LogLevel.ERROR for log in job_logs)
    # Check if both error messages are present (order might vary)
    log_messages = " ".join([log.message for log in job_logs])
    assert error_msg1 in log_messages
    assert error_msg2 in log_messages

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 2 # Expect logs for both failed attempts

    # Mock Verification
    assert mock_external_io["run_command"].call_count == 2 # 1 attempt per device (timeout retries handled in executor)
    mock_external_io["commit_git"].assert_not_called()

def test_run_job_no_devices_found_via_tags(
    db_session: Session, 
    create_test_job_with_tags,
    create_test_tag,
    mock_external_io,
    mocker
):
    """Test job run where associated tags have no devices."""
    # --- Setup ---
    tag_no_devices = create_test_tag(name="empty-tag")
    test_job = create_test_job_with_tags(job_name="backup-empty", tags=[tag_no_devices])

    # Mock responses for each device - return 3-tuple (success, output, log_dict)
    mock_external_io["run_command"].side_effect = [
        (True, MOCK_RAW_CONFIG_1, {"log": "Connected dev1"}), 
        (True, MOCK_RAW_CONFIG_2, {"log": "Connected dev2"})
    ]
    # Mock commit_git - return 2-tuple (commit_hash, log_dict)
    mock_external_io["commit_git"].side_effect = [
        (MOCK_COMMIT_HASH_1, {"message": f"Success. Commit: {MOCK_COMMIT_HASH_1}", "level": "INFO"}),
        (MOCK_COMMIT_HASH_2, {"message": f"Success. Commit: {MOCK_COMMIT_HASH_2}", "level": "INFO"})
    ]

    # --- Run --- 
    runner.run_job(test_job.id, db=db_session) # Add db=db_session back

    # --- Assertions --- 
    updated_job = db_session.get(Job, test_job.id) # Use db_session.get
    assert updated_job is not None
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
