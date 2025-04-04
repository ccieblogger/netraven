"""
Credentials router for managing device credentials.

This module provides endpoints for creating, retrieving, updating, and 
deleting credentials for device access. It supports various credential types
including username/password, SSH keys, SNMP, and API tokens.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from netraven.web.database import get_async_session
from netraven.web.schemas.credential import (
    CredentialCreate, 
    CredentialUpdate, 
    CredentialResponse,
    CredentialWithSecretsResponse
)
from netraven.core.services.service_factory import ServiceFactory
from netraven.web.auth import UserPrincipal, get_current_principal
from netraven.web.auth.permissions import require_scope, require_ownership
from netraven.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/credentials", tags=["credentials"])

# Helper function to extract credential owner ID for permission checks
async def get_credential_owner_id(
    credential_id: str = Path(..., description="The ID of the credential"),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> str:
    """
    Extract the owner ID of a credential for permission checking.
    
    Args:
        credential_id: The credential ID
        session: Database session
        factory: Service factory
        
    Returns:
        str: Owner ID of the credential
        
    Raises:
        HTTPException: If credential not found
    """
    credential = await factory.credential_service.get_credential(credential_id)
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential with ID {credential_id} not found"
        )
    
    return credential.owner_id

@router.post("/", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    credential: CredentialCreate,
    principal: UserPrincipal = Depends(require_scope("write:credentials")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
):
    """
    Create a new credential.
    
    This endpoint requires the write:credentials scope.
    """
    try:
        # Set owner ID to current user
        credential_data = credential.model_dump()
        credential_data["owner_id"] = principal.id
        
        # Create credential using service
        new_credential = await factory.credential_service.create_credential(credential_data)
        
        logger.info(f"Credential created: id={new_credential.id}, type={new_credential.type}, user={principal.username}")
        return new_credential
    except Exception as e:
        logger.error(f"Error creating credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating credential: {str(e)}"
        )

@router.get("/", response_model=List[CredentialResponse])
async def list_credentials(
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = Query(None, description="Filter by credential type"),
    tag_id: Optional[str] = Query(None, description="Filter by tag ID"),
    include_secrets: bool = Query(False, description="Include secret fields (requires special permission)"),
    principal: UserPrincipal = Depends(require_scope("read:credentials")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
):
    """
    List credentials with optional filtering.
    
    This endpoint requires the read:credentials scope.
    Admin users can see all credentials, while regular users only see their own.
    """
    try:
        # Only return credentials owned by the current user unless they're an admin
        filter_params = {}
        if type:
            filter_params["type"] = type
        if tag_id:
            filter_params["tag_id"] = tag_id
        if not principal.is_admin:
            filter_params["owner_id"] = principal.id
        
        # Check special permission for including secrets
        if include_secrets and not principal.has_scope("admin:credentials"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view credential secrets"
            )
        
        # Get credentials using service
        credentials = await factory.credential_service.list_credentials(
            skip=skip, 
            limit=limit, 
            filter_params=filter_params
        )
        
        # If including secrets is requested and permitted, use the service to get credentials with secrets
        if include_secrets:
            credentials_with_secrets = []
            for cred in credentials:
                cred_with_secrets = await factory.credential_service.get_credential_with_secrets(cred.id)
                if cred_with_secrets:
                    credentials_with_secrets.append(cred_with_secrets)
            return credentials_with_secrets
        
        return credentials
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing credentials: {str(e)}"
        )

@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: str,
    include_secrets: bool = Query(False, description="Include secret fields (requires special permission)"),
    principal: UserPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_credential_owner_id))
):
    """
    Get a specific credential by ID.
    
    This endpoint requires ownership of the credential or admin permissions.
    """
    try:
        # Check special permission for including secrets
        if include_secrets and not principal.has_scope("admin:credentials"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view credential secrets"
            )
        
        # Get credential with or without secrets
        if include_secrets:
            credential = await factory.credential_service.get_credential_with_secrets(credential_id)
        else:
            credential = await factory.credential_service.get_credential(credential_id)
        
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential with ID {credential_id} not found"
            )
        
        return credential
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting credential {credential_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting credential: {str(e)}"
        )

@router.put("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: str,
    credential_update: CredentialUpdate,
    principal: UserPrincipal = Depends(require_scope("write:credentials")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_credential_owner_id))
):
    """
    Update a credential.
    
    This endpoint requires the write:credentials scope and ownership of the credential.
    """
    try:
        # Update credential using service
        updated_credential = await factory.credential_service.update_credential(
            credential_id, 
            credential_update.model_dump(exclude_unset=True)
        )
        
        if not updated_credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential with ID {credential_id} not found"
            )
        
        logger.info(f"Credential updated: id={credential_id}, user={principal.username}")
        return updated_credential
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating credential {credential_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating credential: {str(e)}"
        )

@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: str,
    principal: UserPrincipal = Depends(require_scope("delete:credentials")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_credential_owner_id))
):
    """
    Delete a credential.
    
    This endpoint requires the delete:credentials scope and ownership of the credential.
    """
    try:
        # Delete credential using service
        result = await factory.credential_service.delete_credential(credential_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential with ID {credential_id} not found"
            )
        
        logger.info(f"Credential deleted: id={credential_id}, user={principal.username}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting credential {credential_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting credential: {str(e)}"
        )

@router.post("/{credential_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_tag_to_credential(
    credential_id: str,
    tag_id: str,
    principal: UserPrincipal = Depends(require_scope("write:credentials")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_credential_owner_id))
):
    """
    Add a tag to a credential.
    
    This endpoint requires the write:credentials scope and ownership of the credential.
    """
    try:
        # Add tag to credential using service
        result = await factory.credential_service.add_tag_to_credential(credential_id, tag_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential with ID {credential_id} or tag with ID {tag_id} not found"
            )
        
        logger.info(f"Tag {tag_id} added to credential {credential_id} by user {principal.username}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding tag {tag_id} to credential {credential_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error adding tag to credential: {str(e)}"
        )

@router.delete("/{credential_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_credential(
    credential_id: str,
    tag_id: str,
    principal: UserPrincipal = Depends(require_scope("write:credentials")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_credential_owner_id))
):
    """
    Remove a tag from a credential.
    
    This endpoint requires the write:credentials scope and ownership of the credential.
    """
    try:
        # Remove tag from credential using service
        result = await factory.credential_service.remove_tag_from_credential(credential_id, tag_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential with ID {credential_id} or tag with ID {tag_id} not found"
            )
        
        logger.info(f"Tag {tag_id} removed from credential {credential_id} by user {principal.username}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing tag {tag_id} from credential {credential_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error removing tag from credential: {str(e)}"
        )

@router.get("/{credential_id}/tags", response_model=List[str])
async def list_credential_tags(
    credential_id: str,
    principal: UserPrincipal = Depends(require_scope("read:credentials")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_credential_owner_id))
):
    """
    List all tags associated with a credential.
    
    This endpoint requires the read:credentials scope and ownership of the credential.
    """
    try:
        # Get credential tags using service
        tags = await factory.credential_service.get_credential_tags(credential_id)
        
        if tags is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential with ID {credential_id} not found"
            )
        
        return tags
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tags for credential {credential_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing credential tags: {str(e)}"
        )

@router.post("/{credential_id}/validate", status_code=status.HTTP_200_OK)
async def validate_credential(
    credential_id: str,
    principal: UserPrincipal = Depends(require_scope("read:credentials")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_credential_owner_id))
):
    """
    Validate a credential against a device or service.
    
    This endpoint requires the read:credentials scope and ownership of the credential.
    """
    try:
        # Validate credential using service
        validation_result = await factory.credential_service.validate_credential(credential_id)
        
        logger.info(f"Credential validation for {credential_id}: {validation_result}")
        return {"valid": validation_result, "message": "Credential validation successful"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating credential {credential_id}: {str(e)}")
        return {
            "valid": False,
            "message": f"Validation failed: {str(e)}"
        } 