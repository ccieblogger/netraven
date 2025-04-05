"""
Service factory for NetRaven.

This module provides a centralized factory for creating and managing service instances.
"""

from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
import asyncio
import logging # Added for logger
import os

# Core Services
from netraven.core.services.async_job_logging_service import AsyncJobLoggingService
from netraven.core.services.async_scheduler_service import AsyncSchedulerService
from netraven.core.services.async_device_comm_service import AsyncDeviceCommunicationService
from netraven.core.services.sensitive_data_filter import SensitiveDataFilter
from netraven.core.services.async_auth_service import AsyncAuthService # Import new service
from netraven.core.services.async_user_service import AsyncUserService # Import new service
from netraven.core.services.async_device_service import AsyncDeviceService # Import new service
from netraven.core.services.async_tag_service import AsyncTagService # Import new service
from netraven.core.services.async_tag_rule_service import AsyncTagRuleService # Import new service
from netraven.core.services.async_credential_service import AsyncCredentialService # Added import
from netraven.core.services.async_job_logs_service import AsyncJobLogsService # Add job logs service

# Token management service
from netraven.core.services.token.async_token_store import AsyncTokenStore, async_token_store

# Import our client interfaces
from netraven.core.services.client.gateway_client import GatewayClient
from netraven.core.services.client.scheduler_client import SchedulerClient

from netraven.core.job_logging import JobLogging # Assuming JobLogging exists
from netraven.core.scheduler import Scheduler # Assuming Scheduler exists
from netraven.core.device_comm import DeviceComm # Assuming DeviceComm exists
from netraven.core.notification_service import NotificationService # Assuming NotificationService exists
from netraven.core.credential_store import get_credential_store, CredentialStore # Added CredentialStore import
# from netraven.core.audit_service import AuditService # Keep commented out
# Web Services
from netraven.web.services.notification_service import NotificationService
# Keep AuditService import minimal for now due to sync issues
# from netraven.web.services.audit_service import AuditService

# DB Dependency
from netraven.web.database import get_async_session

# Import the refactored AsyncAuditService
from netraven.web.services.audit_service import AsyncAuditService

