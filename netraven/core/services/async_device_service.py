"""
Asynchronous Device Management Service for NetRaven.

Handles CRUD operations for devices, manages tag associations,
interfaces with backup and reachability checks (via other services).
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # For eager loading tags
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from datetime import datetime # Ensure datetime is imported
import uuid # For generating fake job IDs

# Models and Schemas
from netraven.web.models.device import Device as DeviceModel
from netraven.web.schemas.device import DeviceCreate as DeviceCreateSchema, DeviceUpdate
from netraven.web.models.tag import Tag as TagModel # Needed for tag operations
from netraven.web.schemas.tag import Tag as TagSchema # Use schema for return type
from netraven.web.schemas.backup import Backup as BackupSchema # For list_backups return type hint

# Import our client interfaces
from netraven.core.services.client.gateway_client import GatewayClient
from netraven.core.services.client.scheduler_client import SchedulerClient

# Auth principal for type hinting
from netraven.web.auth import UserPrincipal

logger = logging.getLogger(__name__)

class AsyncDeviceService:
    """
    Provides methods for managing network device entities asynchronously.
    """

    def __init__(
        self, 
        db_session: AsyncSession,
        gateway_client: Optional[GatewayClient] = None,
        scheduler_client: Optional[SchedulerClient] = None
    ):
        """
        Initialize the device service.

        Args:
            db_session: Async database session.
            gateway_client: Client for the Device Gateway service.
            scheduler_client: Client for the Scheduler service.
        """
        self._db_session = db_session
        self._gateway_client = gateway_client
        self._scheduler_client = scheduler_client

    # --- Basic CRUD --- 

    async def get_device_by_id(self, device_id: str, include_tags: bool = True) -> Optional[DeviceModel]:
        """Fetches a device by its ID, optionally including tags."""
        # Placeholder for logic from crud.get_device
        stmt = select(DeviceModel).where(DeviceModel.id == device_id)
        if include_tags:
             # Eager load tags to avoid separate queries
            stmt = stmt.options(selectinload(DeviceModel.tags))
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_devices(self, owner_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[DeviceModel]:
        """Lists devices, optionally filtering by owner."""
        # Placeholder for logic from crud.get_devices
        stmt = select(DeviceModel).options(selectinload(DeviceModel.tags)).offset(skip).limit(limit)
        if owner_id:
            stmt = stmt.where(DeviceModel.owner_id == owner_id)
        result = await self._db_session.execute(stmt)
        return result.scalars().all()

    async def create_device(self, device_data: DeviceCreateSchema, owner_id: str) -> DeviceModel:
        """Creates a new device, handling tag associations."""
        # Placeholder for logic from crud.create_device and tag handling in router
        # 1. Check tag existence (if tag_ids provided)
        tag_ids = device_data.tag_ids or []
        tags_to_associate = []
        if tag_ids:
            # TODO: Need efficient way to check multiple tags exist (maybe get_tags_by_ids?)
            for tag_id in tag_ids:
                 tag = await self._get_tag_by_id(tag_id) # Assuming helper method
                 if not tag:
                      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tag with ID {tag_id} not found")
                 tags_to_associate.append(tag)
        
        # 2. Create device object
        db_device = DeviceModel(
            hostname=device_data.hostname,
            device_type=device_data.device_type,
            ip_address=device_data.ip_address,
            description=device_data.description,
            port=device_data.port,
            owner_id=owner_id,
            # TODO: Handle username/password - should these be stored directly?
            # SOT implies credentials should be managed separately via tags/store.
            # Need clarification on how direct credentials on DeviceCreate are handled.
            # For now, assume they are NOT stored directly on the device model.
        )
        
        # 3. Associate tags
        if tags_to_associate:
            db_device.tags.extend(tags_to_associate)
            
        # 4. Add, flush, refresh
        self._db_session.add(db_device)
        try:
            await self._db_session.flush()
            await self._db_session.refresh(db_device, attribute_names=['id', 'tags']) # Refresh ID and tags association
            # Need to explicitly refresh tags if relationship isn't automatically populated
            # Re-fetch might be safer if refresh doesn't populate correctly
            # db_device = await self.get_device_by_id(db_device.id, include_tags=True)
            return db_device
        except IntegrityError as e:
            await self._db_session.rollback()
            logger.error(f"DB integrity error creating device {device_data.hostname}: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Device {device_data.hostname} may already exist or invalid data provided.")
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error during device creation flush/refresh: {e}")
            raise
            
    async def update_device(self, device_id: str, device_data: Dict[str, Any]) -> Optional[DeviceModel]:
        """Updates an existing device."""
        # Placeholder for logic from crud.update_device
        db_device = await self.get_device_by_id(device_id, include_tags=False) # Don't need tags for update itself
        if not db_device:
            return None

        update_data = device_data
        for key, value in update_data.items():
            # TODO: Handle specific logic e.g., updating password/creds if allowed here?
            if hasattr(db_device, key):
                setattr(db_device, key, value)
            else:
                 logger.warning(f"Attempted to update non-existent attribute '{key}' on device {device_id}")
        try:
            await self._db_session.flush()
            await self._db_session.refresh(db_device)
            # Fetch again with tags if needed for response
            return await self.get_device_by_id(device_id, include_tags=True) 
        except Exception as e:
             await self._db_session.rollback()
             logger.error(f"Error during device update flush/refresh: {e}")
             raise

    async def delete_device(self, device_id: str) -> bool:
        """Deletes a device."""
        # Placeholder for logic from crud.delete_device
        db_device = await self.get_device_by_id(device_id, include_tags=False)
        if not db_device:
            return False
        
        await self._db_session.delete(db_device)
        try:
            await self._db_session.flush()
            return True
        except Exception as e:
             await self._db_session.rollback()
             logger.error(f"Error during device deletion flush: {e}")
             raise
             
    # --- Tag Management --- 
    async def _get_tag_by_id(self, tag_id: str) -> Optional[TagModel]:
        stmt = select(TagModel).where(TagModel.id == tag_id)
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_device_tags(self, device_id: str) -> List[TagModel]:
        """Retrieves all tags associated with a specific device."""
        # Placeholder for logic from crud.get_tags_for_device
        # Ensure tags are loaded when fetching the device
        device = await self.get_device_by_id(device_id, include_tags=True)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        return device.tags # Return the loaded tags

    async def assign_tag_to_device(self, device_id: str, tag_id: str) -> bool:
        """Assigns an existing tag to a device."""
        # Placeholder for logic from crud.add_tag_to_device
        device = await self.get_device_by_id(device_id, include_tags=True) # Load tags to check if already present
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
            
        tag = await self._get_tag_by_id(tag_id)
        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
        
        # Check if tag is already assigned
        if tag in device.tags:
            logger.info(f"Tag {tag_id} already assigned to device {device_id}. No action taken.")
            return True # Idempotent: consider assignment successful
            
        device.tags.append(tag)
        try:
            await self._db_session.flush()
            return True
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error assigning tag {tag_id} to device {device_id}: {e}")
            # Consider specific service exception
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to assign tag")
            
    async def remove_tag_from_device(self, device_id: str, tag_id: str) -> bool:
        """Removes a tag association from a device."""
        # Placeholder for logic from crud.remove_tag_from_device
        device = await self.get_device_by_id(device_id, include_tags=True)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        
        tag_to_remove = None
        for tag in device.tags:
            if tag.id == tag_id:
                tag_to_remove = tag
                break
        
        if not tag_to_remove:
            logger.warning(f"Tag {tag_id} not found on device {device_id}. Cannot remove.")
            return False # Indicate tag was not found on device
        
        device.tags.remove(tag_to_remove)
        try:
            await self._db_session.flush()
            return True
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error removing tag {tag_id} from device {device_id}: {e}")
            # Consider specific service exception
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove tag")
    
    # --- Device Operations --- 
    
    async def check_reachability(self, device_id: str, principal: UserPrincipal) -> Dict[str, Any]:
        """
        Checks if a device is reachable using the Device Gateway service.
        
        Args:
            device_id: ID of the device to check
            principal: User principal for logging
            
        Returns:
            Dict containing reachability status
            
        Raises:
            HTTPException: If device not found or gateway communication fails
        """
        if not self._gateway_client:
            logger.error(f"Gateway client not available for reachability check of device {device_id}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Device Gateway service not available"
            )
            
        # Get device details
        device = await self.get_device_by_id(device_id, include_tags=True)
        if not device:
            logger.warning(f"Device {device_id} not found for reachability check")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
            
        # Get credentials from tags or other source
        # This is a placeholder - in reality, you would need to fetch credentials
        # from the credential store or from tags
        try:
            # Extract credentials (placeholder - actual implementation would depend on your credential management)
            # In a real implementation, you would get the credentials from a secure store or from tags
            username = "admin"  # placeholder
            password = "admin"  # placeholder
            
            # Call Gateway service to check reachability
            result = await self._gateway_client.check_device_reachability(
                host=device.ip_address,
                username=username,
                password=password,
                device_type=device.device_type,
                port=device.port
            )
            
            # Process result
            reachable = result.get("data", {}).get("reachable", False)
            
            # Update device status if needed
            # device.last_reachability_check = datetime.utcnow()
            # device.is_reachable = reachable
            # await self._db_session.flush()
            
            logger.info(f"Reachability check for device {device_id} completed: {'Reachable' if reachable else 'Unreachable'}")
            
            return {
                "device_id": device_id,
                "hostname": device.hostname,
                "reachable": reachable,
                "message": "Reachability check successful",
                "checked_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking reachability for device {device_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error checking device reachability: {str(e)}"
            )
    
    async def trigger_backup(self, device_id: str, principal: UserPrincipal) -> Dict[str, Any]:
        """
        Initiates a backup job for the device using the Scheduler service.
        
        Args:
            device_id: ID of the device to back up
            principal: User principal for logging
            
        Returns:
            Dict containing job details
            
        Raises:
            HTTPException: If device not found or scheduler communication fails
        """
        if not self._scheduler_client:
            logger.error(f"Scheduler client not available for backup of device {device_id}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scheduler service not available"
            )
            
        # Get device details
        device = await self.get_device_by_id(device_id, include_tags=True)
        if not device:
            logger.warning(f"Device {device_id} not found for backup")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
            
        try:
            # Extract credentials (placeholder - actual implementation would depend on your credential management)
            # In a real implementation, you would get the credentials from a secure store or from tags
            device_params = {
                "host": device.ip_address,
                "username": "admin",  # placeholder
                "password": "admin",  # placeholder
                "device_type": device.device_type,
                "port": device.port
            }
            
            # Call Scheduler service to schedule backup job
            job_id = f"backup_{device_id}_{uuid.uuid4()}"
            result = await self._scheduler_client.schedule_backup_job(
                device_id=device_id,
                device_params=device_params,
                job_id=job_id
            )
            
            logger.info(f"Backup job {job_id} scheduled for device {device_id}")
            
            return {
                "job_id": job_id,
                "device_id": device_id,
                "message": "Backup job submitted successfully",
                "scheduled_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling backup for device {device_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error scheduling device backup: {str(e)}"
            )

    async def list_backups(self, device_id: str, limit: int, offset: int, principal: UserPrincipal) -> List[BackupSchema]:
        """Lists backups for a specific device using the appropriate service."""
        # Verify device exists
        device = await self.get_device_by_id(device_id, include_tags=False)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
            
        # This would normally call an appropriate service to retrieve backups
        # For now, return an empty list as this is a placeholder
        logger.info(f"Listing backups for device {device_id} (limit={limit}, offset={offset})")
        return []

    async def update_device_backup_status(
        self,
        device_id: str,
        status: str,
        timestamp: datetime,
        message: Optional[str] = None
    ) -> Optional[DeviceModel]:
        """Updates the last backup status on the device model. (Placeholder/Partial)"""
        # This is closer to a CRUD operation, so partially implement DB update
        db_device = await self.get_device_by_id(device_id, include_tags=False)
        if not db_device:
            logger.error(f"Cannot update backup status: Device {device_id} not found.")
            return None

        db_device.last_backup_status = status
        db_device.last_backup_at = timestamp
        # Potentially store message elsewhere if needed, DeviceModel doesn't have it.
        
        try:
            await self._db_session.flush()
            await self._db_session.refresh(db_device)
            logger.info(f"Updated backup status for device {device_id} to {status}")
            return db_device
        except Exception as e:
             await self._db_session.rollback()
             logger.error(f"Error updating backup status for device {device_id}: {e}")
             # Don't raise HTTPException here, as this might be called internally
             return None
    
    # --- Other Operations ---
    async def check_reachability(self, device_id: str, principal: UserPrincipal) -> Dict[str, Any]:
        """Checks if a device is reachable. (Placeholder)"""
        # TODO (Phase 3): Implement interaction with Device Communication Service.
        device = await self.get_device_by_id(device_id, include_tags=False)
        if not device:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        # Add permission checks

        logger.info(f"Placeholder: Checking reachability for device {device_id} requested by {principal.username}")
        # Return fake status
        return {"device_id": device_id, "hostname": device.hostname, "reachable": True, "message": "Placeholder: Reachability check successful"}
