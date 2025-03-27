"""
Service factory for NetRaven.

This module provides a centralized factory for creating and managing service instances.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from netraven.core.services.async_job_logging_service import AsyncJobLoggingService
from netraven.core.services.async_scheduler_service import AsyncSchedulerService
from netraven.core.services.async_device_comm_service import AsyncDeviceCommunicationService
from netraven.core.services.sensitive_data_filter import SensitiveDataFilter

class ServiceFactory:
    """
    Factory for creating and managing service instances.
    
    This class provides a centralized way to create and manage service instances,
    ensuring proper dependency injection and resource management.
    """
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Initialize the service factory.
        
        Args:
            db_session: Optional database session to use for services
        """
        self._db_session = db_session
        self._job_logging_service: Optional[AsyncJobLoggingService] = None
        self._scheduler_service: Optional[AsyncSchedulerService] = None
        self._device_comm_service: Optional[AsyncDeviceCommunicationService] = None
        self._sensitive_data_filter: Optional[SensitiveDataFilter] = None
    
    @property
    def job_logging_service(self) -> AsyncJobLoggingService:
        """
        Get the job logging service instance.
        
        Returns:
            AsyncJobLoggingService instance
        """
        if self._job_logging_service is None:
            self._job_logging_service = AsyncJobLoggingService(
                use_database=True,
                sensitive_data_filter=self.sensitive_data_filter
            )
        return self._job_logging_service
    
    @property
    def scheduler_service(self) -> AsyncSchedulerService:
        """
        Get the scheduler service instance.
        
        Returns:
            AsyncSchedulerService instance
        """
        if self._scheduler_service is None:
            self._scheduler_service = AsyncSchedulerService()
            # Set job logging service dependency
            self._scheduler_service.job_logging_service = self.job_logging_service
        return self._scheduler_service
    
    @property
    def device_comm_service(self) -> AsyncDeviceCommunicationService:
        """
        Get the device communication service instance.
        
        Returns:
            AsyncDeviceCommunicationService instance
        """
        if self._device_comm_service is None:
            self._device_comm_service = AsyncDeviceCommunicationService()
            # Set job logging service dependency
            self._device_comm_service.job_logging_service = self.job_logging_service
        return self._device_comm_service
    
    @property
    def sensitive_data_filter(self) -> SensitiveDataFilter:
        """
        Get the sensitive data filter instance.
        
        Returns:
            SensitiveDataFilter instance
        """
        if self._sensitive_data_filter is None:
            self._sensitive_data_filter = SensitiveDataFilter()
        return self._sensitive_data_filter
    
    async def close(self):
        """Close all service connections and cleanup resources."""
        if self._device_comm_service:
            await self._device_comm_service.close()
        
        if self._scheduler_service:
            await self._scheduler_service.stop()
        
        if self._db_session:
            await self._db_session.close()

# Global factory instance for FastAPI dependency injection
_service_factory: Optional[ServiceFactory] = None

def get_service_factory(db_session: Optional[AsyncSession] = None) -> ServiceFactory:
    """
    Get the global service factory instance.
    
    Args:
        db_session: Optional database session to use for services
        
    Returns:
        ServiceFactory instance
    """
    global _service_factory
    if _service_factory is None:
        _service_factory = ServiceFactory(db_session)
    return _service_factory 