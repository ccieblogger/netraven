import importlib
import pkgutil
import os
import sys
from datetime import datetime

# Directory containing job modules
JOBS_PATH = os.path.join(os.path.dirname(__file__), "jobs")

# Developer log file path
DEV_LOG_PATH = os.path.join(os.path.dirname(__file__), "../../docs/developer_logs/feature-110-dynamic-job-registry/loader.log")

JOB_TYPE_REGISTRY = {}
JOB_TYPE_META = {}

# Ensure jobs directory exists
if not os.path.exists(JOBS_PATH):
    os.makedirs(JOBS_PATH)
    
# Ensure developer log directory exists
os.makedirs(os.path.dirname(DEV_LOG_PATH), exist_ok=True)

def dev_log(message):
    timestamp = datetime.utcnow().isoformat()
    with open(DEV_LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

for _, module_name, _ in pkgutil.iter_modules([JOBS_PATH]):
    if module_name == "__init__":
        continue
    try:
        module = importlib.import_module(f"netraven.worker.jobs.{module_name}")
    except Exception as e:
        dev_log(f"ERROR: Failed to import module '{module_name}': {e}")
        continue
    meta = getattr(module, "JOB_META", None)
    run_func = getattr(module, "run", None)
    if meta is None:
        dev_log(f"WARNING: Module '{module_name}' missing JOB_META. Skipped.")
        continue
    # Automatically set job_type in meta to the filename
    meta["job_type"] = module_name
    if not callable(run_func):
        dev_log(f"WARNING: Module '{module_name}' missing callable run(). Skipped.")
        continue
    if module_name in JOB_TYPE_REGISTRY:
        dev_log(f"ERROR: Duplicate job_type/filename '{module_name}' in module '{module_name}'. Skipped.")
        continue
    JOB_TYPE_REGISTRY[module_name] = run_func
    JOB_TYPE_META[module_name] = meta
    dev_log(f"SUCCESS: Registered job_type '{module_name}' from module '{module_name}'.") 