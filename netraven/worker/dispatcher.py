"""Task dispatcher for parallel device processing.

This module provides functionality for dispatching tasks to network devices
in parallel using thread pools. It handles task submission, execution with
retry logic, and result collection, providing scalable concurrent device
operations with appropriate error handling.

Key components:
- ThreadPoolExecutor: For concurrent device operations
- Retry mechanism: With exponential backoff for transient failures
- Error classification: To determine if errors are retriable
- Result collection: Aggregating results from parallel operations

The dispatcher is a core component that orchestrates device communication,
ensuring efficient use of resources while maintaining robustness through
retry mechanisms and comprehensive error categorization. It implements
a producer-consumer pattern where:
1. The main thread submits device tasks to the thread pool
2. Worker threads execute device operations concurrently
3. The main thread collects and processes results as they complete

Configuration options control behavior such as:
- Maximum concurrent operations via thread pool size
- Retry policies for failed operations
- Timeout settings for various operation stages
"""

from typing import List, Dict, Any, Optional
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from netraven.worker.executor import handle_device
from netraven.worker.error_handler import ErrorCategory, ErrorInfo, classify_exception
from netraven.utils.unified_logger import get_unified_logger
from netraven.db.models import JobResult

# Default thread pool size if not specified in config
DEFAULT_THREAD_POOL_SIZE = 5

