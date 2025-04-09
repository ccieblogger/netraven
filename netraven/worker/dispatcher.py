from typing import List, Dict, Any, Optional
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import logging
from sqlalchemy.orm import Session

from netraven.worker.executor import handle_device
from netraven.worker.error_handler import ErrorCategory, ErrorInfo, classify_exception

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Default thread pool size if not specified in config
DEFAULT_THREAD_POOL_SIZE = 5

def dispatch_tasks(
    devices: List[Any],
    job_id: int,
    config: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """Dispatches device tasks to a thread pool for parallel execution.
    
    Args:
        devices: List of device objects to process
        job_id: ID of the parent job
        config: Optional configuration dictionary
        db: Optional SQLAlchemy session
    
    Returns:
        List of task result dictionaries, one per device
    """
    # Load thread pool size from config, with fallback
    thread_pool_size = DEFAULT_THREAD_POOL_SIZE
    if config and 'worker' in config and 'thread_pool_size' in config['worker']:
        pool_size = config['worker']['thread_pool_size']
        if isinstance(pool_size, int) and pool_size > 0:
            thread_pool_size = pool_size

    # Load retry configuration
    retry_config = {
        'max_retries': 2,
        'retry_delay': 5
    }
    if config and 'worker' in config:
        if 'retry_attempts' in config['worker']:
            retry_config['max_retries'] = config['worker']['retry_attempts']
        if 'retry_backoff' in config['worker']:
            retry_config['retry_delay'] = config['worker']['retry_backoff']

    log.info(f"[Job: {job_id}] Starting task dispatcher with thread pool size: {thread_pool_size}")
    
    device_count = len(devices) if devices else 0
    if device_count == 0:
        log.warning(f"[Job: {job_id}] No devices to process.")
        return []
    
    log.info(f"[Job: {job_id}] Will process {device_count} devices")
    
    # Results container
    results: List[Dict[str, Any]] = []
    
    # Using a context manager to ensure executor shutdown
    with ThreadPoolExecutor(max_workers=thread_pool_size) as executor:
        # This will hold the Future objects for each device task
        future_to_device = {}
        
        # Submit tasks to the executor
        for device in devices:
            device_id = getattr(device, 'id', 0)
            device_name = getattr(device, 'hostname', f"Device_{device_id}")
            
            log.info(f"[Job: {job_id}] Submitting task for device: {device_name}")
            
            # Submit the task to the executor, capturing the Future
            future = executor.submit(
                task_with_retry,
                device=device,
                job_id=job_id,
                config=config,
                db=db,
                retry_config=retry_config
            )
            
            future_to_device[future] = device
        
        # Process completed futures as they complete
        for future in concurrent.futures.as_completed(future_to_device):
            device = future_to_device[future]
            device_id = getattr(device, 'id', 0)
            device_name = getattr(device, 'hostname', f"Device_{device_id}")
            
            try:
                # Get the result - may raise exception if the task failed
                result = future.result()
                log.info(f"[Job: {job_id}] Task completed for device: {device_name}")
                results.append(result)
            except Exception as e:
                # This handles errors from the future/thread itself, not from the device task
                log.error(f"[Job: {job_id}] Thread error processing device {device_name}: {e}")
                
                # Create a failure result
                error_info = classify_exception(
                    e,
                    job_id=job_id,
                    device_id=device_id,
                    retry_config=retry_config
                )
                
                failure_result = {
                    "device_id": device_id,
                    "success": False,
                    "error": f"Thread error: {str(e)}",
                    "error_info": error_info.to_dict()
                }
                
                results.append(failure_result)
    
    log.info(f"[Job: {job_id}] All device tasks completed. Success rate: {sum(1 for r in results if r.get('success', False))}/{len(results)}")
    
    return results

def task_with_retry(
    device: Any,
    job_id: int,
    config: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
    retry_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute a device task with retry logic.
    
    Args:
        device: Device object to process
        job_id: ID of the parent job
        config: Optional configuration dictionary
        db: Optional SQLAlchemy session
        retry_config: Configuration for retries
        
    Returns:
        Task result dictionary including retry information
    """
    if retry_config is None:
        retry_config = {
            'max_retries': 2,
            'retry_delay': 5
        }
    
    device_id = getattr(device, 'id', 0)
    device_name = getattr(device, 'hostname', f"Device_{device_id}")
    
    # First attempt
    try:
        # Execute the main device handling logic
        result = handle_device(device, job_id, config, db)
        
        # If success, return immediately
        if result.get('success', False):
            result['retries'] = 0  # No retries needed
            return result
            
        # If not success but no exception was raised, classify as unknown
        error_info = classify_exception(
            Exception(result.get('error', 'Unknown error')),
            job_id=job_id,
            device_id=device_id,
            retry_config=retry_config
        )
        
    except Exception as e:
        # Classify the exception
        error_info = classify_exception(
            e,
            job_id=job_id,
            device_id=device_id,
            retry_config=retry_config
        )
        
        # Create initial failure result
        result = {
            "device_id": device_id,
            "success": False,
            "error": str(e),
            "error_info": error_info.to_dict()
        }
    
    # Check if we should retry
    retry_count = 0
    max_retries = retry_config['max_retries']
    
    # Only retry if the error is retriable
    if error_info.is_retriable:
        while retry_count < max_retries:
            retry_count += 1
            
            # Calculate backoff time
            backoff_time = error_info.next_retry_delay()
            
            log.info(
                f"[Job: {job_id}] Retrying device {device_name} in {backoff_time}s "
                f"(attempt {retry_count}/{max_retries})"
            )
            
            # Wait before retry
            time.sleep(backoff_time)
            
            # Update error info for the next attempt
            error_info = error_info.increment_retry()
            
            # Try again
            try:
                retry_result = handle_device(device, job_id, config, db)
                
                # If success, return immediately with retry info
                if retry_result.get('success', False):
                    retry_result['retries'] = retry_count
                    return retry_result
                
                # Update result with latest error
                result = retry_result
                result['retries'] = retry_count
                
            except Exception as retry_e:
                # Classify the new exception
                error_info = classify_exception(
                    retry_e,
                    job_id=job_id,
                    device_id=device_id,
                    retry_config=retry_config
                )
                
                # Update result with retry info
                result = {
                    "device_id": device_id,
                    "success": False,
                    "error": str(retry_e),
                    "retries": retry_count,
                    "error_info": error_info.to_dict()
                }
                
                # If the new error is not retriable, break the loop
                if not error_info.is_retriable:
                    log.warning(
                        f"[Job: {job_id}] Encountered non-retriable error during retry "
                        f"for device {device_name}: {error_info.message}"
                    )
                    break
    
    # Add final retry information to result
    result['retries'] = retry_count
    result['max_retries'] = max_retries
    
    return result
