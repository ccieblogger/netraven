"""
Credentials router for the NetRaven web interface.

This module provides endpoints for managing device credentials,
including listing, adding, updating, removing, and testing credentials.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
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

# Import schemas and CRUD functions
from netraven.web.schemas.credential import (
    CredentialCreate, CredentialUpdate, CredentialOut, CredentialWithTags,
    CredentialTagAssociation, CredentialTagAssociationOut,
    CredentialTest, CredentialTestResult, CredentialBulkOperation
)
from netraven.web.crud import (
    get_credentials, get_credential, create_credential, update_credential, delete_credential,
    get_credentials_by_tag, associate_credential_with_tag, remove_credential_from_tag,
    test_credential, bulk_associate_credentials_with_tags, bulk_remove_credentials_from_tags
)

# Create logger
from netraven.core.logging import get_logger
logger = get_logger("netraven.web.routers.credentials")

# Create router
router = APIRouter(prefix="", tags=["credentials"])

@router.get("/", response_model=List[CredentialWithTags])
async def get_credentials_endpoint(
    skip: int = Query(0, description="Number of records to skip", ge=0),
    limit: int = Query(100, description="Maximum number of records to return", ge=1, le=1000),
    include_tags: bool = Query(True, description="Whether to include tag information"),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> List[Dict[str, Any]]:
    """
    Get all credentials.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        include_tags: Whether to include tag information
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of credentials
    """
    # Check if user has required permissions
    require_scope(current_principal, "read:credentials")
    
    try:
        logger.info(f"User {current_principal.username} is requesting credentials list")
        return get_credentials(db, skip=skip, limit=limit, include_tags=include_tags)
    except Exception as e:
        logger.error(f"Error retrieving credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving credentials: {str(e)}"
        )

@router.get("/{credential_id}", response_model=CredentialWithTags)
async def get_credential_endpoint(
    credential_id: str = Path(..., description="ID of the credential"),
    include_tags: bool = Query(True, description="Whether to include tag information"),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> Dict[str, Any]:
    """
    Get a credential by ID.
    
    Args:
        credential_id: ID of the credential
        include_tags: Whether to include tag information
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Credential details
    """
    # Check if user has required permissions
    require_scope(current_principal, "read:credentials")
    
    try:
        credential = get_credential(db, credential_id=credential_id, include_tags=include_tags)
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential with ID {credential_id} not found"
            )
        
        logger.info(f"User {current_principal.username} retrieved credential {credential_id}")
        return credential
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving credential {credential_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving credential: {str(e)}"
        )

@router.post("/", response_model=CredentialWithTags, status_code=status.HTTP_201_CREATED)
async def create_credential_endpoint(
    credential: CredentialCreate,
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> Dict[str, Any]:
    """
    Create a new credential.
    
    Args:
        credential: Credential creation data
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Created credential
    """
    # Check if user has required permissions
    require_scope(current_principal, "write:credentials")
    
    try:
        new_credential = create_credential(db, credential=credential)
        logger.info(f"User {current_principal.username} created credential {new_credential['id']}")
        return new_credential
    except Exception as e:
        logger.error(f"Error creating credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating credential: {str(e)}"
        )

@router.put("/{credential_id}", response_model=CredentialWithTags)
async def update_credential_endpoint(
    credential_id: str = Path(..., description="ID of the credential"),
    credential: CredentialUpdate = None,
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> Dict[str, Any]:
    """
    Update a credential.
    
    Args:
        credential_id: ID of the credential
        credential: Credential update data
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Updated credential
    """
    # Check if user has required permissions
    require_scope(current_principal, "write:credentials")
    
    try:
        # Check if credential exists
        existing = get_credential(db, credential_id=credential_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential with ID {credential_id} not found"
            )
        
        # Update the credential
        updated_credential = update_credential(db, credential_id=credential_id, credential=credential)
        if not updated_credential:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update credential {credential_id}"
            )
        
        logger.info(f"User {current_principal.username} updated credential {credential_id}")
        return updated_credential
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating credential {credential_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating credential: {str(e)}"
        )

@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential_endpoint(
    credential_id: str = Path(..., description="ID of the credential"),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> None:
    """
    Delete a credential.
    
    Args:
        credential_id: ID of the credential
        db: Database session
        current_principal: The authenticated user
    """
    # Check if user has required permissions
    require_scope(current_principal, "write:credentials")
    
    try:
        # Check if credential exists
        existing = get_credential(db, credential_id=credential_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential with ID {credential_id} not found"
            )
        
        # Delete the credential
        success = delete_credential(db, credential_id=credential_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete credential {credential_id}"
            )
        
        logger.info(f"User {current_principal.username} deleted credential {credential_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting credential {credential_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting credential: {str(e)}"
        )

@router.get("/tag/{tag_id}", response_model=List[CredentialWithTags])
async def get_credentials_by_tag_endpoint(
    tag_id: str = Path(..., description="ID of the tag"),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> List[Dict[str, Any]]:
    """
    Get all credentials associated with a tag.
    
    Args:
        tag_id: ID of the tag
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of credentials
    """
    # Check if user has required permissions
    require_scope(current_principal, "read:credentials")
    
    try:
        credentials = get_credentials_by_tag(db, tag_id=tag_id)
        logger.info(f"User {current_principal.username} retrieved credentials for tag {tag_id}")
        return credentials
    except Exception as e:
        logger.error(f"Error retrieving credentials for tag {tag_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving credentials for tag: {str(e)}"
        )

@router.post("/tag", response_model=CredentialTagAssociationOut)
async def associate_credential_with_tag_endpoint(
    association: CredentialTagAssociation,
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> Dict[str, Any]:
    """
    Associate a credential with a tag.
    
    Args:
        association: Credential-tag association data
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Association details
    """
    # Check if user has required permissions
    require_scope(current_principal, "write:credentials")
    
    try:
        result = associate_credential_with_tag(db, association=association)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential or tag not found"
            )
        
        logger.info(f"User {current_principal.username} associated credential {association.credential_id} with tag {association.tag_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error associating credential with tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error associating credential with tag: {str(e)}"
        )

@router.delete("/tag/{credential_id}/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_credential_from_tag_endpoint(
    credential_id: str = Path(..., description="ID of the credential"),
    tag_id: str = Path(..., description="ID of the tag"),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> None:
    """
    Remove a credential from a tag.
    
    Args:
        credential_id: ID of the credential
        tag_id: ID of the tag
        db: Database session
        current_principal: The authenticated user
    """
    # Check if user has required permissions
    require_scope(current_principal, "write:credentials")
    
    try:
        success = remove_credential_from_tag(db, credential_id=credential_id, tag_id=tag_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Association between credential {credential_id} and tag {tag_id} not found"
            )
        
        logger.info(f"User {current_principal.username} removed credential {credential_id} from tag {tag_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing credential from tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing credential from tag: {str(e)}"
        )

@router.post("/test/{credential_id}", response_model=CredentialTestResult)
async def test_credential_endpoint(
    credential_id: str = Path(..., description="ID of the credential"),
    test_data: CredentialTest = None,
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> Dict[str, Any]:
    """
    Test a credential against a device.
    
    Args:
        credential_id: ID of the credential
        test_data: Test parameters
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Test result
    """
    # Check if user has required permissions
    require_scope(current_principal, "read:credentials")
    
    try:
        # Check if credential exists
        existing = get_credential(db, credential_id=credential_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential with ID {credential_id} not found"
            )
        
        # If test_data is None, initialize with empty object
        if test_data is None:
            test_data = CredentialTest()
        
        # Test the credential
        result = test_credential(
            db, 
            credential_id=credential_id,
            device_id=test_data.device_id,
            hostname=test_data.hostname,
            device_type=test_data.device_type,
            port=test_data.port or 22
        )
        
        logger.info(f"User {current_principal.username} tested credential {credential_id}: {'success' if result['success'] else 'failure'}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing credential {credential_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing credential: {str(e)}"
        )

@router.post("/bulk/tag", response_model=Dict[str, Any])
async def bulk_associate_credentials_with_tags_endpoint(
    bulk_operation: CredentialBulkOperation,
    priority: float = Query(0.0, description="Priority for the associations"),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> Dict[str, Any]:
    """
    Associate multiple credentials with multiple tags.
    
    Args:
        bulk_operation: Bulk operation data
        priority: Priority for the associations
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Operation results
    """
    # Check if user has required permissions
    require_scope(current_principal, "write:credentials")
    
    try:
        result = bulk_associate_credentials_with_tags(
            db, 
            credential_ids=bulk_operation.credential_ids,
            tag_ids=bulk_operation.tag_ids,
            priority=priority
        )
        
        logger.info(f"User {current_principal.username} performed bulk tag association: {result['successful_operations']} successful, {result['failed_operations']} failed")
        return result
    except Exception as e:
        logger.error(f"Error associating credentials with tags in bulk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error associating credentials with tags in bulk: {str(e)}"
        )

@router.delete("/bulk/tag", response_model=Dict[str, Any])
async def bulk_remove_credentials_from_tags_endpoint(
    bulk_operation: CredentialBulkOperation,
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> Dict[str, Any]:
    """
    Remove multiple credentials from multiple tags.
    
    Args:
        bulk_operation: Bulk operation data
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Operation results
    """
    # Check if user has required permissions
    require_scope(current_principal, "write:credentials")
    
    try:
        result = bulk_remove_credentials_from_tags(
            db, 
            credential_ids=bulk_operation.credential_ids,
            tag_ids=bulk_operation.tag_ids
        )
        
        logger.info(f"User {current_principal.username} performed bulk tag removal: {result['successful_operations']} successful, {result['failed_operations']} failed")
        return result
    except Exception as e:
        logger.error(f"Error removing credentials from tags in bulk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing credentials from tags in bulk: {str(e)}"
        )

@router.get("/stats", response_model=schemas.CredentialStats)
async def get_credential_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get statistics about credentials usage and success rates.
    """
    logger.info(f"User {current_user.username} retrieved credential statistics")
    return await crud.credential.get_credential_stats(db=db) 