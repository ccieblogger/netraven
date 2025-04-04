"""
Scheduler Service Client.

This module provides a client for interacting with the Scheduler service,
which manages job scheduling and execution.
"""

import logging
import os
from typing import Dict, Any, Optional, List, Union
import uuid

from netraven.core.services.client.base_client import BaseClient, ServiceError

# Configure logging
logger = logging.getLogger(__name__)

class SchedulerClient(BaseClient):
    """
    Client for the Scheduler service.
    
    This class provides methods for scheduling and managing jobs
    through the Scheduler service.
    """
    
    def __init__(self, scheduler_url: Optional[str] = None, client_id: Optional[str] = None, timeout: int = 30):
        """
        Initialize the Scheduler client.
        
        Args:
            scheduler_url: URL of the Scheduler service (defaults to environment variable)
            client_id: Unique identifier for the client
            timeout: Request timeout in seconds
        """
        # Get the Scheduler URL from environment if not provided
        if scheduler_url is None:
            scheduler_url = os.environ.get("SCHEDULER_URL", "http://scheduler:8002")
        
        super().__init__(scheduler_url, client_id, timeout)
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for Scheduler requests.
        
        Returns:
            Dict with HTTP headers
        """
        headers = super()._get_headers()
        # Add authentication header here if needed
        # headers["Authorization"] = f"Bearer {token}"
        return headers
    
    async def schedule_job(
        self,
        job_type: str,
        params: Dict[str, Any],
        schedule_time: Optional[str] = None,
        job_id: Optional[str] = None,
        priority: int = 0,
        timeout: int = 3600,
        retries: int = 0
    ) -> Dict[str, Any]:
        """
        Schedule a job.
        
        Args:
            job_type: Type of job to schedule
            params: Job parameters
            schedule_time: When to run the job (ISO format, None for immediate)
            job_id: Custom job ID (generated if not provided)
            priority: Job priority (0-100, higher is more important)
            timeout: Job timeout in seconds
            retries: Number of retry attempts if job fails
            
        Returns:
            Dict containing job details
        """
        logger.debug(f"Scheduling {job_type} job via scheduler")
        
        # Generate job ID if not provided
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        data = {
            "job_id": job_id,
            "job_type": job_type,
            "params": params,
            "schedule_time": schedule_time,
            "priority": priority,
            "timeout": timeout,
            "retries": retries
        }
        
        try:
            result = await self._request("POST", "jobs", data=data)
            
            if result.get("status") == "success":
                logger.info(f"Job {job_id} scheduled successfully")
            else:
                logger.warning(f"Failed to schedule job: {result.get('message')}")
            
            return result
        except Exception as e:
            logger.error(f"Error scheduling job via scheduler: {str(e)}")
            raise
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dict containing job status
        """
        logger.debug(f"Getting status for job {job_id}")
        
        try:
            result = await self._request("GET", f"jobs/{job_id}")
            
            if result.get("status") == "success":
                logger.info(f"Retrieved status for job {job_id}")
            else:
                logger.warning(f"Failed to get job status: {result.get('message')}")
            
            return result
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            raise
    
    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled or running job.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            Dict containing cancellation result
        """
        logger.debug(f"Cancelling job {job_id}")
        
        try:
            result = await self._request("DELETE", f"jobs/{job_id}")
            
            if result.get("status") == "success":
                logger.info(f"Job {job_id} cancelled successfully")
            else:
                logger.warning(f"Failed to cancel job: {result.get('message')}")
            
            return result
        except Exception as e:
            logger.error(f"Error cancelling job: {str(e)}")
            raise
    
    async def schedule_backup_job(
        self,
        device_id: str,
        device_params: Dict[str, Any],
        schedule_time: Optional[str] = None,
        job_id: Optional[str] = None,
        priority: int = 0,
        timeout: int = 600,
        retries: int = 1
    ) -> Dict[str, Any]:
        """
        Schedule a device backup job.
        
        Args:
            device_id: ID of the device to back up
            device_params: Device connection parameters
            schedule_time: When to run the backup (ISO format, None for immediate)
            job_id: Custom job ID (generated if not provided)
            priority: Job priority (0-100, higher is more important)
            timeout: Job timeout in seconds
            retries: Number of retry attempts if job fails
            
        Returns:
            Dict containing job details
        """
        logger.debug(f"Scheduling backup job for device {device_id}")
        
        # Create job parameters
        params = {
            "device_id": device_id,
            "operation": "backup",
            **device_params
        }
        
        # Schedule the job
        return await self.schedule_job(
            job_type="device_backup",
            params=params,
            schedule_time=schedule_time,
            job_id=job_id,
            priority=priority,
            timeout=timeout,
            retries=retries
        ) 