def dispatch_tasks(
    devices: List[Any],
    job_id: int,
    config: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """Dispatch device tasks to a thread pool for parallel execution.
    
    This function is the primary entry point for executing operations against multiple
    devices concurrently. It sets up a thread pool, submits tasks for each device,
    monitors their execution, and collects results. The function handles configuration
    of retry policies and manages thread pool sizing based on configuration.
    
    Thread pool execution ensures that device operations are performed in parallel
    up to the configured maximum, optimizing throughput while managing resource usage.
    The implementation uses concurrent.futures.ThreadPoolExecutor for thread management
    and as_completed() for non-blocking result collection.
    
    Args:
        devices (List[Any]): List of device objects to process. Each device must have
                           the following attributes:
                           - id: Unique identifier
                           - hostname: Device hostname for logging
                           - Other attributes required by handle_device()
        job_id (int): ID of the parent job for correlation and logging purposes
        config (Optional[Dict[str, Any]]): Configuration dictionary with these options:
                                         - worker.thread_pool_size: Max concurrent operations
                                         - worker.retry_attempts: Maximum retry attempts
                                         - worker.retry_backoff: Base delay between retries
                                         - Additional options passed to handle_device()
        db (Optional[Session]): SQLAlchemy session for database operations,
                               passed to device handlers
    
    Returns:
        List[Dict[str, Any]]: List of task result dictionaries, one per device, each containing:
                             - device_id: Device identifier
                             - device_name: Device hostname
                             - success: Boolean indicating success or failure
                             - error: Error message if applicable
                             - error_info: Structured error information if applicable 
                             - retries: Number of retry attempts performed
                             - Additional task-specific result data
    
    Note:
        This function handles failures at multiple levels:
        1. Device-level failures within the task_with_retry function
        2. Thread-level failures if the thread itself encounters an error
        All failures are captured, classified, and included in the results.
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

    logger = get_unified_logger()
    logger.log(
        f"Job '{job_id}' started: dispatching tasks to devices",
        level="INFO",
        destinations=["stdout", "file", "db"],
        job_id=job_id,
        source="dispatcher",
    )
    
    device_count = len(devices) if devices else 0
    if device_count == 0:
        logger.log(
            f"No devices to process for job '{job_id}'",
            level="WARNING",
            destinations=["stdout", "file", "db"],
            job_id=job_id,
            source="dispatcher",
        )
        return []
    
    logger.log(
        f"Job '{job_id}' will process {device_count} devices",
        level="INFO",
        destinations=["stdout", "file", "db"],
        job_id=job_id,
        source="dispatcher",
    )
    
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
            # Device validation
            if not is_valid_device(device):
                logger.log(
                    f"Skipping invalid device (missing required attributes) for job '{job_id}': {device}",
                    level="WARNING",
                    destinations=["stdout", "file", "db"],
                    job_id=job_id,
                    device_id=device_id,
                    source="dispatcher",
                )
                continue
            print(f"[DEBUG dispatcher] Submitting device_id={device_id} device_name={device_name} job_id={job_id}")
            logger.log(
                f"Submitting task for device '{device_name}' in job '{job_id}'",
                level="INFO",
                destinations=["stdout", "file", "db"],
                job_id=job_id,
                device_id=device_id,
                source="dispatcher",
            )
            
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
            try:
                if future in future_to_device:
                    device = future_to_device[future]
                    device_id = getattr(device, 'id', 0)
                    device_name = getattr(device, 'hostname', f"Device_{device_id}")
                else:
                    try:
                        result = future.result()
                        device_id = result.get('device_id', 0)
                        device_name = result.get('device_name', f"Device_{device_id}")
                    except Exception:
                        device_id = 0
                        device_name = "Unknown_Device"
                result = future.result()
                # --- Result Validation ---
                required_fields = ["success", "device_id"]
                if not isinstance(result, dict) or any(f not in result for f in required_fields):
                    logger.log(
                        f"Invalid or missing result from job run() for device '{device_name}' in job '{job_id}'. Generating failure result.",
                        level="ERROR",
                        destinations=["stdout", "file", "db"],
                        job_id=job_id,
                        device_id=device_id,
                        source="dispatcher",
                    )
                    # Generate failure result
                    result = {
                        "device_id": device_id,
                        "device_name": device_name,
                        "success": False,
                        "error": "Job run() did not return a valid result.",
                        "error_info": {"type": "InvalidResult", "msg": "Job run() did not return a dict with required fields."}
                    }
                logger.log(
                    f"Task completed for device '{device_name}' in job '{job_id}'",
                    level="INFO",
                    destinations=["stdout", "file", "db"],
                    job_id=job_id,
                    device_id=device_id,
                    source="dispatcher",
                )
                results.append(result)
                # --- JobResult DB Write ---
                if db is not None:
                    try:
                        # Determine job_type and status
                        job_type = result.get('job_type')
                        if not job_type:
                            # Fallback: fetch from DB if not present
                            from netraven.db.models import Job
                            job_obj = db.query(Job).filter(Job.id == job_id).first()
                            job_type = getattr(job_obj, 'job_type', 'unknown')
                        status = 'success' if result.get('success') else 'failure'
                        # Compose details (exclude redundant fields if needed)
                        details = dict(result)
                        # Remove fields that are already top-level in JobResult
                        for k in ['device_id', 'job_type', 'status', 'job_id', 'result_time', 'created_at']:
                            details.pop(k, None)
                        job_result = JobResult(
                            job_id=job_id,
                            device_id=device_id,
                            job_type=job_type,
                            status=status,
                            result_time=datetime.now(timezone.utc),
                            details=details,
                            created_at=datetime.now(timezone.utc)
                        )
                        db.add(job_result)
                        db.commit()
                        logger.log(
                            f"JobResult created for job_id={job_id}, device_id={device_id}, status={status}, job_type={job_type}",
                            level="INFO",
                            destinations=["stdout", "file", "db"],
                            job_id=job_id,
                            device_id=device_id,
                            source="dispatcher",
                            log_type="job"
                        )
                    except SQLAlchemyError as db_exc:
                        db.rollback()
                        logger.log(
                            f"Failed to create JobResult for job_id={job_id}, device_id={device_id}: {db_exc}",
                            level="ERROR",
                            destinations=["stdout", "file", "db"],
                            job_id=job_id,
                            device_id=device_id,
                            source="dispatcher",
                            log_type="job"
                        )
            except Exception as e:
                logger.log(
                    f"Thread error processing device '{device_name}' in job '{job_id}': {e}",
                    level="ERROR",
                    destinations=["stdout", "file", "db"],
                    job_id=job_id,
                    device_id=device_id,
                    source="dispatcher",
                )
                
                # Attempt to get device info if available
                device_id = 0
                device_name = "Unknown_Device"
                
                if future in future_to_device:
                    device = future_to_device[future]
                    device_id = getattr(device, 'id', 0)
                    device_name = getattr(device, 'hostname', f"Device_{device_id}")
                
                # Create a failure result
                error_info = classify_exception(
                    e,
                    job_id=job_id,
                    device_id=device_id,
                    retry_config=retry_config
                )
                
                failure_result = {
                    "device_id": device_id,
                    "device_name": device_name,
                    "success": False,
                    "error": f"Thread error: {str(e)}",
                    "error_info": error_info.to_dict()
                }
                
                results.append(failure_result)
    
    logger.log(
        f"All device tasks completed for job '{job_id}'. Success rate: {sum(1 for r in results if r.get('success', False))}/{len(results)}",
        level="INFO",
        destinations=["stdout", "file", "db"],
        job_id=job_id,
        source="dispatcher",
    )
    
    return results

def task_with_retry(
    device: Any,
    job_id: int,
    config: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
    retry_config: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute a device task with automatic retry logic.
    
    This function wraps device operation execution with retry capabilities.
    It attempts to execute the device operation, and if it fails with a
    retriable error (as determined by the error classification system),
    it will wait using exponential backoff and retry up to the configured
    maximum number of attempts.
    
    The function includes sophisticated error handling:
    1. All exceptions are caught and classified using the error_handler system
    2. Classification determines if the error is retriable 
    3. Retriable errors trigger retry with exponential backoff
    4. Non-retriable errors fail immediately
    5. Comprehensive error details are included in the result
    
    Args:
        device (Any): Device object to process with attributes:
                    - id: Unique identifier
                    - hostname: Device hostname for logging
                    - Other attributes needed by handle_device()
        job_id (int): ID of the parent job for correlation and logging
        config (Optional[Dict[str, Any]]): Configuration dictionary for device operations,
                                         passed to handle_device()
        db (Optional[Session]): SQLAlchemy session for database operations,
                              passed to handle_device()
        retry_config (Optional[Dict[str, Any]]): Retry configuration with:
                                                - max_retries: Maximum retry attempts
                                                - retry_delay: Base delay in seconds
        metadata (Optional[Dict[str, Any]]): Additional metadata to include in the result
        
    Returns:
        Dict[str, Any]: Task result dictionary containing:
                       - device_id: Device identifier
                       - device_name: Device hostname
                       - success: Boolean indicating success or failure
                       - error: Error message if failure occurred
                       - error_info: Structured error information if failure
                       - retries: Number of retry attempts performed
                       - max_retries: Maximum configured retry attempts
                       - Additional operation-specific result data from handle_device()
    
    Note:
        The retry logic implements exponential backoff where each successive
        retry waits longer than the previous one. The wait time is calculated as:
        retry_delay * (2^retry_count).
    """
    if retry_config is None:
        retry_config = {
            'max_retries': 2,
            'retry_delay': 5
        }
    
    device_id = getattr(device, 'id', 0)
    device_name = getattr(device, 'hostname', f"Device_{device_id}")
    print(f"[DEBUG dispatcher] task_with_retry ENTRY: device_id={device_id} device_name={device_name} job_id={job_id}")
    
    # First attempt
    try:
        # Execute the main device handling logic
        result = handle_device(device, job_id, config, db)
        
        # If success, return immediately
        if result.get('success', False):
            print(f"[DEBUG dispatcher] task_with_retry SUCCESS: device_id={device_id} device_name={device_name} job_id={job_id} retries=0")
            result['retries'] = 0  # No retries needed
            # Ensure device info is in the result
            result['device_id'] = device_id
            result['device_name'] = device_name
            return result

        # --- PATCH: If all credentials are exhausted, do NOT retry ---
        # If result indicates all credentials failed (no error_info), return immediately
        if not result.get('success', False) and not result.get('error_info'):
            print(f"[DEBUG dispatcher] task_with_retry: All credentials exhausted for device_id={device_id} device_name={device_name} job_id={job_id}. Not retrying.")
            result['retries'] = 0
            result['device_id'] = device_id
            result['device_name'] = device_name
            return result
        # --- END PATCH ---

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
            "device_name": device_name,
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
            print(f"[DEBUG dispatcher] Scheduling retry for device_id={device_id} device_name={device_name} job_id={job_id} attempt={retry_count}/{max_retries} in {backoff_time}s")
            logger.log(
                f"Retrying device '{device_name}' in {backoff_time}s (attempt {retry_count}/{max_retries})",
                level="INFO",
                destinations=["stdout", "file", "db"],
                job_id=job_id,
                device_id=device_id,
                source="dispatcher",
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
                    retry_result['device_id'] = device_id
                    retry_result['device_name'] = device_name
                    return retry_result
                
                # Update result with latest error
                result = retry_result
                result['device_id'] = device_id
                result['device_name'] = device_name
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
                    "device_name": device_name,
                    "success": False,
                    "error": str(retry_e),
                    "retries": retry_count,
                    "error_info": error_info.to_dict()
                }
                
                # If the new error is not retriable, break the loop
                if not error_info.is_retriable:
                    logger.log(
                        f"Encountered non-retriable error during retry for device '{device_name}': {error_info.message}",
                        level="WARNING",
                        destinations=["stdout", "file", "db"],
                        job_id=job_id,
                        device_id=device_id,
                        source="dispatcher",
                    )
                    break
    
    # Add final retry information to result
    result['retries'] = retry_count
    result['max_retries'] = max_retries
    
    # Handle status field for test compatibility
    if 'status' in result:
        # If it has a status field, make sure success is set
        if result.get('status') == 'success' and 'success' not in result:
            result['success'] = True
    
    return result

def is_valid_device(device):
    required_attrs = ['id', 'hostname', 'device_type']
    for attr in required_attrs:
        if not hasattr(device, attr) or getattr(device, attr) in (None, '', 0):
            return False
    return True
