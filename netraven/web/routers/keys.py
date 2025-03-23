"""
Keys router for the NetRaven web interface.

This module provides endpoints for managing encryption keys,
including listing, creating, activating, rotating, backing up, and restoring keys.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import authentication dependencies
from netraven.web.auth import (
    get_current_principal, 
    UserPrincipal, 
    require_scope
)
from netraven.web.database import get_db

# Import core modules
from netraven.core.key_rotation import KeyRotationManager
from netraven.core.credential_store import get_credential_store

# Import schemas
from netraven.web.schemas.key_rotation import (
    KeyList, KeyInfo, KeyCreate, KeyResponse, 
    KeyActivate, KeyRotate, KeyRotationResponse,
    KeyBackupCreate, KeyBackupResponse, KeyBackupList,
    KeyRestore, KeyRestoreResponse
)

# Create logger
from netraven.core.logging import get_logger
logger = get_logger("netraven.web.routers.keys")

# Create router
router = APIRouter(prefix="", tags=["keys"])

# Initialize key rotation manager
key_manager = None

def get_key_manager():
    """Get the global key manager instance."""
    global key_manager
    
    if key_manager is None:
        credential_store = get_credential_store()
        key_manager = KeyRotationManager(credential_store=credential_store)
        
    return key_manager

@router.get("/", response_model=KeyList)
async def get_keys(
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("admin:*"))
) -> Dict[str, Any]:
    """
    Get all encryption keys.
    
    Args:
        db: Database session
        current_principal: The authenticated user with admin:* scope
        
    Returns:
        Dict[str, Any]: List of keys and the active key ID
    """
    try:
        logger.info(f"User {current_principal.username} is requesting keys list")
        
        # Get key manager
        manager = get_key_manager()
        
        # Get keys from manager
        keys = []
        active_key_id = None
        
        for key_id, metadata in manager._key_metadata.items():
            keys.append(KeyInfo(
                id=key_id,
                created_at=datetime.fromisoformat(metadata.get("created_at", datetime.utcnow().isoformat())),
                active=metadata.get("active", False),
                description=metadata.get("description", None),
                last_used=datetime.fromisoformat(metadata.get("last_used", datetime.utcnow().isoformat())) if metadata.get("last_used") else None
            ))
            if metadata.get("active", False):
                active_key_id = key_id
        
        return {
            "keys": keys,
            "active_key_id": active_key_id
        }
    except Exception as e:
        logger.error(f"Error retrieving keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving keys: {str(e)}"
        )

@router.get("/{key_id}", response_model=KeyInfo)
async def get_key(
    key_id: str = Path(..., description="ID of the key"),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("admin:*"))
) -> Dict[str, Any]:
    """
    Get information about a specific key.
    
    Args:
        key_id: ID of the key
        db: Database session
        current_principal: The authenticated user with admin:* scope
        
    Returns:
        Dict[str, Any]: Key information
    """
    try:
        logger.info(f"User {current_principal.username} is requesting key information for {key_id}")
        
        # Get key manager
        manager = get_key_manager()
        
        # Check if key exists
        if key_id not in manager._key_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Key with ID {key_id} not found"
            )
        
        # Get key metadata
        metadata = manager._key_metadata[key_id]
        
        return KeyInfo(
            id=key_id,
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.utcnow().isoformat())),
            active=metadata.get("active", False),
            description=metadata.get("description", None),
            last_used=datetime.fromisoformat(metadata.get("last_used", datetime.utcnow().isoformat())) if metadata.get("last_used") else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving key {key_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving key: {str(e)}"
        )

@router.post("/", response_model=KeyResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    key_create: KeyCreate,
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("admin:*"))
) -> Dict[str, Any]:
    """
    Create a new encryption key.
    
    Args:
        key_create: Key creation data
        db: Database session
        current_principal: The authenticated user with admin:* scope
        
    Returns:
        Dict[str, Any]: Created key information
    """
    try:
        logger.info(f"User {current_principal.username} is creating a new key")
        
        # Get key manager
        manager = get_key_manager()
        
        # Create a new key
        key_id = manager.create_new_key()
        
        # Update description if provided
        if key_create.description and key_id in manager._key_metadata:
            manager._key_metadata[key_id]["description"] = key_create.description
            manager._save_key_metadata()
        
        # Get key metadata
        metadata = manager._key_metadata[key_id]
        
        logger.info(f"User {current_principal.username} created key {key_id}")
        
        return KeyResponse(
            id=key_id,
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.utcnow().isoformat())),
            active=metadata.get("active", False),
            description=metadata.get("description", None)
        )
    except Exception as e:
        logger.error(f"Error creating key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating key: {str(e)}"
        )

@router.post("/activate", response_model=KeyResponse)
async def activate_key(
    key_activate: KeyActivate,
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("admin:*"))
) -> Dict[str, Any]:
    """
    Activate an encryption key.
    
    Args:
        key_activate: Key activation data
        db: Database session
        current_principal: The authenticated user with admin:* scope
        
    Returns:
        Dict[str, Any]: Activated key information
    """
    try:
        logger.info(f"User {current_principal.username} is activating key {key_activate.key_id}")
        
        # Get key manager
        manager = get_key_manager()
        
        # Check if key exists
        if key_activate.key_id not in manager._key_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Key with ID {key_activate.key_id} not found"
            )
        
        # Activate the key
        success = manager.activate_key(key_activate.key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to activate key {key_activate.key_id}"
            )
        
        # Get key metadata
        metadata = manager._key_metadata[key_activate.key_id]
        
        logger.info(f"User {current_principal.username} activated key {key_activate.key_id}")
        
        return KeyResponse(
            id=key_activate.key_id,
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.utcnow().isoformat())),
            active=metadata.get("active", False),
            description=metadata.get("description", None)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activating key: {str(e)}"
        )

@router.post("/rotate", response_model=KeyRotationResponse)
async def rotate_keys(
    key_rotate: KeyRotate = Body(default=KeyRotate()),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("admin:*"))
) -> Dict[str, Any]:
    """
    Rotate encryption keys.
    
    Args:
        key_rotate: Key rotation parameters
        db: Database session
        current_principal: The authenticated user with admin:* scope
        
    Returns:
        Dict[str, Any]: Key rotation results
    """
    try:
        logger.info(f"User {current_principal.username} is initiating key rotation (force={key_rotate.force})")
        
        # Get key manager
        manager = get_key_manager()
        
        # Store the previous active key ID
        previous_key_id = manager._active_key_id
        
        # Rotate keys
        new_key_id = manager.rotate_keys(force=key_rotate.force)
        
        if not new_key_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Key rotation not needed at this time. Use 'force=true' to override."
            )
        
        # Update description if provided
        if key_rotate.description and new_key_id in manager._key_metadata:
            manager._key_metadata[new_key_id]["description"] = key_rotate.description
            manager._save_key_metadata()
        
        # Get the credential store
        credential_store = get_credential_store()
        
        # Re-encrypt credentials with the new key
        reencrypted_count = 0
        if credential_store:
            reencrypted_count = credential_store.reencrypt_all_credentials(new_key_id)
        
        # Get key metadata
        metadata = manager._key_metadata[new_key_id]
        
        logger.info(f"User {current_principal.username} completed key rotation. New key: {new_key_id}")
        
        return KeyRotationResponse(
            new_key_id=new_key_id,
            previous_key_id=previous_key_id,
            reencrypted_count=reencrypted_count,
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.utcnow().isoformat()))
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rotating keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rotating keys: {str(e)}"
        )

@router.post("/backup", response_model=KeyBackupResponse)
async def create_backup(
    backup_request: KeyBackupCreate,
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("admin:*"))
) -> Dict[str, Any]:
    """
    Create a backup of encryption keys.
    
    Args:
        backup_request: Backup creation data
        db: Database session
        current_principal: The authenticated user with admin:* scope
        
    Returns:
        Dict[str, Any]: Backup information
    """
    try:
        logger.info(f"User {current_principal.username} is creating a key backup")
        
        # Get key manager
        manager = get_key_manager()
        
        # Handle specific key IDs if provided
        key_id = None
        if backup_request.key_ids and len(backup_request.key_ids) == 1:
            key_id = backup_request.key_ids[0]
            
            # Check if key exists
            if key_id not in manager._key_metadata:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Key with ID {key_id} not found"
                )
        
        # Create backup
        backup_data = manager.export_key_backup(
            password=backup_request.password,
            key_id=key_id
        )
        
        # Generate a backup ID
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Determine key count and if active key is included
        key_count = 1 if key_id else len(manager._keys)
        includes_active_key = key_id == manager._active_key_id if key_id else True
        
        logger.info(f"User {current_principal.username} created key backup {backup_id} with {key_count} keys")
        
        return KeyBackupResponse(
            backup_id=backup_id,
            created_at=datetime.utcnow(),
            key_count=key_count,
            includes_active_key=includes_active_key
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating key backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating key backup: {str(e)}"
        )

@router.post("/restore", response_model=KeyRestoreResponse)
async def restore_keys(
    restore_request: KeyRestore,
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("admin:*"))
) -> Dict[str, Any]:
    """
    Restore encryption keys from a backup.
    
    Args:
        restore_request: Key restore data
        db: Database session
        current_principal: The authenticated user with admin:* scope
        
    Returns:
        Dict[str, Any]: Restore results
    """
    try:
        logger.info(f"User {current_principal.username} is restoring keys from backup")
        
        # Get key manager
        manager = get_key_manager()
        
        # Restore keys from backup
        imported_keys = manager.import_key_backup(
            backup_data=restore_request.backup_data,
            password=restore_request.password
        )
        
        activated_key_id = None
        if restore_request.activate_key and imported_keys:
            # Find the key that was active in the backup
            # This is a simplification; actual implementation might be different
            for key_id in imported_keys:
                if key_id in manager._key_metadata and manager._key_metadata[key_id].get("active_in_backup", False):
                    manager.activate_key(key_id)
                    activated_key_id = key_id
                    break
        
        logger.info(f"User {current_principal.username} restored {len(imported_keys)} keys from backup")
        
        return KeyRestoreResponse(
            imported_keys=imported_keys,
            activated_key_id=activated_key_id
        )
    except Exception as e:
        logger.error(f"Error restoring keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restoring keys: {str(e)}"
        ) 