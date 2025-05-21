# Context factory for NetRaven job plugins
from netraven.services.device import DeviceService
from netraven.services.inventory import InventoryClient
from netraven.db import SessionLocal
from netraven.utils.logging import get_logger

class PluginContext:
    def __init__(self, user):
        self.user = user
        self.device_service = DeviceService(user)
        self.inventory_client = InventoryClient(user)
        self.db = SessionLocal()
        self.logger = get_logger(__name__)
        # TODO: Add event stream or pub/sub client if/when used

    def close(self):
        self.db.close()
