import concurrent.futures
from typing import List, Any, Dict, Optional
from sqlalchemy.orm import Session

from netraven.worker import executor

# Placeholder for configuration - load properly later
DEFAULT_THREAD_POOL_SIZE = 5
DEFAULT_GIT_REPO_PATH = "/data/git-repo/" # Should match executor or be loaded centrally

def dispatch_tasks(
    devices: List[Any],
    job_id: int,
    config: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None # Accept optional db session
) -> List[Dict[str, Any]]:
    """Dispatches tasks to handle multiple devices concurrently using a thread pool.

    Passes the DB session down to the executor tasks.

    Args:
        devices: A list of device objects to process.
        job_id: The ID of the parent job.
        config: The loaded application configuration dictionary.
        db: The SQLAlchemy session to use for database operations within tasks.

    Returns:
        A list of result dictionaries, one for each device processed by handle_device.
    """
    results = []

    # Get max_workers from config, fallback to default
    max_workers = DEFAULT_THREAD_POOL_SIZE
    if config and isinstance(config.get("worker", {}).get("thread_pool_size"), int):
        loaded_max_workers = config["worker"]["thread_pool_size"]
        if loaded_max_workers > 0:
            max_workers = loaded_max_workers
            print(f"[Job: {job_id}] Using thread pool size from config: {max_workers}")
        else:
            print(f"[Job: {job_id}] Config provided invalid thread pool size ({loaded_max_workers}), using default: {max_workers}")
    else:
        print(f"[Job: {job_id}] Using default thread pool size: {max_workers}")

    print(f"[Job: {job_id}] Dispatching tasks for {len(devices)} devices using up to {max_workers} workers...")

    # Using ThreadPoolExecutor to run handle_device concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        # Submit tasks, passing the config AND db session down to the executor
        future_to_device = {
            pool.submit(executor.handle_device, device, job_id, config, db): device
            for device in devices
        }

        for future in concurrent.futures.as_completed(future_to_device):
            device = future_to_device[future]
            device_identifier = getattr(device, 'ip_address', getattr(device, 'hostname', f'Device_{getattr(device, "id", "Unknown")}'))
            try:
                result = future.result() # Get the result dict from handle_device
                print(f"[Job: {job_id}, Device: {device_identifier}] Task completed. Success: {result.get('success')}")
                results.append(result)
            except Exception as exc:
                # This catches exceptions raised *within* handle_device that might not have been caught
                # Or exceptions during the future execution itself (less likely here)
                error_message = f"[Job: {job_id}, Device: {device_identifier}] Task generated an exception: {exc}"
                print(error_message)
                # We should ensure handle_device returns a dict even on failure,
                # but add a fallback result just in case.
                results.append({
                    "success": False,
                    "result": None,
                    "error": error_message
                })
                # Optionally log this failure again using log_utils? handle_device should cover it.

    print(f"[Job: {job_id}] All {len(devices)} tasks dispatched and completed.")
    return results
