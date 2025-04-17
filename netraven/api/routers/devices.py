"""Device management router for network device operations.

This module provides API endpoints for managing network devices in the system,
implementing RESTful CRUD operations (Create, Read, Update, Delete) for device resources.
The router handles operations including:

- Device registration with validation for unique hostname/IP address
- Device listing with filtering and pagination capabilities
- Individual device retrieval, modification, and deletion
- Tag management for device categorization
- Credential management and association with devices

Each endpoint enforces appropriate access controls and validation to ensure
data integrity and security. Device information is persisted in the database
through SQLAlchemy ORM models.

Security:
- All endpoints require authentication via the get_current_active_user dependency
- Certain operations may require elevated privileges (admin role)

Relationships:
- Devices can be associated with multiple tags for grouping and filtering
- Devices can be matched with credentials based on tag associations
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, and_, func

from netraven.api import schemas # Import schemas module
from netraven.api.dependencies import get_db_session, get_current_active_user, require_admin_role # Import dependencies
from netraven.db import models # Import DB models
from netraven.services.device_credential import get_matching_credentials_for_device

# Constants
DEFAULT_TAG_NAME = "default"

router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
    dependencies=[Depends(get_current_active_user)] # Apply auth to all device routes
)

# Helper function to get tags by ID (used in create/update)
def get_tags_by_ids(db: Session, tag_ids: List[int]) -> List[models.Tag]:
    """Retrieve tags by their IDs from the database.
    
    Args:
        db (Session): Database session for executing queries
        tag_ids (List[int]): List of tag IDs to retrieve
        
    Returns:
        List[models.Tag]: List of Tag model objects matching the provided IDs
        
    Raises:
        HTTPException (404): If any requested tag IDs cannot be found in the database,
                            including details about which specific IDs were missing
    """
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
    """Create a new network device in the system.
    
    Args:
        device (schemas.device.DeviceCreate): Device creation schema containing required device attributes
                                             and optional tag associations
        db (Session): Database session for executing queries
        
    Returns:
        models.Device: The newly created device object with all properties and relationships populated
        
    Raises:
        HTTPException (400): If the hostname or IP address is already registered to another device
        HTTPException (404): If any of the specified tag IDs don't exist in the database
        
    Notes:
        - Automatically adds the default tag to the device if it exists
        - Ensures device hostname and IP address are unique across the system
        - Returns a 201 Created status code upon successful creation
    """
    # Check if hostname or IP already exists
    existing_device = db.query(models.Device).filter(
        (models.Device.hostname == device.hostname) | (models.Device.ip_address == str(device.ip_address))
    ).first()
    if existing_device:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hostname or IP address already registered")

    # Create a dict with device data and explicitly convert IP to string
    device_data = device.model_dump(exclude={'tags'})
    device_data['ip_address'] = str(device_data['ip_address'])
    
    # Create the device instance with the updated data
    db_device = models.Device(**device_data)
    
    # Handle tags if provided
    tag_ids = device.tags or []
    
    # Get the default tag
    default_tag = db.query(models.Tag).filter(models.Tag.name == DEFAULT_TAG_NAME).first()
    
    # If default tag exists and not already in the list, add it
    if default_tag and default_tag.id not in tag_ids:
        tag_ids.append(default_tag.id)
    
    if tag_ids:
        tags = get_tags_by_ids(db, tag_ids)
        db_device.tags = tags

    db.add(db_device)
    db.commit()
    db.refresh(db_device)

    # --- Ensure at least one credential is associated ---
    matching_credentials = get_matching_credentials_for_device(db, db_device.id)
    if not matching_credentials:
        # Try to add the default tag if not already present
        default_tag = db.query(models.Tag).filter(models.Tag.name == DEFAULT_TAG_NAME).first()
        if not default_tag:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No credentials match this device and the default tag does not exist. Please create a default tag and credential.")
        if default_tag not in db_device.tags:
            db_device.tags.append(default_tag)
            db.commit()
            db.refresh(db_device)
            # Re-check credentials
            matching_credentials = get_matching_credentials_for_device(db, db_device.id)
        if not matching_credentials:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No credentials match this device, even after associating the default tag. Please check your credential configuration.")
    return db_device

@router.get("/", response_model=schemas.device.PaginatedDeviceResponse)
def list_devices(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    hostname: Optional[str] = None,
    ip_address: Optional[str] = None,
    device_type: Optional[str] = None,
    tag_id: Optional[List[int]] = Query(None, description="Filter by tag IDs"),
    db: Session = Depends(get_db_session)
):
    """Retrieve a paginated and filtered list of network devices.
    
    Args:
        page (int): Page number for pagination, starting at 1
        size (int): Number of items per page, between 1 and 100
        hostname (Optional[str]): Filter devices by partial hostname match
        ip_address (Optional[str]): Filter devices by partial IP address match
        device_type (Optional[str]): Filter devices by exact device type match
        tag_id (Optional[List[int]]): Filter devices that have any of the specified tag IDs
        db (Session): Database session for executing queries
        
    Returns:
        Dict: Paginated response containing:
            - items (List[Dict]): List of device objects with tags and credential counts
            - total (int): Total number of devices matching the filters
            - page (int): Current page number
            - size (int): Number of items per page
            - pages (int): Total number of pages available
            
    Notes:
        - Filtering is applied as AND conditions between different filter types
        - Tag filtering supports multiple tags (devices with ANY of the specified tags)
        - Each device includes a count of matching credentials for connection management
    """
    query = db.query(models.Device).options(selectinload(models.Device.tags))
    
    # Apply filters
    filters = []
    if hostname:
        filters.append(models.Device.hostname.ilike(f"%{hostname}%"))
    if ip_address:
        filters.append(models.Device.ip_address.ilike(f"%{ip_address}%"))
    if device_type:
        filters.append(models.Device.device_type == device_type)
    
    # Apply all filters
    if filters:
        query = query.filter(and_(*filters))
    
    # Apply tag filter if specified
    if tag_id:
        query = query.join(models.Device.tags).filter(models.Tag.id.in_(tag_id)).group_by(models.Device.id)
    
    # Get total count for pagination
    total = query.count()
    
    # Calculate pagination values
    pages = (total + size - 1) // size
    offset = (page - 1) * size
    
    # Get paginated devices
    devices = query.offset(offset).limit(size).all()
    
    # Enhance with credential counts
    device_list = []
    for device in devices:
        # Convert SQLAlchemy model to dictionary
        device_dict = {
            column.name: getattr(device, column.name)
            for column in device.__table__.columns
        }
        
        # Add tags relationship
        device_dict["tags"] = device.tags
        
        # Get matching credential count using the service function
        matching_credentials = get_matching_credentials_for_device(db, device.id)
        device_dict["matching_credentials_count"] = len(matching_credentials)
        
        device_list.append(device_dict)
    
    # Return paginated response
    return {
        "items": device_list,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/{device_id}", response_model=schemas.device.Device)
def get_device(
    device_id: int,
    db: Session = Depends(get_db_session)
):
    """Retrieve a specific network device by ID.
    
    Args:
        device_id (int): Unique identifier of the device to retrieve
        db (Session): Database session for executing queries
        
    Returns:
        models.Device: Device object with all properties and relationships (including tags)
        
    Raises:
        HTTPException (404): If no device exists with the specified ID
    """
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
    """Update an existing network device.
    
    Args:
        device_id (int): Unique identifier of the device to update
        device (schemas.device.DeviceUpdate): Update schema containing fields to modify
        db (Session): Database session for executing queries
        
    Returns:
        models.Device: Updated device object with all properties and relationships refreshed
        
    Raises:
        HTTPException (404): If no device exists with the specified ID
        HTTPException (400): If attempting to change hostname to one that already exists
        HTTPException (400): If attempting to change IP address to one that already exists
        HTTPException (404): If any of the specified tag IDs don't exist in the database
        
    Notes:
        - Only fields explicitly set in the request body will be updated
        - Setting tags to null or [] will remove all tag associations
        - Uniqueness constraints are enforced for hostname and IP address
    """
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

    # Convert IP address to string if present
    if 'ip_address' in update_data:
        update_data['ip_address'] = str(update_data['ip_address'])

    # Update simple attributes
    for key, value in update_data.items():
        if key != "tags": # Handle tags separately
            setattr(db_device, key, value)

    # Handle tags update
    if "tags" in update_data:
        # Get the default tag
        default_tag = db.query(models.Tag).filter(models.Tag.name == DEFAULT_TAG_NAME).first()
        if not default_tag:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Default tag does not exist in the database.")

        tag_ids = update_data["tags"]
        if tag_ids is None or tag_ids == []:
            # If tags are set to empty or None, set to [default_tag.id]
            db_device.tags = [default_tag]
        else:
            # Ensure default tag is present
            if default_tag.id not in tag_ids:
                tag_ids.append(default_tag.id)
            tags = get_tags_by_ids(db, tag_ids)
            db_device.tags = tags

    db.commit()
    db.refresh(db_device)
    return db_device

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db_session),
    #_: models.User = Depends(require_admin_role) # Example: Protect deletion
):
    """Delete a network device from the system.
    
    Args:
        device_id (int): Unique identifier of the device to delete
        db (Session): Database session for executing queries
        
    Returns:
        None: Returns no content with 204 status code on successful deletion
        
    Raises:
        HTTPException (404): If no device exists with the specified ID
        
    Notes:
        - This operation permanently removes the device and cannot be undone
        - Related objects (like device configurations) may also be deleted
          depending on database cascade settings
    """
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if db_device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    
    db.delete(db_device)
    db.commit()
    return None

@router.get("/{device_id}/credentials", response_model=List[schemas.credential.Credential])
def get_device_credentials(
    device_id: int,
    db: Session = Depends(get_db_session)
):
    """Retrieve credentials applicable to a specific device.
    
    Args:
        device_id (int): Unique identifier of the device to retrieve credentials for
        db (Session): Database session for executing queries
        
    Returns:
        List[models.Credential]: List of matching credential objects, ordered by priority
        
    Raises:
        HTTPException (404): If no device exists with the specified ID
        
    Notes:
        - Returns credentials that match the device's tags
        - Credentials are ordered by priority to facilitate connection attempts
        - Used by connection services to determine authentication methods
    """
    # First check if device exists
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    
    # Get matching credentials using the service function
    credentials = get_matching_credentials_for_device(db, device_id)
    return credentials
