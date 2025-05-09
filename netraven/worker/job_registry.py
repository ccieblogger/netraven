import importlib
import pkgutil
import os
import sys
from datetime import datetime
import inspect

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
    # --- Contract Enforcement: Validate run() return value ---
    required_fields = ["success", "device_id"]
    try:
        sig = inspect.signature(run_func)
        # Prepare dummy args for signature
        dummy_device = type("DummyDevice", (), {"id": 0, "hostname": "dummy", "ip_address": "127.0.0.1", "device_type": "test"})()
        dummy_job_id = 0
        dummy_config = {}
        dummy_db = None
        # Only call if function expects 4 or fewer args
        if len(sig.parameters) == 4:
            result = run_func(dummy_device, dummy_job_id, dummy_config, dummy_db)
            if not isinstance(result, dict):
                dev_log(f"ERROR: Module '{module_name}' run() did not return a dict. Skipped.")
                continue
            missing = [f for f in required_fields if f not in result]
            if missing:
                dev_log(f"ERROR: Module '{module_name}' run() result missing required fields: {missing}. Skipped.")
                continue
        else:
            dev_log(f"WARNING: Module '{module_name}' run() signature does not match expected (device, job_id, config, db). Skipped contract check.")
    except Exception as e:
        dev_log(f"ERROR: Exception during contract check for module '{module_name}': {e}. Skipped.")
        continue
    if module_name in JOB_TYPE_REGISTRY:
        dev_log(f"ERROR: Duplicate job_type/filename '{module_name}' in module '{module_name}'. Skipped.")
        continue
    JOB_TYPE_REGISTRY[module_name] = run_func
    JOB_TYPE_META[module_name] = meta
    dev_log(f"SUCCESS: Registered job_type '{module_name}' from module '{module_name}'.") 