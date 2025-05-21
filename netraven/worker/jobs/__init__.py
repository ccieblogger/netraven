# Auto-discover and import all job modules for plugin registration
import pkgutil
import importlib
import os
from netraven.worker.plugin_settings import NETRAVEN_PLUGIN_PATH

plugin_path = NETRAVEN_PLUGIN_PATH
if not os.path.isdir(plugin_path):
    raise RuntimeError(f"Plugin path not found: {plugin_path}")

for _, module_name, _ in pkgutil.iter_modules([plugin_path]):
    if module_name != "__init__":
        importlib.import_module(f"netraven.worker.jobs.plugins.{module_name}")
