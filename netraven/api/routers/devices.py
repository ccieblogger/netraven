from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from netraven.api import schemas # Import schemas module
from netraven.api.dependencies import get_db_session, get_current_active_user, require_admin_role # Import dependencies
from netraven.db import models # Import DB models

router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
    dependencies=[Depends(get_current_active_user)] # Apply auth to all device routes
)

# Helper function to get tags by ID (used in create/update)
def get_tags_by_ids(db: Session, tag_ids: List[int]) -> List[models.Tag]:
    tags = db.query(models.Tag).filter(models.Tag.id.in_(tag_ids)).all()
    if len(tags) != len(tag_ids):
        # Find which IDs were not found
        found_ids = {tag.id for tag in tags}
        missing_ids = [tag_id for tag_id in tag_ids if tag_id not in found_ids]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag(s) not found: {missing_ids}")
    return tags

@router.post("/", response_model=schemas.device.Device, status_code=status.HTTP_201_CREATED)
def create_device(
    device: schemas.device.DeviceCreate,
    db: Session = Depends(get_db_session),
    # current_user: models.User = Depends(get_current_active_user) # Inject user if needed for ownership etc.
):
    """Create a new network device."""
    # Check if hostname or IP already exists
    existing_device = db.query(models.Device).filter(
        (models.Device.hostname == device.hostname) | (models.Device.ip_address == str(device.ip_address))
    ).first()
    if existing_device:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hostname or IP address already registered")

    db_device = models.Device(**device.model_dump(exclude={'tags'})) # Use model_dump in Pydantic v2
    
    # Handle tags if provided
    if device.tags:
        tags = get_tags_by_ids(db, device.tags)
        db_device.tags = tags

    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@router.get("/", response_model=List[schemas.device.Device])
def list_devices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Retrieve a list of network devices."""
    devices = (
        db.query(models.Device)
        .options(selectinload(models.Device.tags)) # Eager load tags
        .offset(skip)
        .limit(limit)
        .all()
    )
    return devices

@router.get("/{device_id}", response_model=schemas.device.Device)
def get_device(
    device_id: int,
    db: Session = Depends(get_db_session)
):
    """Retrieve a specific network device by ID."""
    db_device = (
        db.query(models.Device)
        .options(selectinload(models.Device.tags))
        .filter(models.Device.id == device_id)
        .first()
    )
    if db_device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return db_device

@router.put("/{device_id}", response_model=schemas.device.Device)
def update_device(
    device_id: int,
    device: schemas.device.DeviceUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a network device."""
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if db_device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    update_data = device.model_dump(exclude_unset=True) # Get only fields that were set

    # Check for potential conflicts if hostname/IP are being changed
    if 'hostname' in update_data and update_data['hostname'] != db_device.hostname:
        if db.query(models.Device).filter(models.Device.hostname == update_data['hostname']).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hostname already exists")
    if 'ip_address' in update_data and str(update_data['ip_address']) != db_device.ip_address:
         if db.query(models.Device).filter(models.Device.ip_address == str(update_data['ip_address'])).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="IP address already exists")

    # Update simple attributes
    for key, value in update_data.items():
        if key != "tags": # Handle tags separately
            setattr(db_device, key, value)

    # Handle tags update
    if "tags" in update_data:
        if update_data["tags"] is None: # Explicitly setting tags to empty list
             db_device.tags = []
        else:
            tags = get_tags_by_ids(db, update_data["tags"])
            db_device.tags = tags

    db.commit()
    db.refresh(db_device)
    # Eager load tags again for the response model
    db.query(models.Device).options(selectinload(models.Device.tags)).filter(models.Device.id == device_id).first()
    return db_device

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db_session),
    #_: models.User = Depends(require_admin_role) # Example: Protect deletion
):
    """Delete a network device."""
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if db_device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    db.delete(db_device)
    db.commit()
    return None # Return None for 204 status