logger = logging.getLogger(__name__)


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
        # Core Services
        self._job_logging_service: Optional[AsyncJobLoggingService] = None
        self._scheduler_service: Optional[AsyncSchedulerService] = None
        self._device_comm_service: Optional[AsyncDeviceCommunicationService] = None
        self._sensitive_data_filter: Optional[SensitiveDataFilter] = None
        self._auth_service: Optional[AsyncAuthService] = None
        self._user_service: Optional[AsyncUserService] = None
        self._device_service: Optional[AsyncDeviceService] = None
        self._tag_service: Optional[AsyncTagService] = None
        self._tag_rule_service: Optional[AsyncTagRuleService] = None # Add tag rule service placeholder
        self._credential_service: Optional[AsyncCredentialService] = None # Added placeholder
        self._job_logs_service: Optional[AsyncJobLogsService] = None # Add job logs service placeholder
        self._token_store_service: Optional[AsyncTokenStore] = None # Add token store service
        
        # Client interfaces
        self._gateway_client: Optional[GatewayClient] = None
        self._scheduler_client: Optional[SchedulerClient] = None
        
        # Web Services
        self._audit_service: Optional[AsyncAuditService] = None # Placeholder for AsyncAuditService
        self._notification_service: Optional[NotificationService] = None
    
        # Initialize non-async or singleton services if needed immediately
        # Note: CredentialStore uses a singleton pattern via get_credential_store()
        self._credential_store_instance: CredentialStore = get_credential_store()
    
    # --- Core Service Properties ---
    
    @property
    def job_logging_service(self) -> AsyncJobLoggingService:
        """
        Get the job logging service instance.
        
        Returns:
            AsyncJobLoggingService instance
        """
        if self._job_logging_service is None:
            self._job_logging_service = AsyncJobLoggingService(
                use_database=True, # Assuming DB usage is desired
                sensitive_data_filter=self.sensitive_data_filter,
                db_session=self._db_session # Pass the session
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
            self._scheduler_service = AsyncSchedulerService(
                job_logging_service=self.job_logging_service,
                db_session=self._db_session, # Pass the session
                device_comm_service=self.device_comm_service # Pass device comm service
            )
        return self._scheduler_service
    
    @property
    def device_comm_service(self) -> AsyncDeviceCommunicationService:
        """
        Get the device communication service instance.
        
        Returns:
            AsyncDeviceCommunicationService instance
        """
        if self._device_comm_service is None:
            self._device_comm_service = AsyncDeviceCommunicationService(
                job_logging_service=self.job_logging_service,
                db_session=self._db_session # Pass the session
            )
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

    @property
    def token_store(self) -> AsyncTokenStore:
        """
        Get the token store instance.
        
        Returns:
            AsyncTokenStore instance
        """
        if self._token_store_service is None:
            # Use the global singleton instance
            self._token_store_service = async_token_store
        return self._token_store_service

    @property
    def auth_service(self) -> AsyncAuthService:
        """
        Get the authentication service instance.

        Returns:
            AsyncAuthService instance
        """
        if self._auth_service is None:
            self._auth_service = AsyncAuthService(
                db_session=self._db_session,
                audit_service=self.audit_service # Pass placeholder audit service
            )
        return self._auth_service

    @property
    def user_service(self) -> AsyncUserService:
        """
        Get the user management service instance.

        Returns:
            AsyncUserService instance
        """
        if self._user_service is None:
            self._user_service = AsyncUserService(
                db_session=self._db_session
            )
        return self._user_service
        
    @property
    def gateway_client(self) -> GatewayClient:
        """
        Get the Device Gateway client instance.
        
        Returns:
            GatewayClient instance
        """
        if self._gateway_client is None:
            # Get URL from environment if available
            gateway_url = os.environ.get("GATEWAY_URL", "http://device_gateway:8001")
            self._gateway_client = GatewayClient(gateway_url=gateway_url)
        return self._gateway_client
        
    @property
    def scheduler_client(self) -> SchedulerClient:
        """
        Get the Scheduler client instance.
        
        Returns:
            SchedulerClient instance
        """
        if self._scheduler_client is None:
            # Get URL from environment if available
            scheduler_url = os.environ.get("SCHEDULER_URL", "http://scheduler:8002")
            self._scheduler_client = SchedulerClient(scheduler_url=scheduler_url)
        return self._scheduler_client

    @property
    def device_service(self) -> AsyncDeviceService:
        """
        Get the device management service instance.

        Returns:
            AsyncDeviceService instance
        """
        if self._device_service is None:
            # Inject gateway and scheduler clients
            self._device_service = AsyncDeviceService(
                db_session=self._db_session,
                gateway_client=self.gateway_client,
                scheduler_client=self.scheduler_client
            )
        return self._device_service

    @property
    def tag_service(self) -> AsyncTagService:
        """
        Get the tag management service instance.

        Returns:
            AsyncTagService instance
        """
        if self._tag_service is None:
            self._tag_service = AsyncTagService(
                db_session=self._db_session 
            )
        return self._tag_service

    @property
    def tag_rule_service(self) -> AsyncTagRuleService:
        """
        Get the tag rule management service instance.

        Returns:
            AsyncTagRuleService instance
        """
        if self._tag_rule_service is None:
            # Inject necessary service dependencies
            self._tag_rule_service = AsyncTagRuleService(
                db_session=self._db_session,
                tag_service=self.tag_service,      # Inject TagService
                device_service=self.device_service # Inject DeviceService
            )
        return self._tag_rule_service
        
    @property
    def credential_store(self) -> CredentialStore:
        """Provides access to the singleton CredentialStore instance."""
        # Simply return the instance obtained during init
        # This avoids calling get_credential_store() repeatedly within the factory's lifecycle
        if self._credential_store_instance is None:
             # This should ideally not happen if __init__ ran correctly, but as a fallback:
             logger.warning("CredentialStore instance was None, re-initializing.")
             self._credential_store_instance = get_credential_store()
        return self._credential_store_instance

    @property
    def credential_service(self) -> AsyncCredentialService:
        """Provides an instance of the AsyncCredentialService."""
        if self._credential_service is None:
            logger.debug("Creating AsyncCredentialService instance.")
            self._credential_service = AsyncCredentialService(
                db_session=self._db_session,
                credential_store=self.credential_store, # Inject the singleton store instance
                tag_service=self.tag_service # Inject AsyncTagService via its property
            )
        return self._credential_service

    @property
    def job_logs_service(self) -> AsyncJobLogsService:
        """
        Get the job logs service instance.
        
        Returns:
            AsyncJobLogsService instance
        """
        if self._job_logs_service is None:
            self._job_logs_service = AsyncJobLogsService(
                db_session=self._db_session,
                job_logging_service=self.job_logging_service
            )
        return self._job_logs_service

    # --- Web Service Properties ---
    
    @property
    def notification_service(self) -> NotificationService:
        """
        Get the notification service instance.

        Returns:
            NotificationService instance
        """
        if self._notification_service is None:
            # NotificationService reads config from env vars, doesn't need db session
            self._notification_service = NotificationService()
        return self._notification_service

    @property
    def audit_service(self) -> AsyncAuditService:
        """
        Get the audit logging service instance.
        
        Returns:
            AsyncAuditService instance
        """
        if self._audit_service is None:
            if self._db_session is None:
                raise ValueError("Database session is required to initialize AsyncAuditService")
            self._audit_service = AsyncAuditService(self._db_session)
        return self._audit_service

    @property
    def rate_limiter(self) -> AsyncRateLimiter: # Assuming RateLimiter is needed
        """Get the rate limiter instance."""
        # Return the singleton instance directly for now
        # This could be made configurable later if needed
        from netraven.web.auth.rate_limiting import rate_limiter
        return rate_limiter
    
    async def close(self):
        """Close all service connections and cleanup resources."""
        # Close core services
        if self._device_comm_service:
            # Ensure close is awaited if it's async
            close_method = getattr(self._device_comm_service, "close", None)
            if asyncio.iscoroutinefunction(close_method):
                await close_method()
            elif callable(close_method):
                 close_method() # Call if sync
        
        if self._scheduler_service:
            # Ensure stop is awaited if it's async
            stop_method = getattr(self._scheduler_service, "stop", None)
            if asyncio.iscoroutinefunction(stop_method):
                await stop_method()
            elif callable(stop_method):
                 stop_method() # Call if sync
        
        # No close needed for NotificationService based on its init
        # No close needed for AuditService placeholder

        # Close DB session if the factory owns it (might be managed externally by FastAPI)
        # if self._db_session:
        #     await self._db_session.close()

# Global factory instance for FastAPI dependency injection
_service_factory: Optional[ServiceFactory] = None

def get_service_factory(db_session: AsyncSession = Depends(get_async_session)) -> ServiceFactory:
    """
    Get the global service factory instance, ensuring DB session is provided.
    Uses FastAPI's Depends to get the session per request.
    
    Args:
        db_session: Async database session dependency.
        
    Returns:
        ServiceFactory instance
    """
    # Create a new factory per request, injecting the request-specific db_session
    # This avoids issues with reusing sessions across requests if the old global pattern was used.
    return ServiceFactory(db_session)