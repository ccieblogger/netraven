"""
Asynchronous Job Logs Service for NetRaven.

This service provides functionality for retrieving, managing, and analyzing job logs,
including historical job data, statistics, and retention policy management.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_, desc, text
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from netraven.web.models.job_log import JobLog as JobLogModel, JobLogEntry as JobLogEntryModel
from netraven.web.models.device import Device as DeviceModel
from netraven.web.schemas.job_log import JobLogFilter, RetentionPolicyUpdate
from netraven.core.services.async_job_logging_service import AsyncJobLoggingService

logger = logging.getLogger(__name__)

class AsyncJobLogsService:
    """
    Service for managing job logs in NetRaven.
    Provides methods for retrieving, analyzing, and managing job log data.
    """
    
    def __init__(self, db_session: AsyncSession, job_logging_service: AsyncJobLoggingService):
        """
        Initialize the job logs service.
        
        Args:
            db_session: Async database session
            job_logging_service: The job logging service for active job operations
        """
        self._db_session = db_session
        self._job_logging_service = job_logging_service
    
    async def list_job_logs(
        self, 
        skip: int = 0, 
        limit: int = 10, 
        filter_params: Optional[JobLogFilter] = None,
        user_id: Optional[str] = None,
        is_admin: bool = False
    ) -> List[JobLogModel]:
        """
        List job logs with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filter_params: Optional filtering parameters
            user_id: Optional user ID for access control
            is_admin: Whether the requesting user is an admin
            
        Returns:
            List[JobLogModel]: List of job logs
        """
        logger.debug(f"Listing job logs: skip={skip}, limit={limit}, filter_params={filter_params}")
        
        # Start with base query
        query = select(JobLogModel).order_by(desc(JobLogModel.start_time))
        
        # Apply filters if provided
        if filter_params:
            conditions = []
            
            if filter_params.device_id:
                conditions.append(JobLogModel.device_id == filter_params.device_id)
            
            if filter_params.status:
                conditions.append(JobLogModel.status == filter_params.status)
            
            if filter_params.job_type:
                conditions.append(JobLogModel.job_type == filter_params.job_type)
                
            if conditions:
                query = query.where(and_(*conditions))
        
        # Apply access control filter if not admin
        if not is_admin and user_id:
            # Join with device to check ownership
            query = query.outerjoin(DeviceModel, JobLogModel.device_id == DeviceModel.id)
            query = query.where(
                or_(
                    JobLogModel.created_by == user_id,  # User created the job
                    DeviceModel.owner_id == user_id,    # User owns the device
                    JobLogModel.device_id.is_(None)     # Job not associated with a device
                )
            )
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self._db_session.execute(query)
        job_logs = result.scalars().all()
        
        logger.debug(f"Found {len(job_logs)} job logs")
        return job_logs
    
    async def get_job_log(self, job_log_id: str) -> Optional[JobLogModel]:
        """
        Get a specific job log by ID.
        
        Args:
            job_log_id: ID of the job log
            
        Returns:
            Optional[JobLogModel]: The job log if found, None otherwise
        """
        logger.debug(f"Getting job log: {job_log_id}")
        
        query = select(JobLogModel).where(JobLogModel.id == job_log_id)
        result = await self._db_session.execute(query)
        job_log = result.scalar_one_or_none()
        
        return job_log
    
    async def get_job_log_entries(self, job_log_id: str, limit: int = 100) -> List[JobLogEntryModel]:
        """
        Get entries for a specific job log.
        
        Args:
            job_log_id: ID of the job log
            limit: Maximum number of entries to return
            
        Returns:
            List[JobLogEntryModel]: List of job log entries
        """
        logger.debug(f"Getting job log entries: job_log_id={job_log_id}, limit={limit}")
        
        query = (
            select(JobLogEntryModel)
            .where(JobLogEntryModel.job_log_id == job_log_id)
            .order_by(JobLogEntryModel.timestamp)
            .limit(limit)
        )
        
        result = await self._db_session.execute(query)
        entries = result.scalars().all()
        
        logger.debug(f"Found {len(entries)} entries")
        return entries
    
    async def get_job_log_with_entries(
        self, 
        job_log_id: str, 
        entry_limit: int = 100
    ) -> Tuple[Optional[JobLogModel], List[JobLogEntryModel]]:
        """
        Get a job log and its entries.
        
        Args:
            job_log_id: ID of the job log
            entry_limit: Maximum number of entries to return
            
        Returns:
            Tuple[Optional[JobLogModel], List[JobLogEntryModel]]: 
                The job log and its entries
        """
        job_log = await self.get_job_log(job_log_id)
        
        if job_log is None:
            return None, []
        
        entries = await self.get_job_log_entries(job_log_id, entry_limit)
        return job_log, entries
    
    async def delete_job_log(self, job_log_id: str) -> bool:
        """
        Delete a job log.
        
        Args:
            job_log_id: ID of the job log
            
        Returns:
            bool: True if the log was deleted, False otherwise
        """
        logger.debug(f"Deleting job log: {job_log_id}")
        
        job_log = await self.get_job_log(job_log_id)
        
        if job_log is None:
            logger.warning(f"Job log not found: {job_log_id}")
            return False
        
        # Delete related entries first
        await self._db_session.execute(
            text(f"DELETE FROM job_log_entries WHERE job_log_id = '{job_log_id}'")
        )
        
        # Then delete the job log
        await self._db_session.delete(job_log)
        await self._db_session.flush()
        
        logger.info(f"Job log deleted: {job_log_id}")
        return True
    
    async def update_retention_policy(
        self, 
        retention_days: int,
        job_type: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update retention policy for job logs.
        
        Args:
            retention_days: Number of days to retain logs
            job_type: Optional job type to apply policy to
            device_id: Optional device ID to apply policy to
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        logger.debug(f"Updating retention policy: days={retention_days}, job_type={job_type}, device_id={device_id}")
        
        if retention_days < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Retention days must be at least 1"
            )
        
        # Build query to update logs
        query = select(JobLogModel)
        
        conditions = []
        if job_type:
            conditions.append(JobLogModel.job_type == job_type)
        
        if device_id:
            conditions.append(JobLogModel.device_id == device_id)
            
        if conditions:
            query = query.where(and_(*conditions))
            
        result = await self._db_session.execute(query)
        logs = result.scalars().all()
        
        # Update retention days for each log
        count = 0
        for log in logs:
            log.retention_days = retention_days
            count += 1
        
        await self._db_session.flush()
        
        return {
            "updated_count": count,
            "retention_days": retention_days,
            "job_type": job_type,
            "device_id": device_id
        }
    
    async def cleanup_old_logs(self, days: Optional[int] = None) -> Dict[str, Any]:
        """
        Delete old job logs based on retention policy.
        
        Args:
            days: Optional override for retention days
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        logger.debug(f"Cleaning up old logs: days={days}")
        
        deleted_count = 0
        
        if days is not None:
            # Delete logs older than specified days
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # First get the logs to delete
            query = select(JobLogModel).where(JobLogModel.start_time < cutoff_date)
            result = await self._db_session.execute(query)
            logs_to_delete = result.scalars().all()
            
            # Delete entries for each log
            for log in logs_to_delete:
                await self._db_session.execute(
                    text(f"DELETE FROM job_log_entries WHERE job_log_id = '{log.id}'")
                )
                await self._db_session.delete(log)
                deleted_count += 1
        else:
            # Use retention policy for each log
            current_date = datetime.utcnow()
            
            # Get all logs
            query = select(JobLogModel)
            result = await self._db_session.execute(query)
            all_logs = result.scalars().all()
            
            # Check each log against its retention policy
            for log in all_logs:
                if log.retention_days and log.start_time:
                    cutoff_date = log.start_time + timedelta(days=log.retention_days)
                    if current_date > cutoff_date:
                        # Delete log entries
                        await self._db_session.execute(
                            text(f"DELETE FROM job_log_entries WHERE job_log_id = '{log.id}'")
                        )
                        await self._db_session.delete(log)
                        deleted_count += 1
        
        await self._db_session.flush()
        
        return {
            "deleted_count": deleted_count,
            "days": days
        }
    
    async def get_active_jobs(self) -> List[Dict[str, Any]]:
        """
        Get list of currently active jobs.
        
        Returns:
            List[Dict[str, Any]]: List of active jobs
        """
        logger.debug("Getting active jobs")
        
        # Get active jobs from the job tracking service
        active_jobs = self._job_logging_service.get_active_sessions()
        
        # Convert to list of dictionaries
        result = []
        for session_id, job_info in active_jobs.items():
            result.append({
                "session_id": session_id,
                "job_type": job_info.get("job_type"),
                "start_time": job_info.get("start_time"),
                "device_id": job_info.get("device_id"),
                "status": job_info.get("status", "running"),
                "progress": job_info.get("progress", 0),
                "details": job_info.get("details", {})
            })
        
        return result
    
    async def get_job_statistics(self, time_period: str = "day") -> Dict[str, Any]:
        """
        Get job statistics for a given time period.
        
        Args:
            time_period: Time period for statistics (day, week, month)
            
        Returns:
            Dict[str, Any]: Job statistics
        """
        logger.debug(f"Getting job statistics: period={time_period}")
        
        # Determine date range based on time period
        end_date = datetime.utcnow()
        
        if time_period == "day":
            start_date = end_date - timedelta(days=1)
        elif time_period == "week":
            start_date = end_date - timedelta(weeks=1)
        elif time_period == "month":
            start_date = end_date - timedelta(days=30)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid time period. Must be 'day', 'week', or 'month'."
            )
        
        # Get total count of jobs in period
        query = select(func.count(JobLogModel.id)).where(
            JobLogModel.start_time.between(start_date, end_date)
        )
        result = await self._db_session.execute(query)
        total_count = result.scalar_one() or 0
        
        # Get success count
        query = select(func.count(JobLogModel.id)).where(
            JobLogModel.start_time.between(start_date, end_date),
            JobLogModel.status == "success"
        )
        result = await self._db_session.execute(query)
        success_count = result.scalar_one() or 0
        
        # Get failure count
        query = select(func.count(JobLogModel.id)).where(
            JobLogModel.start_time.between(start_date, end_date),
            JobLogModel.status == "failed"
        )
        result = await self._db_session.execute(query)
        failure_count = result.scalar_one() or 0
        
        # Get in-progress count
        query = select(func.count(JobLogModel.id)).where(
            JobLogModel.start_time.between(start_date, end_date),
            JobLogModel.status == "running"
        )
        result = await self._db_session.execute(query)
        running_count = result.scalar_one() or 0
        
        # Get count by job type
        query = select(
            JobLogModel.job_type,
            func.count(JobLogModel.id).label("count")
        ).where(
            JobLogModel.start_time.between(start_date, end_date)
        ).group_by(
            JobLogModel.job_type
        )
        result = await self._db_session.execute(query)
        by_type_counts = {row[0]: row[1] for row in result.all()}
        
        return {
            "time_period": time_period,
            "start_date": start_date,
            "end_date": end_date,
            "total_count": total_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "running_count": running_count,
            "by_type": by_type_counts
        } 