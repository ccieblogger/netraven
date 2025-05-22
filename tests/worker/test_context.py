import sys
from types import ModuleType
import pytest
from unittest.mock import MagicMock

# Patch sys.modules before importing PluginContext
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

from netraven.worker.jobs.context import PluginContext

class DummyUser:
    pass

def test_plugin_context_instantiates_and_closes():
    user = DummyUser()
    context = PluginContext(user)
    assert context.device_service is mock_device_service.DeviceService.return_value
    assert context.inventory_client is mock_inventory_client.InventoryClient.return_value
    assert context.db is mock_session_local.SessionLocal.return_value
    assert context.logger is mock_logging.get_logger.return_value
    context.close()
    context.db.close.assert_called_once()
