from typing import List, Any, Dict
import time # For simulating work/delays

from netraven.worker import dispatcher
from netraven.db.session import get_db # Assuming this exists
# from netraven.db.models import Job, Device # Assuming these exist
from netraven.config.loader import load_config # Assume this exists and works

# --- Placeholder Data / Mocks --- 
# Replace with actual DB interaction later
class MockDevice:
    """Placeholder for the Device DB Model."""
    def __init__(self, id, device_type, ip_address, username, password, hostname=None):
        self.id = id
        self.device_type = device_type
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.hostname = hostname if hostname else ip_address

def load_devices_for_job(job_id: int) -> List[Any]:
    """Placeholder function to simulate loading devices for a job from DB."""
    print(f"[Job: {job_id}] Simulating loading devices from database...")
    # In reality, query the DB using job_id to find associated devices/groups
    # Example: Query Job table, get associated device tags/IDs, query Device table
    # For now, return a hardcoded list of mock devices
    devices = [
        MockDevice(id=1, device_type="cisco_ios", ip_address="192.168.1.1", username="user", password="pass1", hostname="router1"),
        MockDevice(id=2, device_type="cisco_ios", ip_address="192.168.1.2", username="user", password="pass2", hostname="router2-unreachable"), # Simulate failure
        MockDevice(id=3, device_type="arista_eos", ip_address="10.0.0.1", username="admin", password="pass3", hostname="switch1"),
        MockDevice(id=4, device_type="juniper_junos", ip_address="10.0.0.2", username="admin", password="pass4", hostname="firewall1"),
    ]
    print(f"[Job: {job_id}] Loaded {len(devices)} mock devices.")
    return devices

def update_job_status(job_id: int, status: str, start_time: float = None, end_time: float = None):
    """Placeholder function to simulate updating job status in DB."""
    duration = f" in {end_time - start_time:.2f}s" if start_time and end_time else ""
    print(f"[Job: {job_id}] Simulating update job status to '{status}'{duration}.")
    # In reality, find Job by job_id and update status, started_at, completed_at fields
    pass
# --- End Placeholder Data / Mocks ---

def run_job(job_id: int) -> None:
    """Main entry point to run a specific job by its ID.

    Loads job details and devices, loads configuration, dispatches tasks
    using the dispatcher (passing config), and handles overall job status updates.

    Args:
        job_id: The ID of the job to execute.
    """
    start_time = time.time()
    print(f"[Job: {job_id}] Received job request. Starting...")
    update_job_status(job_id, "RUNNING", start_time=start_time)

    try:
        # 0. Load Configuration
        # Assume load_config determines the environment (e.g., from env var)
        config = load_config()
        print(f"[Job: {job_id}] Configuration loaded.")
        # Example: Accessing a config value
        # repo_path_test = config.get("worker", {}).get("git_repo_path", "DEFAULT_PATH")
        # print(f"[Job: {job_id}] Test read Git repo path from config: {repo_path_test}")

        # 1. Load devices associated with the job
        # Replace this with actual DB call using job_id
        devices_to_process = load_devices_for_job(job_id)

        if not devices_to_process:
            print(f"[Job: {job_id}] No devices found for this job. Marking as complete.")
            update_job_status(job_id, "COMPLETED_NO_DEVICES", start_time=start_time, end_time=time.time())
            return

        # 2. Dispatch tasks using the dispatcher
        # Pass the loaded config down
        print(f"[Job: {job_id}] Handing off {len(devices_to_process)} devices to dispatcher...")
        results = dispatcher.dispatch_tasks(devices_to_process, job_id, config=config)

        # 3. Process results and determine final job status
        successful_tasks = sum(1 for r in results if r.get("success"))
        failed_tasks = len(results) - successful_tasks
        print(f"[Job: {job_id}] Dispatcher finished. Results: {successful_tasks} succeeded, {failed_tasks} failed.")

        # Determine final status based on results
        final_status = "UNKNOWN"
        if successful_tasks == len(results):
            final_status = "COMPLETED_SUCCESS"
        elif failed_tasks == len(results):
            final_status = "COMPLETED_FAILURE"
        else:
            final_status = "COMPLETED_PARTIAL_FAILURE"

        end_time = time.time()
        update_job_status(job_id, final_status, start_time=start_time, end_time=end_time)

    except Exception as e:
        # Catch unexpected errors during job loading or overall processing
        error_message = f"[Job: {job_id}] Unexpected error during run_job: {e}"
        print(error_message)
        # Log this critical failure to the job log if possible
        # Might need a dedicated log_job_error function that doesn't need device_id
        # For now, just update status
        update_job_status(job_id, "FAILED_UNEXPECTED", start_time=start_time, end_time=time.time())
        # Re-raise the exception if needed for the calling process (e.g., RQ worker)
        # raise

    print(f"[Job: {job_id}] Finished job execution.")

# Example of how this might be called (e.g., from setup/dev_runner.py)
# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) > 1:
#         try:
#             job_id_to_run = int(sys.argv[1])
#             run_job(job_id_to_run)
#         except ValueError:
#             print("Please provide a valid integer Job ID.")
#     else:
#         print("Usage: python runner.py <job_id>")
