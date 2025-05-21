import pytest
from unittest.mock import MagicMock, patch
from netraven.worker.jobs.context import PluginContext

class DummyUser:
    pass

def test_plugin_context_instantiates_and_closes():
    user = DummyUser()
    with patch('netraven.worker.jobs.context.DeviceService') as MockDeviceService, \
         patch('netraven.worker.jobs.context.InventoryClient') as MockInventoryClient, \
         patch('netraven.worker.jobs.context.SessionLocal') as MockSessionLocal, \
         patch('netraven.worker.jobs.context.get_logger') as MockGetLogger:
        mock_db = MagicMock()
        MockSessionLocal.return_value = mock_db
        context = PluginContext(user)
        assert context.device_service is MockDeviceService.return_value
        assert context.inventory_client is MockInventoryClient.return_value
        assert context.db is mock_db
        assert context.logger is MockGetLogger.return_value
        context.close()
        mock_db.close.assert_called_once()
