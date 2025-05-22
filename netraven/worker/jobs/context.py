# Context factory for NetRaven job plugins
class PluginContext:
    def __init__(self, user):
        # Import dependencies here for easier mocking/testing and to avoid import errors if modules are missing
        from netraven.services.device import DeviceService
        from netraven.services.inventory import InventoryClient
        from netraven.db import SessionLocal
        from netraven.utils.logging import get_logger
        self.user = user
        self.device_service = DeviceService(user)
        self.inventory_client = InventoryClient(user)
        self.db = SessionLocal()
        self.logger = get_logger(__name__)
        # TODO: Add event stream or pub/sub client if/when used

    def close(self):
        self.db.close()
