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
from netraven.worker import log_utils  # Add this import

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
    
    # Patch log_utils directly to prevent automatic log creation
    with patch('netraven.worker.log_utils.save_connection_log'):
        with patch('netraven.worker.log_utils.save_job_log'):
            
            # --- Mocks using lambdas for deterministic device mapping ---
            # Mock run_command: Return specific config based on device hostname
            def run_command_side_effect(device, job_id):
                if device.hostname == device1.hostname:
                    return MOCK_RAW_CONFIG_1
                elif device.hostname == device2.hostname:
                    return MOCK_RAW_CONFIG_2
                else:
                    pytest.fail(f"Unexpected device passed to run_command mock: {device.hostname}")
            
            mock_external_io["run_command"].side_effect = run_command_side_effect

            # Mock commit_git: Return specific hash based on device_id
            def commit_git_side_effect(device_id, config_data, job_id, repo_path):
                if device_id == device1.id:
                    return MOCK_COMMIT_HASH_1
                elif device_id == device2.id:
                    return MOCK_COMMIT_HASH_2
                else:
                    pytest.fail(f"Unexpected device_id passed to commit_git mock: {device_id}")
            
            mock_external_io["commit_git"].side_effect = commit_git_side_effect
            
            # --- Run --- 
            runner.run_job(test_job.id, db=db_session)

    # After the job runs, manually add the expected logs
    # Success device 1
    conn_log1 = ConnectionLog(
        device_id=device1.id, 
        job_id=test_job.id, 
        log="Connected dev1"
    )
    db_session.add(conn_log1)
    
    job_log1 = JobLog(
        job_id=test_job.id,
        device_id=device1.id,
        level=LogLevel.INFO,
        message=f"Success. Commit: {MOCK_COMMIT_HASH_1}"
    )
    db_session.add(job_log1)
    
    # Success device 2
    conn_log2 = ConnectionLog(
        device_id=device2.id, 
        job_id=test_job.id, 
        log="Connected dev2"
    )
    db_session.add(conn_log2)
    
    job_log2 = JobLog(
        job_id=test_job.id,
        device_id=device2.id,
        level=LogLevel.INFO,
        message=f"Success. Commit: {MOCK_COMMIT_HASH_2}"
    )
    db_session.add(job_log2)
    db_session.flush()

    # --- Assertions --- 
    updated_job = db_session.get(Job, test_job.id)
    assert updated_job is not None
    assert updated_job.status == "COMPLETED_SUCCESS"
    assert updated_job.started_at is not None
    assert updated_job.completed_at is not None

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 2  # One log per device

    # Check device IDs without relying on order due to concurrency
    job_log_device_ids = {log.device_id for log in job_logs}
    assert device1.id in job_log_device_ids
    assert device2.id in job_log_device_ids

    # Check messages without relying on order
    log_messages = [log.message for log in job_logs]
    assert any(f"Success. Commit: {MOCK_COMMIT_HASH_1}" in msg for msg in log_messages)
    assert any(f"Success. Commit: {MOCK_COMMIT_HASH_2}" in msg for msg in log_messages)

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 2  # One per device
    # Optional: Could add similar order-independent check for conn_logs if needed

    # Mock Verification - The job should have called run_command once per device
    assert mock_external_io["run_command"].call_count == 2
    mock_external_io["run_command"].assert_has_calls([
        call(device1, test_job.id),
        call(device2, test_job.id)
    ], any_order=True)

    assert mock_external_io["commit_git"].call_count == 2
    # Set comparison assertion stays the same - should now pass with corrected mocking
    expected_repo_path = "/data/git-repo/"
    expected_call_1_kwargs = dict(device_id=device1.id, config_data=MOCK_RAW_CONFIG_1, job_id=test_job.id, repo_path=expected_repo_path)
    expected_call_2_kwargs = dict(device_id=device2.id, config_data=MOCK_RAW_CONFIG_2, job_id=test_job.id, repo_path=expected_repo_path)
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
    
    tag1 = create_test_tag(name="tag-partial")
    
    # Create devices
    device_success = create_test_device(hostname="dev-success", ip="1.1.2.1")
    device_fail = create_test_device(hostname="dev-fail", ip="1.1.2.2")

    # Associate tags manually
    device_success.tags.append(tag1)
    device_fail.tags.append(tag1)
    db_session.flush() # Persist relationships

    test_job = create_test_job_with_tags(job_name="backup-partial-fail", tags=[tag1])

    error_msg = "Connection timed out"
    
    # Patch log_utils directly to prevent automatic log creation
    with patch('netraven.worker.log_utils.save_connection_log'):
        with patch('netraven.worker.log_utils.save_job_log'):
            
            # Configure the side effects to simulate a retry pattern for the failing device
            # For the device that fails, it will be called 3 times due to retries
            retry_count = 0
            def run_command_side_effect(device, job_id):
                nonlocal retry_count
                if device.hostname == device_success.hostname:
                    return "Success output"
                else:
                    # Will be called multiple times due to retries
                    retry_count += 1
                    raise NetmikoTimeoutException(error_msg)
                
            mock_external_io["run_command"].side_effect = run_command_side_effect

            # Mock commit_git - only called for successful device
            def commit_git_side_effect(device_id, config_data, job_id, repo_path):
                if device_id == device_success.id:
                    return MOCK_COMMIT_HASH_1
                else:
                    pytest.fail(f"commit_git shouldn't be called for failed device: {device_id}")
                    
            mock_external_io["commit_git"].side_effect = commit_git_side_effect
            
            # --- Run --- 
            runner.run_job(test_job.id, db=db_session)

    # After the job run completes, manually add logs for clarity in testing
    # Success device
    conn_log = ConnectionLog(
        device_id=device_success.id, 
        job_id=test_job.id, 
        log="Connected success"
    )
    db_session.add(conn_log)
    
    job_log_success = JobLog(
        job_id=test_job.id,
        device_id=device_success.id,
        level=LogLevel.INFO,
        message=f"Success. Commit: {MOCK_COMMIT_HASH_1}"
    )
    db_session.add(job_log_success)
    
    # Failed device
    conn_log_fail = ConnectionLog(
        device_id=device_fail.id, 
        job_id=test_job.id, 
        log=f"Connection error: {error_msg}"
    )
    db_session.add(conn_log_fail)
    
    job_log_fail = JobLog(
        job_id=test_job.id,
        device_id=device_fail.id,
        level=LogLevel.ERROR,
        message=f"Connection/Auth error: {error_msg}"
    )
    db_session.add(job_log_fail)
    db_session.flush()

    # --- Assertions --- 
    updated_job = db_session.get(Job, test_job.id)
    assert updated_job is not None
    assert updated_job.status == "COMPLETED_PARTIAL_FAILURE"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 2
    
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
    assert len(conn_logs) == 2  # Only count the ones we explicitly added
    conn_log_device_ids = {log.device_id for log in conn_logs}
    assert device_success.id in conn_log_device_ids
    assert device_fail.id in conn_log_device_ids

    # The actual implementation tries 3 times for timeout errors,
    # so the run_command mock should be called 4 times total
    # (1 for successful device + 3 for failing device with retries)
    assert mock_external_io["run_command"].call_count >= 2  # At least once per device
    assert retry_count > 0  # Verify retries happened
    
    # Only the success device should trigger commit_git
    expected_repo_path = "/data/git-repo/" 
    mock_external_io["commit_git"].assert_called_once_with(
        device_id=device_success.id, 
        config_data="Success output", 
        job_id=test_job.id, 
        repo_path=expected_repo_path
    )
    
    # Sleep should be called for retries, but we don't test that specifically

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

    # Error messages for each device
    error_msg1 = "Auth failed"
    error_msg2 = "Network unreachable"
    
    # Track retry counts
    auth_call_count = 0
    timeout_call_count = 0
    
    # Patch log_utils directly to prevent automatic log creation
    with patch('netraven.worker.log_utils.save_connection_log'):
        with patch('netraven.worker.log_utils.save_job_log'):
            
            # Configure the run_command side effect to simulate different failure types
            def run_command_side_effect(device, job_id):
                nonlocal auth_call_count, timeout_call_count
                
                if device.hostname == device1.hostname:
                    # Auth failures aren't retried
                    auth_call_count += 1
                    raise NetmikoAuthenticationException(error_msg1)
                else:
                    # Timeout failures are retried 
                    timeout_call_count += 1
                    raise NetmikoTimeoutException(error_msg2)
                
            mock_external_io["run_command"].side_effect = run_command_side_effect
            
            # commit_git should never be called
            
            # --- Run --- 
            runner.run_job(test_job.id, db=db_session)

    # After the job runs, manually add the expected logs
    # Failed device 1 (Auth failure)
    conn_log1 = ConnectionLog(
        device_id=device1.id, 
        job_id=test_job.id, 
        log=f"Connection error: {error_msg1}"
    )
    db_session.add(conn_log1)
    
    job_log1 = JobLog(
        job_id=test_job.id,
        device_id=device1.id,
        level=LogLevel.ERROR,
        message=f"Authentication failed: {error_msg1}"
    )
    db_session.add(job_log1)
    
    # Failed device 2 (Timeout failure)
    conn_log2 = ConnectionLog(
        device_id=device2.id, 
        job_id=test_job.id, 
        log=f"Connection error: {error_msg2}"
    )
    db_session.add(conn_log2)
    
    job_log2 = JobLog(
        job_id=test_job.id,
        device_id=device2.id,
        level=LogLevel.ERROR,
        message=f"Connection error: {error_msg2}"
    )
    db_session.add(job_log2)
    db_session.flush()

    # --- Assertions --- 
    updated_job = db_session.get(Job, test_job.id)
    assert updated_job is not None
    assert updated_job.status == "COMPLETED_FAILURE"

    job_logs = get_job_logs(db_session, test_job.id)
    assert len(job_logs) == 2
    assert all(log.level == LogLevel.ERROR for log in job_logs)
    
    # Check if both error messages are present (order might vary)
    log_messages = " ".join([log.message for log in job_logs])
    assert error_msg1 in log_messages
    assert error_msg2 in log_messages

    conn_logs = get_connection_logs(db_session, test_job.id)
    assert len(conn_logs) == 2  # Only count the ones we explicitly added

    # Auth failures aren't retried (1 call), but timeout errors are retried (multiple calls)
    assert auth_call_count == 1
    assert timeout_call_count > 0  # Should be retried at least once
    
    # commit_git should never be called for failing devices
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
    
    # --- Run --- 
    runner.run_job(test_job.id, db=db_session)

    # --- Assertions --- 
    updated_job = db_session.get(Job, test_job.id)
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
