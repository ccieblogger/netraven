import sys
from types import ModuleType
from unittest.mock import MagicMock, patch
import pytest

# Patch sys.modules before importing PluginContext and ExampleJob
mock_device_service = ModuleType("netraven.services.device")
mock_inventory_client = ModuleType("netraven.services.inventory")
mock_session_local = ModuleType("netraven.db")
mock_logging = ModuleType("netraven.utils.logging")

mock_device_service.DeviceService = MagicMock()
mock_inventory_client.InventoryClient = MagicMock()
mock_session_local.SessionLocal = MagicMock()
mock_logging.get_logger = MagicMock()

sys.modules["netraven.services.device"] = mock_device_service
sys.modules["netraven.services.inventory"] = mock_inventory_client
sys.modules["netraven.db"] = mock_session_local
sys.modules["netraven.utils.logging"] = mock_logging

from netraven.worker.jobs.base import ExampleJob
from netraven.worker.job_registry import JobRegistry

class DummyUser:
    pass

def test_job_registry_executes_job_with_context():
    user = DummyUser()
    params = {"device": "dummy_device", "job_id": 123, "config": {}}
    with patch("netraven.worker.jobs.context.PluginContext") as MockContext:
        mock_context = MockContext.return_value
        mock_context.db = MagicMock()
        result = JobRegistry.execute_job("ExampleJob", user, params)
        assert result["success"] is True
        assert result["job_id"] == 123
        mock_context.close.assert_called_once()
