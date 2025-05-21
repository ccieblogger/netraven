import os
import sys
import shutil
import tempfile
import types
import importlib
import pytest

# Patch sys.path to allow dynamic import of temp job modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../netraven/worker')))

from netraven.worker import job_registry

JOBS_PATH = os.path.join(os.path.dirname(job_registry.__file__), 'jobs')

# --- Legacy function-based job registry tests (deprecated) ---
pytest.skip("Legacy function-based job registry is deprecated. Tests below are skipped.", allow_module_level=True)

@pytest.fixture(autouse=True)
def setup_and_teardown_jobs_dir():
    # Backup and clear jobs dir
    if os.path.exists(JOBS_PATH):
        backup = tempfile.mkdtemp()
        for f in os.listdir(JOBS_PATH):
            shutil.move(os.path.join(JOBS_PATH, f), backup)
    else:
        os.makedirs(JOBS_PATH)
        backup = None
    yield
    # Restore jobs dir
    for f in os.listdir(JOBS_PATH):
        path = os.path.join(JOBS_PATH, f)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    if backup:
        for f in os.listdir(backup):
            shutil.move(os.path.join(backup, f), JOBS_PATH)
        shutil.rmtree(backup)


def write_job_module(name, content):
    """Write a job module with only user-facing fields in JOB_META. job_type is set by the loader."""
    path = os.path.join(JOBS_PATH, f"{name}.py")
    with open(path, "w") as f:
        f.write(content)
    print(f"[DEBUG] Wrote job module: {path}")
    return path

def reload_registry(*module_names):
    import importlib
    importlib.invalidate_caches()
    # Remove test modules from sys.modules to force re-import
    for name in module_names:
        modname = f"netraven.worker.jobs.{name}"
        if modname in sys.modules:
            del sys.modules[modname]
    importlib.reload(job_registry)
    return job_registry

# --- Legacy function-based job registry tests (fully removed for class-based system) ---
# def test_valid_job_module_loads():
#     pass
# def test_missing_job_meta_skipped():
#     pass
# def test_missing_run_skipped():
#     pass
# def test_multiple_unique_filenames_registered():
#     pass

# --- Class-based job plugin test remains below ---
def test_class_based_job_registration():
    # Write a class-based job plugin
    job_code = '''
from netraven.worker.jobs.base import BaseJob
class MyTestJob(BaseJob):
    name = "MyTestJob"
    description = "A test job using the new plugin system."
    def run(self, device, job_id, config, db):
        return {"success": True, "device_id": getattr(device, 'id', None)}
'''
    write_job_module("my_test_job", job_code)
    reg = reload_registry("my_test_job")
    # Discover plugins
    reg.JobRegistry.discover_plugins(JOBS_PATH)
    jobs = reg.JobRegistry.get_all_jobs()
    assert "MyTestJob" in jobs
    job_cls = jobs["MyTestJob"]
    assert issubclass(job_cls, reg.BaseJob)
    instance = job_cls()
    result = instance.run(type("DummyDevice", (), {"id": 1})(), 1, {}, None)
    assert result["success"] is True
    assert result["device_id"] == 1