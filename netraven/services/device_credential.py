"""Device credential matching service.

This module provides services for matching network device credentials based on tags.
It implements the core logic for finding appropriate credentials for devices,
which is vital for secure and efficient device connections.

The credential matching system uses device tags to identify which credentials
should be used for a particular device, allowing for flexible credential management
across the network infrastructure.
"""

from typing import List
from sqlalchemy.orm import Session, selectinload

from netraven.db import models

def get_matching_credentials_for_device(db: Session, device_id: int) -> List[models.Credential]:
    """
    Get all credentials that match a device's tags, ordered by priority.
    
    Returns an empty list if no credentials match or the device has no tags.
    
    Args:
        db: Database session
        device_id: ID of the device to find credentials for
        
    Returns:
        List of matching credentials ordered by priority (lower number = higher priority)
    """
    # Get the device with its tags
    device = (
        db.query(models.Device)
        .options(selectinload(models.Device.tags))
        .filter(models.Device.id == device_id)
        .first()
    )
    
    if not device or not device.tags:
        return []
        
    # Get tag IDs for the device
    device_tag_ids = [tag.id for tag in device.tags]
    
    # Find all credentials that share at least one tag with the device
    # Order by priority (lower number = higher priority)
    matching_credentials = (
        db.query(models.Credential)
        .options(selectinload(models.Credential.tags))
        .join(models.Credential.tags)
        .filter(models.Tag.id.in_(device_tag_ids))
        .order_by(models.Credential.priority)
        .distinct()
        .all()
    )
    
    return matching_credentials 