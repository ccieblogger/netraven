import importlib
import pkgutil
import os
import sys
from datetime import datetime
import inspect
from netraven.worker.jobs.base import BaseJob, JobMeta

# Directory containing job modules
JOBS_PATH = os.path.join(os.path.dirname(__file__), "jobs")
PLUGINS_PATH = os.path.join(JOBS_PATH, "plugins")

# Developer log file path
DEV_LOG_PATH = os.path.join(os.path.dirname(__file__), "../../docs/developer_logs/feature-110-dynamic-job-registry/loader.log")

JOB_TYPE_REGISTRY = {}
JOB_TYPE_META = {}

# Ensure jobs and plugins directories exist
if not os.path.exists(JOBS_PATH):
    os.makedirs(JOBS_PATH)
if not os.path.exists(PLUGINS_PATH):
    os.makedirs(PLUGINS_PATH)
    
# Ensure developer log directory exists
os.makedirs(os.path.dirname(DEV_LOG_PATH), exist_ok=True)

def dev_log(message):
    timestamp = datetime.utcnow().isoformat()
    with open(DEV_LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

class JobRegistry:
    """Central registry for all job plugins (class-based)."""
    @classmethod
    def get_all_jobs(cls):
        return dict(JobMeta.registry)

    @classmethod
    def get_job(cls, name: str):
        return JobMeta.registry[name]

    @classmethod
    def discover_plugins(cls, plugins_path: str = PLUGINS_PATH):
        """Import all modules in the plugins directory to trigger registration."""
        for _, module_name, _ in pkgutil.iter_modules([plugins_path]):
            if module_name == "__init__":
                continue
            try:
                importlib.import_module(f"netraven.worker.jobs.plugins.{module_name}")
            except Exception as e:
                dev_log(f"ERROR: Failed to import plugin module '{module_name}': {e}")
                continue

# Discover plugins in the plugins directory
JobRegistry.discover_plugins(PLUGINS_PATH)