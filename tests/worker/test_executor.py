import pytest
from unittest.mock import MagicMock, patch, ANY

from netraven.worker.executor import reachability_handler

@pytest.fixture
def fake_device():
    class Device:
        id = 42
        hostname = "test-device"
        ip_address = "127.0.0.1"
    return Device()

def test_import_netraven_db_session():
    try:
        from netraven.db import session
    except Exception as e:
        assert False, f"Import failed: {e}"
    assert True

def test_reachability_handler_logs_success(fake_device):
    # Patch subprocess and socket to simulate success
    with patch("subprocess.run") as mock_run, \
         patch("socket.create_connection") as mock_socket, \
         patch("netraven.db.log_utils.save_job_log") as mock_save_log:
        # Simulate ping success
        mock_run.return_value.returncode = 0
        # Simulate TCP success (no exception)
        mock_socket.return_value = MagicMock()
        # Call handler
        result = reachability_handler(fake_device, job_id=123, config=None, db=MagicMock())
        # Assert log was called for success
        mock_save_log.assert_any_call(
            fake_device.id, 123, "Reachability check completed successfully.", success=True, db=ANY
        )
        assert result["success"] is True

def test_reachability_handler_logs_failure(fake_device):
    # Patch subprocess and socket to simulate failure
    with patch("subprocess.run") as mock_run, \
         patch("socket.create_connection", side_effect=Exception("TCP fail")), \
         patch("netraven.db.log_utils.save_job_log") as mock_save_log:
        # Simulate ping failure
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Ping failed"
        # Call handler
        result = reachability_handler(fake_device, job_id=123, config=None, db=MagicMock())
        # Assert log was called for failure
        assert any(
            call_args[0][0] == fake_device.id and
            call_args[0][1] == 123 and
            "Reachability check failed" in call_args[0][2] and
            call_args[1]["success"] is False
            for call_args in mock_save_log.call_args_list
        )
        assert result["success"] is False 