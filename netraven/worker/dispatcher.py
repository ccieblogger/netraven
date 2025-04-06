import concurrent.futures
from typing import List, Any, Dict

from netraven.worker import executor

# Placeholder for configuration - load properly later
DEFAULT_THREAD_POOL_SIZE = 5
DEFAULT_GIT_REPO_PATH = "/data/git-repo/" # Should match executor or be loaded centrally

def dispatch_tasks(devices: List[Any], job_id: int, max_workers: int = DEFAULT_THREAD_POOL_SIZE, repo_path: str = DEFAULT_GIT_REPO_PATH) -> List[Dict[str, Any]]:
    """Dispatches tasks to handle multiple devices concurrently using a thread pool.

    Args:
        devices: A list of device objects to process.
        job_id: The ID of the parent job.
        max_workers: The maximum number of threads to use.
        repo_path: The path to the Git repository for storing configs.

    Returns:
        A list of result dictionaries, one for each device processed by handle_device.
    """
    results = []
    print(f"[Job: {job_id}] Dispatching tasks for {len(devices)} devices using up to {max_workers} workers...")

    # Using ThreadPoolExecutor to run handle_device concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        # Create a future for each device
        # We use submit to pass different arguments to each call if needed,
        # but map might be simpler if only device changes.
        # Using submit allows passing job_id and repo_path easily.
        future_to_device = {
            pool.submit(executor.handle_device, device, job_id, repo_path): device
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
