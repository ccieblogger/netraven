import pytest
from unittest.mock import MagicMock, patch, ANY

from netraven.worker.job_registry import JOB_TYPE_REGISTRY

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
         patch("socket.create_connection") as mock_socket:
        # Simulate ping success
        mock_run.return_value.returncode = 0
        # Simulate TCP success (no exception)
        mock_socket.return_value = MagicMock()
        # Call handler
        reachability_handler = JOB_TYPE_REGISTRY["reachability"]
        result = reachability_handler(fake_device, job_id=123, config=None, db=MagicMock())
        assert result["success"] is True

def test_reachability_handler_logs_failure(fake_device):
    # Patch subprocess and socket to simulate failure
    with patch("subprocess.run") as mock_run, \
         patch("socket.create_connection", side_effect=Exception("TCP fail")):
        # Simulate ping failure
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Ping failed"
        # Call handler
        reachability_handler = JOB_TYPE_REGISTRY["reachability"]
        result = reachability_handler(fake_device, job_id=123, config=None, db=MagicMock())
        assert result["success"] is False