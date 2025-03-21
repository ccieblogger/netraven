"""
Credentials router for the NetRaven web interface.

This module provides endpoints for managing device credentials,
including listing, adding, updating, removing, and testing credentials.
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

# Import schemas and CRUD functions
from netraven.web.schemas.credential import (
    CredentialCreate, CredentialUpdate, CredentialOut, CredentialWithTags,
    CredentialTagAssociation, CredentialTagAssociationOut,
    CredentialTest, CredentialTestResult, CredentialBulkOperation,
    CredentialStats, TagCredentialStats, SmartCredentialRequest, SmartCredentialResponse
)
from netraven.web.crud import (
    get_credentials, get_credential, create_credential, update_credential, delete_credential,
    get_credentials_by_tag, associate_credential_with_tag, remove_credential_from_tag,
    test_credential, bulk_associate_credentials_with_tags, bulk_remove_credentials_from_tags,
    get_credential_stats
)

# Import the credential store
from netraven.core.credential_store import get_credential_store

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
    current_principal: UserPrincipal = Depends(require_scope("read:credentials"))
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
    try:
        logger.info(f"User {current_principal.username} is requesting credentials list")
        return get_credentials(db, skip=skip, limit=limit, include_tags=include_tags)
    except Exception as e:
        logger.error(f"Error retrieving credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving credentials: {str(e)}"
        )

@router.get("/stats", response_model=CredentialStats)
async def get_credential_stats_endpoint(
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("read:credentials"))
) -> Dict[str, Any]:
    """
    Get global credential usage statistics.
    
    Args:
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Credential usage statistics
    """
    try:
        credential_store = get_credential_store()
        if not credential_store:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Credential store is not available"
            )
        
        stats = credential_store.get_credential_stats()
        logger.info(f"User {current_principal.username} retrieved credential statistics")
        return stats
    except Exception as e:
        logger.error(f"Error retrieving credential statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving credential statistics: {str(e)}"
        )

@router.get("/stats/tag/{tag_id}", response_model=TagCredentialStats)
async def get_tag_credential_stats_endpoint(
    tag_id: str = Path(..., description="ID of the tag"),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("read:credentials"))
) -> Dict[str, Any]:
    """
    Get credential usage statistics for a specific tag.
    
    Args:
        tag_id: ID of the tag
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Credential usage statistics for the tag
    """
    try:
        credential_store = get_credential_store()
        if not credential_store:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Credential store is not available"
            )
        
        stats = credential_store.get_tag_credential_stats(tag_id)
        logger.info(f"User {current_principal.username} retrieved credential statistics for tag {tag_id}")
        return stats
    except Exception as e:
        logger.error(f"Error retrieving credential statistics for tag {tag_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving credential statistics: {str(e)}"
        )

@router.get("/{credential_id}", response_model=CredentialWithTags)
async def get_credential_endpoint(
    credential_id: str = Path(..., description="ID of the credential"),
    include_tags: bool = Query(True, description="Whether to include tag information"),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("read:credentials"))
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
    current_principal: UserPrincipal = Depends(require_scope("write:credentials"))
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
    current_principal: UserPrincipal = Depends(require_scope("write:credentials"))
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
    current_principal: UserPrincipal = Depends(require_scope("write:credentials"))
) -> None:
    """
    Delete a credential.
    
    Args:
        credential_id: ID of the credential
        db: Database session
        current_principal: The authenticated user
    """
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
    current_principal: UserPrincipal = Depends(require_scope("read:credentials"))
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
    current_principal: UserPrincipal = Depends(require_scope("write:credentials"))
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
    current_principal: UserPrincipal = Depends(require_scope("write:credentials"))
) -> None:
    """
    Remove a credential from a tag.
    
    Args:
        credential_id: ID of the credential
        tag_id: ID of the tag
        db: Database session
        current_principal: The authenticated user
    """
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
    current_principal: UserPrincipal = Depends(require_scope("read:credentials"))
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
    current_principal: UserPrincipal = Depends(require_scope("write:credentials"))
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
    current_principal: UserPrincipal = Depends(require_scope("write:credentials"))
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

@router.post("/smart-select", response_model=SmartCredentialResponse)
async def get_smart_credentials_endpoint(
    request: SmartCredentialRequest,
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("read:credentials"))
) -> Dict[str, Any]:
    """
    Get a list of credentials for a tag, intelligently ranked based on success rates.
    
    This endpoint uses a smart algorithm that considers:
    - Historical success rate (75% weight)
    - Manual priority settings (15% weight)
    - Recency of successful use (10% weight)
    
    Args:
        request: Smart credential request parameters
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: List of ranked credentials with explanatory data
    """
    try:
        credential_store = get_credential_store()
        if not credential_store:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Credential store is not available"
            )
        
        credentials = credential_store.get_smart_credentials_for_tag(
            tag_id=request.tag_id,
            limit=request.limit
        )
        
        # Create explanation of ranking algorithm
        explanation = {
            "algorithm": "Smart ranking algorithm",
            "weights": {
                "success_rate": "75%",
                "manual_priority": "15%",
                "recency": "10%"
            },
            "factors_considered": [
                "Historical success/failure rate with this tag",
                "Manually set credential priority",
                "How recently the credential was used successfully"
            ],
            "recommendation": "Credentials are ordered by their computed score. Try them in order."
        }
        
        logger.info(f"User {current_principal.username} retrieved smart credentials for tag {request.tag_id}")
        return {
            "credentials": credentials,
            "explanation": explanation
        }
    except Exception as e:
        logger.error(f"Error retrieving smart credentials for tag {request.tag_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving smart credentials: {str(e)}"
        )

@router.post("/optimize-priorities/{tag_id}", response_model=Dict[str, Any])
async def optimize_credential_priorities_endpoint(
    tag_id: str = Path(..., description="ID of the tag to optimize priorities for"),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("write:credentials"))
) -> Dict[str, Any]:
    """
    Automatically adjust credential priorities for a tag based on success rates.
    
    This endpoint will re-prioritize credentials based on historical success rates
    and recent usage patterns.
    
    Args:
        tag_id: ID of the tag
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Result of the optimization operation
    """
    try:
        credential_store = get_credential_store()
        if not credential_store:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Credential store is not available"
            )
        
        success = credential_store.optimize_credential_priorities(tag_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to optimize credential priorities for tag {tag_id}"
            )
        
        # Get credentials after optimization to return the new priorities
        credentials = credential_store.get_credentials_by_tag(tag_id)
        
        logger.info(f"User {current_principal.username} optimized credential priorities for tag {tag_id}")
        return {
            "success": True,
            "message": f"Successfully optimized credential priorities for tag {tag_id}",
            "tag_id": tag_id,
            "credentials": credentials
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing credential priorities for tag {tag_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error optimizing credential priorities: {str(e)}"
        )

@router.post("/reencrypt", response_model=Dict[str, Any])
async def reencrypt_credentials_endpoint(
    batch_size: int = Query(100, description="Number of credentials to process in each batch"),
    db: Session = Depends(get_db),
    current_principal: UserPrincipal = Depends(require_scope("write:credentials"))
) -> Dict[str, Any]:
    """
    Re-encrypt all credentials with the current encryption key.
    
    This endpoint processes credentials in batches for better performance
    and provides detailed statistics about the operation.
    
    Args:
        batch_size: Number of credentials to process in each batch
        db: Database session
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Statistics about the re-encryption operation
    """
    try:
        # Only admins should be able to trigger re-encryption
        if not current_principal.has_role("admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can re-encrypt credentials"
            )
        
        credential_store = get_credential_store()
        if not credential_store:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Credential store is not available"
            )
        
        # Define a progress callback
        async def progress_callback(current, total, batch_number, status):
            # In a real implementation, this might update a progress indicator
            # or send a websocket message with progress information
            logger.info(f"Re-encryption progress: {current}/{total} credentials (batch {batch_number}), status: {status}")
        
        # Perform the re-encryption
        result = credential_store.reencrypt_all_credentials(
            batch_size=batch_size,
            progress_callback=progress_callback
        )
        
        logger.info(f"User {current_principal.username} completed credential re-encryption: {result}")
        return {
            "success": result['success'],
            "message": "Credential re-encryption completed",
            "details": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during credential re-encryption: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during credential re-encryption: {str(e)}"
        ) 