"""
Job logs router for managing network job logs.

This module provides endpoints for creating, retrieving, updating, and
deleting job logs, as well as configuring retention policies and retrieving
job statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta

from netraven.web.database import get_async_session
from netraven.web.schemas.job_log import (
    JobLog,
    JobLogEntry,
    JobLogFilter,
    RetentionPolicyUpdate
)
from netraven.web.auth import UserPrincipal, get_current_principal
from netraven.web.auth.permissions import (
    require_scope, 
    require_admin, 
    require_job_log_access
)
from netraven.core.services.service_factory import ServiceFactory
from netraven.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/job-logs", tags=["job-logs"])

# Helper function to extract job log owner ID for permission checks
async def get_job_log_owner_id(
    job_log_id: str = Path(..., description="The ID of the job log"),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> str:
    """
    Extract the owner ID of a job log for permission checking.
    
    Args:
        job_log_id: The job log ID
        session: Database session
        factory: Service factory
        
    Returns:
        str: Owner ID of the job log
        
    Raises:
        HTTPException: If job log not found
    """
    job_log = await factory.job_logs_service.get_job_log(job_log_id)
    
    if not job_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job log with ID {job_log_id} not found"
        )
    
    return job_log.created_by

@router.get("/", response_model=List[JobLog])
async def list_job_logs(
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    principal: UserPrincipal = Depends(require_scope("read:job_logs")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> List[JobLog]:
    """
    List job logs with optional filtering.
    
    This endpoint requires the read:job_logs scope.
    Admin users can see all job logs, while regular users only see their own.
    """
    try:
        # Create filter params
        filter_params = JobLogFilter(
            device_id=device_id,
            status=status,
            job_type=job_type
        )
        
        # Get job logs from service
        job_logs = await factory.job_logs_service.list_job_logs(
            skip=offset,
            limit=limit,
            filter_params=filter_params,
            user_id=None if principal.is_admin else principal.id,
            is_admin=principal.is_admin
        )
        
        action = "list_all" if principal.is_admin else "list_own"
        logger.info(f"Access granted: user={principal.username}, resource=job_logs, action={action}, count={len(job_logs)}")
        return job_logs
    except Exception as e:
        logger.error(f"Error listing job logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing job logs: {str(e)}"
        )

@router.get("/{job_log_id}", response_model=Dict[str, Any])
async def get_job_log(
    job_log_id: str,
    include_entries: bool = Query(False, description="Whether to include log entries"),
    entry_limit: int = Query(100, gt=0, le=1000, description="Maximum number of entries to return"),
    principal: UserPrincipal = Depends(require_scope("read:job_logs")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_job_log_access(get_job_log_owner_id))
) -> Dict[str, Any]:
    """
    Get a specific job log with optional entries.
    
    This endpoint requires the read:job_logs scope and ownership of the job log
    or admin permissions.
    """
    try:
        if include_entries:
            # Get job log and entries
            job_log, entries = await factory.job_logs_service.get_job_log_with_entries(
                job_log_id=job_log_id,
                entry_limit=entry_limit
            )
        else:
            # Get just the job log
            job_log = await factory.job_logs_service.get_job_log(job_log_id=job_log_id)
            entries = []
        
        if job_log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job log with ID {job_log_id} not found"
            )
        
        # Convert to dictionary format for response
        job_log_dict = job_log.__dict__
        
        # Add entries if requested
        if include_entries:
            entries_list = []
            for entry in entries:
                entries_list.append(entry.__dict__)
            job_log_dict["entries"] = entries_list
        
        logger.info(f"Job log retrieved: id={job_log_id}, user={principal.username}")
        return job_log_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job log {job_log_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job log: {str(e)}"
        )

@router.get("/{job_log_id}/entries", response_model=List[Dict[str, Any]])
async def get_job_log_entries(
    job_log_id: str,
    limit: int = Query(100, gt=0, le=1000, description="Maximum number of entries to return"),
    principal: UserPrincipal = Depends(require_scope("read:job_logs")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_job_log_access(get_job_log_owner_id))
) -> List[Dict[str, Any]]:
    """
    Get entries for a specific job log.
    
    This endpoint requires the read:job_logs scope and ownership of the job log
    or admin permissions.
    """
    try:
        entries = await factory.job_logs_service.get_job_log_entries(
            job_log_id=job_log_id,
            limit=limit
        )
        
        if entries is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job log with ID {job_log_id} not found"
            )
        
        entries_list = []
        for entry in entries:
            entries_list.append(entry.__dict__)
        
        logger.info(f"Job log entries retrieved: log_id={job_log_id}, user={principal.username}, count={len(entries_list)}")
        return entries_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job log entries for {job_log_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job log entries: {str(e)}"
        )

@router.delete("/{job_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_log(
    job_log_id: str,
    principal: UserPrincipal = Depends(require_scope("delete:job_logs")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_job_log_access(get_job_log_owner_id))
):
    """
    Delete a job log.
    
    This endpoint requires the delete:job_logs scope and ownership of the job log
    or admin permissions.
    """
    try:
        result = await factory.job_logs_service.delete_job_log(job_log_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job log with ID {job_log_id} not found"
            )
        
        logger.info(f"Job log deleted: id={job_log_id}, user={principal.username}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job log {job_log_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting job log: {str(e)}"
        )

@router.post("/retention", status_code=status.HTTP_200_OK)
async def update_retention_policy(
    retention_policy: RetentionPolicyUpdate,
    principal: UserPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> Dict[str, Any]:
    """
    Update the job log retention policy.
    
    This endpoint requires admin permissions.
    """
    try:
        result = await factory.job_logs_service.update_retention_policy(
            days=retention_policy.days
        )
        
        logger.info(f"Retention policy updated: days={retention_policy.days}, user={principal.username}")
        return {
            "success": True,
            "message": f"Retention policy updated to {retention_policy.days} days",
            "days": retention_policy.days
        }
    except Exception as e:
        logger.error(f"Error updating retention policy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating retention policy: {str(e)}"
        )

@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_job_logs(
    days: Optional[int] = Query(None, description="Number of days to keep logs"),
    principal: UserPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> Dict[str, Any]:
    """
    Clean up old job logs.
    
    This endpoint requires admin permissions.
    """
    try:
        result = await factory.job_logs_service.cleanup_old_logs(days=days)
        
        days_msg = f"{days} days" if days else "default retention period"
        logger.info(f"Job logs cleanup executed: days={days_msg}, user={principal.username}, deleted_count={result.get('deleted_count', 0)}")
        
        return {
            "success": True,
            "message": f"Deleted {result.get('deleted_count', 0)} logs older than {days_msg}",
            "deleted_count": result.get("deleted_count", 0)
        }
    except Exception as e:
        logger.error(f"Error cleaning up job logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up job logs: {str(e)}"
        )

@router.get("/active", response_model=List[Dict[str, Any]])
async def list_active_jobs(
    principal: UserPrincipal = Depends(require_scope("read:job_logs")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> List[Dict[str, Any]]:
    """
    List active jobs.
    
    This endpoint requires the read:job_logs scope.
    Admin users can see all active jobs, while regular users only see their own.
    """
    try:
        # Retrieve active jobs from service
        active_jobs = await factory.job_logs_service.get_active_jobs(
            user_id=None if principal.is_admin else principal.id
        )
        
        # Convert to list of dictionaries
        result = []
        for job in active_jobs:
            result.append(job)
        
        action = "list_all" if principal.is_admin else "list_own"
        logger.info(f"Active jobs retrieved: user={principal.username}, action={action}, count={len(result)}")
        return result
    except Exception as e:
        logger.error(f"Error listing active jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing active jobs: {str(e)}"
        )

@router.get("/statistics", response_model=Dict[str, Any])
async def get_job_statistics(
    time_period: str = Query("day", description="Time period for statistics (day, week, month)"),
    principal: UserPrincipal = Depends(require_scope("read:job_logs")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> Dict[str, Any]:
    """
    Get job statistics.
    
    This endpoint requires the read:job_logs scope.
    Admin users can see statistics for all jobs, while regular users only see their own.
    """
    try:
        # Validate time period
        valid_periods = ["day", "week", "month"]
        if time_period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid time period. Must be one of: {', '.join(valid_periods)}"
            )
        
        # Calculate time range
        now = datetime.utcnow()
        if time_period == "day":
            start_time = now - timedelta(days=1)
        elif time_period == "week":
            start_time = now - timedelta(weeks=1)
        else:  # month
            start_time = now - timedelta(days=30)
        
        # Get statistics from service
        stats = await factory.job_logs_service.get_job_statistics(
            start_time=start_time,
            user_id=None if principal.is_admin else principal.id
        )
        
        action = "all_jobs" if principal.is_admin else "own_jobs"
        logger.info(f"Job statistics retrieved: user={principal.username}, period={time_period}, action={action}")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job statistics: {str(e)}"
        ) 