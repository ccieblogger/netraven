"""
Backups router for the NetRaven web interface.

This module provides endpoints for managing device configuration backups,
including listing, viewing, comparing, and restoring backups.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Import authentication dependencies
from netraven.web.routers.auth import User, get_current_active_user

# Create router
router = APIRouter()

class BackupBase(BaseModel):
    """Base model for backup data."""
    device_id: str
    version: str
    file_path: str
    file_size: int
    status: str

class Backup(BackupBase):
    """Model for backup data returned to clients."""
    id: str
    device_hostname: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class BackupContent(BaseModel):
    """Model for backup content."""
    id: str
    device_id: str
    device_hostname: str
    content: str
    created_at: datetime

# Demo backups for initial testing - to be replaced with database storage
DEMO_BACKUPS = [
    {
        "id": "9c8b7a65-6d5e-4f3g-2h1i-0j9k8l7m6n5o",
        "device_id": "1c39a8c9-4e77-4954-9e8d-19c7d82b3b34",
        "device_hostname": "router1",
        "version": "1.0",
        "file_path": "/backups/router1_config_20230401.txt",
        "file_size": 2048,
        "status": "complete",
        "created_at": datetime(2023, 4, 1, 12, 0, 0)
    },
    {
        "id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
        "device_id": "1c39a8c9-4e77-4954-9e8d-19c7d82b3b34",
        "device_hostname": "router1",
        "version": "1.1",
        "file_path": "/backups/router1_config_20230501.txt",
        "file_size": 2112,
        "status": "complete",
        "created_at": datetime(2023, 5, 1, 12, 0, 0)
    },
    {
        "id": "q7r8s9t0-u1v2-w3x4-y5z6-a7b8c9d0e1f2",
        "device_id": "6a0e9f7a-8b4c-4d5e-9f7a-8b4c6a0e9f7a",
        "device_hostname": "switch1",
        "version": "1.0",
        "file_path": "/backups/switch1_config_20230401.txt",
        "file_size": 1536,
        "status": "complete",
        "created_at": datetime(2023, 4, 1, 12, 30, 0)
    }
]

# Demo backup content
DEMO_BACKUP_CONTENT = {
    "9c8b7a65-6d5e-4f3g-2h1i-0j9k8l7m6n5o": """
hostname Router1
!
interface GigabitEthernet0/0
 description WAN
 ip address dhcp
 no shutdown
!
interface GigabitEthernet0/1
 description LAN
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 GigabitEthernet0/0
!
end
""",
    "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6": """
hostname Router1
!
interface GigabitEthernet0/0
 description WAN Connection
 ip address dhcp
 no shutdown
!
interface GigabitEthernet0/1
 description Internal LAN
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/2
 description DMZ
 ip address 192.168.2.1 255.255.255.0
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 GigabitEthernet0/0
!
end
""",
    "q7r8s9t0-u1v2-w3x4-y5z6-a7b8c9d0e1f2": """
hostname Switch1
!
vlan 10
 name Users
!
vlan 20
 name Voice
!
interface GigabitEthernet0/1
 description Uplink to Router
 switchport mode trunk
 switchport trunk allowed vlan 10,20
 no shutdown
!
interface range GigabitEthernet1/0/1-24
 description Access Ports
 switchport mode access
 switchport access vlan 10
 switchport voice vlan 20
 spanning-tree portfast
 no shutdown
!
end
"""
}

@router.get("", response_model=List[Backup])
async def list_backups(
    device_id: Optional[str] = None,
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    List backups.
    
    This endpoint returns a list of backups, optionally filtered by device.
    """
    # In a real app, this would query the database
    if device_id:
        filtered_backups = [b for b in DEMO_BACKUPS if b["device_id"] == device_id]
    else:
        filtered_backups = DEMO_BACKUPS
        
    # Apply pagination
    paginated_backups = filtered_backups[offset:offset + limit]
    
    return paginated_backups

@router.get("/{backup_id}", response_model=Backup)
async def get_backup(
    backup_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get backup details.
    
    This endpoint returns details for a specific backup.
    """
    # In a real app, this would query the database
    for backup in DEMO_BACKUPS:
        if backup["id"] == backup_id:
            return backup
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Backup with ID {backup_id} not found"
    )

@router.get("/{backup_id}/content", response_model=BackupContent)
async def get_backup_content(
    backup_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get backup content.
    
    This endpoint returns the content of a specific backup.
    """
    # In a real app, this would read the backup file
    if backup_id not in DEMO_BACKUP_CONTENT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content for backup ID {backup_id} not found"
        )
    
    # Find the backup metadata
    backup_metadata = None
    for backup in DEMO_BACKUPS:
        if backup["id"] == backup_id:
            backup_metadata = backup
            break
    
    if not backup_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup_id} not found"
        )
    
    return {
        "id": backup_id,
        "device_id": backup_metadata["device_id"],
        "device_hostname": backup_metadata["device_hostname"],
        "content": DEMO_BACKUP_CONTENT[backup_id],
        "created_at": backup_metadata["created_at"]
    }

@router.post("/compare", status_code=status.HTTP_200_OK)
async def compare_backups(
    backup1_id: str,
    backup2_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Compare two backups.
    
    This endpoint compares the content of two backups and returns the differences.
    """
    # Check if both backups exist
    if backup1_id not in DEMO_BACKUP_CONTENT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content for backup ID {backup1_id} not found"
        )
    
    if backup2_id not in DEMO_BACKUP_CONTENT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content for backup ID {backup2_id} not found"
        )
    
    # In a real app, this would use a proper diff algorithm
    # For now, just return a simple object with both contents
    return {
        "backup1_id": backup1_id,
        "backup2_id": backup2_id,
        "differences": [
            {
                "line": 5,
                "backup1": "description WAN",
                "backup2": "description WAN Connection"
            },
            {
                "line": 10,
                "backup1": "description LAN",
                "backup2": "description Internal LAN"
            }
        ]
    }

@router.post("/{backup_id}/restore", status_code=status.HTTP_202_ACCEPTED)
async def restore_backup(
    backup_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Restore a backup to a device.
    
    This endpoint initiates a restore job for a specific backup.
    """
    # In a real app, this would trigger an actual restore job
    for backup in DEMO_BACKUPS:
        if backup["id"] == backup_id:
            return {
                "message": f"Restore job initiated for device {backup['device_hostname']}",
                "job_id": str(uuid.uuid4()),
                "backup_id": backup_id,
                "device_id": backup["device_id"],
                "status": "pending"
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Backup with ID {backup_id} not found"
    )

@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(
    backup_id: str,
    current_user: User = Depends(get_current_active_user)
) -> None:
    """
    Delete a backup.
    
    This endpoint deletes a specific backup.
    """
    # In a real app, this would delete from the database and storage
    for i, backup in enumerate(DEMO_BACKUPS):
        if backup["id"] == backup_id:
            # In a real app, we would actually delete the item
            # For now, we'll just return
            return
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Backup with ID {backup_id} not found"
    ) 