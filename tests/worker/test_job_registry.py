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

def test_valid_job_module_loads():
    # No job_type in JOB_META; loader sets it to 'valid_job'
    write_job_module("valid_job", '''\nJOB_META = {"label": "Valid Job"}\ndef run(device, job_id, config, db):\n    return True\n''')
    print(f"[DEBUG] jobs dir contents before reload: {os.listdir(JOBS_PATH)}")
    reg = reload_registry("valid_job")
    print(f"[DEBUG] JOB_TYPE_REGISTRY: {reg.JOB_TYPE_REGISTRY}")
    assert "valid_job" in reg.JOB_TYPE_REGISTRY
    assert callable(reg.JOB_TYPE_REGISTRY["valid_job"])
    assert reg.JOB_TYPE_META["valid_job"]["job_type"] == "valid_job"

def test_missing_job_meta_skipped():
    write_job_module("no_meta", '''\ndef run(device, job_id, config, db):\n    return True\n''')
    reg = reload_registry("no_meta")
    assert "no_meta" not in reg.JOB_TYPE_REGISTRY
    assert all(meta.get("job_type") != "no_meta" for meta in reg.JOB_TYPE_META.values())

def test_missing_run_skipped():
    write_job_module("no_run", '''\nJOB_META = {"label": "No Run"}\n''')
    reg = reload_registry("no_run")
    assert "no_run" not in reg.JOB_TYPE_REGISTRY
    assert "no_run" not in reg.JOB_TYPE_META

def test_multiple_unique_filenames_registered():
    write_job_module("job_a", '''\nJOB_META = {"label": "A"}\ndef run(device, job_id, config, db):\n    return True\n''')
    write_job_module("job_b", '''\nJOB_META = {"label": "B"}\ndef run(device, job_id, config, db):\n    return True\n''')
    print(f"[DEBUG] jobs dir contents before reload: {os.listdir(JOBS_PATH)}")
    reg = reload_registry("job_a", "job_b")
    print(f"[DEBUG] JOB_TYPE_REGISTRY: {reg.JOB_TYPE_REGISTRY}")
    assert "job_a" in reg.JOB_TYPE_REGISTRY
    assert "job_b" in reg.JOB_TYPE_REGISTRY
    assert reg.JOB_TYPE_META["job_a"]["job_type"] == "job_a"
    assert reg.JOB_TYPE_META["job_b"]["job_type"] == "job_b"

def test_run_returns_non_dict_skipped():
    write_job_module("bad_return_type", '''\nJOB_META = {"label": "Bad Return"}\ndef run(device, job_id, config, db):\n    return 123\n''')
    reg = reload_registry("bad_return_type")
    assert "bad_return_type" not in reg.JOB_TYPE_REGISTRY
    assert "bad_return_type" not in reg.JOB_TYPE_META

def test_run_missing_required_fields_skipped():
    write_job_module("missing_fields", '''\nJOB_META = {"label": "Missing Fields"}\ndef run(device, job_id, config, db):\n    return {"success": True}\n''')
    reg = reload_registry("missing_fields")
    assert "missing_fields" not in reg.JOB_TYPE_REGISTRY
    assert "missing_fields" not in reg.JOB_TYPE_META

def test_run_with_required_fields_registered():
    write_job_module("good_job", '''\nJOB_META = {"label": "Good Job"}\ndef run(device, job_id, config, db):\n    return {"success": True, "device_id": 1}\n''')
    reg = reload_registry("good_job")
    assert "good_job" in reg.JOB_TYPE_REGISTRY
    assert reg.JOB_TYPE_META["good_job"]["job_type"] == "good_job" 