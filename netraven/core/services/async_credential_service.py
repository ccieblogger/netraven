"""
Asynchronous Credential Management Service for NetRaven.

Handles CRUD operations for credentials, manages associations with tags,
provides statistics, tests credentials, and interacts with the credential store.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, NoResultFound
from fastapi import HTTPException, status

# Models and Schemas (adjust imports as needed)
from netraven.web.models.credential import Credential as CredentialModel
from netraven.web.models.tag import Tag as TagModel # For associations
from netraven.web.models.credential_tag import CredentialTag as CredentialTagModel # Join table
from netraven.web.schemas.credential import (
    CredentialCreate, CredentialUpdate, CredentialWithTags,
    CredentialTagAssociation, CredentialTagAssociationOut,
    CredentialTest, CredentialTestResult, CredentialBulkOperation,
    CredentialStats, TagCredentialStats, SmartCredentialRequest, SmartCredentialResponse
)

# Dependencies (Placeholder - To be injected via __init__)
# from .async_tag_service import AsyncTagService
from netraven.core.credential_store import CredentialStore # Assuming CredentialStore might be used directly for now

logger = logging.getLogger(__name__)

class AsyncCredentialService:
    """
    Provides methods for managing credentials asynchronously.
    """
    def __init__(self, db_session: AsyncSession, credential_store: CredentialStore, tag_service: Any):
        """
        Initialize the credential service.
        Args:
            db_session: Async database session.
            credential_store: Instance of CredentialStore.
            tag_service: Instance of AsyncTagService.
        """
        self._db_session = db_session
        self._credential_store = credential_store # Store dependency
        self._tag_service = tag_service # Store dependency

    # --- CRUD Methods ---

    async def list_credentials(self, skip: int = 0, limit: int = 100, include_tags: bool = True) -> List[CredentialModel]:
        """Lists credentials with optional tag details."""
        logger.debug(f"Listing credentials: skip={skip}, limit={limit}, include_tags={include_tags}")
        stmt = select(CredentialModel).order_by(CredentialModel.name).offset(skip).limit(limit)
        if include_tags:
            # Eager load tags to avoid N+1 queries if tags are accessed later
            stmt = stmt.options(selectinload(CredentialModel.tags))
        
        result = await self._db_session.execute(stmt)
        credentials = result.scalars().all()
        logger.debug(f"Found {len(credentials)} credentials.")
        # Note: Schema conversion (e.g., to CredentialWithTags) happens in the router or a dedicated mapping layer
        return credentials

    async def get_credential_by_id(self, credential_id: str, include_tags: bool = True) -> Optional[CredentialModel]:
        """Fetches a credential by ID, optionally with tags."""
        logger.debug(f"Getting credential by id: {credential_id}, include_tags={include_tags}")
        stmt = select(CredentialModel).where(CredentialModel.id == credential_id)
        if include_tags:
             stmt = stmt.options(selectinload(CredentialModel.tags))
        result = await self._db_session.execute(stmt)
        credential = result.scalar_one_or_none()
        if credential:
            logger.debug(f"Found credential: {credential.name}")
        else:
            logger.debug(f"Credential with id {credential_id} not found.")
        return credential

    async def create_credential(self, credential_data: CredentialCreate) -> CredentialModel:
        """Creates a new credential using the credential store for encryption."""
        logger.debug(f"Attempting to create credential: {credential_data.name}")
        # TODO: Interaction with CredentialStore for encryption before saving
        # encrypted_password = self._credential_store.encrypt(credential_data.password) # Example placeholder
        
        # For now, create directly (assuming password handling in model/store)
        # Need clarification on where encryption happens
        db_credential = CredentialModel(
            name=credential_data.name,
            username=credential_data.username,
            password=credential_data.password, # Store directly for now - NEEDS REVISITING for encryption
            credential_type=credential_data.credential_type,
            description=credential_data.description,
            notes=credential_data.notes
        )
        self._db_session.add(db_credential)
        try:
            await self._db_session.flush()
            await self._db_session.refresh(db_credential)
            logger.info(f"Successfully created credential {db_credential.id} ({db_credential.name})")
            return db_credential
        except IntegrityError as e:
            await self._db_session.rollback()
            logger.error(f"DB integrity error creating credential {credential_data.name}: {e}")
            # Check for unique constraint violation if applicable
            if "unique constraint" in str(e).lower():
                 raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Credential with name '{credential_data.name}' already exists.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credential could not be created due to integrity constraint.")
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error during credential creation flush/refresh: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error creating credential.")

    async def update_credential(self, credential_id: str, credential_data: CredentialUpdate) -> Optional[CredentialModel]:
        """Updates an existing credential."""
        logger.debug(f"Attempting to update credential: {credential_id}")
        db_credential = await self.get_credential_by_id(credential_id, include_tags=False) # Don't need tags for update itself
        if not db_credential:
            logger.warning(f"Update failed: Credential {credential_id} not found.")
            return None

        update_data = credential_data.dict(exclude_unset=True)
        
        # TODO: Handle password update - needs encryption via CredentialStore
        # if 'password' in update_data:
        #    db_credential.password = self._credential_store.encrypt(update_data['password'])
        #    del update_data['password'] # Remove plain text password

        for key, value in update_data.items():
            if hasattr(db_credential, key):
                 # Handle password separately if encryption is involved
                 if key == 'password':
                     # Placeholder: Assume direct set, NEEDS REVISITING
                     setattr(db_credential, key, value)
                     logger.warning(f"Updating password for {credential_id} without encryption (placeholder).")
                 else:
                     setattr(db_credential, key, value)
            else:
                logger.warning(f"Attempted to update non-existent attribute '{key}' on credential {credential_id}")

        try:
            await self._db_session.flush()
            await self._db_session.refresh(db_credential)
            logger.info(f"Successfully updated credential {credential_id}")
            return db_credential
        except IntegrityError as e:
             await self._db_session.rollback()
             logger.error(f"DB integrity error updating credential {credential_id}: {e}")
             if "unique constraint" in str(e).lower():
                 # Determine which field caused the conflict if possible
                 raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Credential update failed due to unique constraint (e.g., name conflict).")
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credential update failed due to integrity constraint.")
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error during credential update flush/refresh for {credential_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error updating credential.")


    async def delete_credential(self, credential_id: str) -> bool:
        """Deletes a credential."""
        logger.debug(f"Attempting to delete credential: {credential_id}")
        db_credential = await self.get_credential_by_id(credential_id, include_tags=False)
        if not db_credential:
            logger.warning(f"Delete failed: Credential {credential_id} not found.")
            return False
            
        # TODO: Check for associations or dependencies before deletion?
        # If credentials should not be deleted if associated with devices/jobs, add checks here.

        await self._db_session.delete(db_credential)
        try:
            await self._db_session.flush()
            logger.info(f"Successfully deleted credential {credential_id}")
            return True
        except IntegrityError as e:
             # This might happen if foreign key constraints prevent deletion
             await self._db_session.rollback()
             logger.error(f"DB integrity error deleting credential {credential_id}: {e}")
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete credential, it might be associated with other resources.")
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error during credential deletion flush for {credential_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error deleting credential.")

    # --- Tag Association Methods ---

    async def get_credentials_by_tag(self, tag_id: str) -> List[CredentialModel]:
        """Lists credentials associated with a specific tag."""
        logger.debug(f"Getting credentials for tag: {tag_id}")
        
        # First verify the tag exists using tag service
        tag = await self._tag_service.get_tag_by_id(tag_id)
        if not tag:
            logger.warning(f"Tag {tag_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Tag with ID {tag_id} not found"
            )
        
        # Query credentials through the relationship
        stmt = (
            select(CredentialModel)
            .join(CredentialTagModel, CredentialModel.id == CredentialTagModel.credential_id)
            .where(CredentialTagModel.tag_id == tag_id)
            .options(selectinload(CredentialModel.tags))  # Load tags to avoid N+1 queries
        )
        
        result = await self._db_session.execute(stmt)
        credentials = result.scalars().all()
        logger.debug(f"Found {len(credentials)} credentials for tag {tag_id}")
        return credentials

    async def associate_credential_with_tag(self, association_data: CredentialTagAssociation) -> CredentialTagModel:
        """Associates a credential with a tag."""
        logger.debug(f"Associating credential {association_data.credential_id} with tag {association_data.tag_id}")
        
        # 1. Verify credential exists
        credential = await self.get_credential_by_id(association_data.credential_id, include_tags=False)
        if not credential:
            logger.warning(f"Credential {association_data.credential_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Credential with ID {association_data.credential_id} not found"
            )
        
        # 2. Verify tag exists (use injected tag service)
        tag = await self._tag_service.get_tag_by_id(association_data.tag_id)
        if not tag:
            logger.warning(f"Tag {association_data.tag_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Tag with ID {association_data.tag_id} not found"
            )
        
        # 3. Check if association already exists
        stmt = (
            select(CredentialTagModel)
            .where(
                (CredentialTagModel.credential_id == association_data.credential_id) &
                (CredentialTagModel.tag_id == association_data.tag_id)
            )
        )
        result = await self._db_session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Just update priority if the association already exists
            existing.priority = association_data.priority
            await self._db_session.flush()
            await self._db_session.refresh(existing)
            logger.info(f"Updated priority for existing association between credential {association_data.credential_id} and tag {association_data.tag_id}")
            return existing
        
        # 4. Create the association
        credential_tag = CredentialTagModel(
            credential_id=association_data.credential_id,
            tag_id=association_data.tag_id,
            priority=association_data.priority
        )
        self._db_session.add(credential_tag)
        
        try:
            await self._db_session.flush()
            await self._db_session.refresh(credential_tag)
            logger.info(f"Created association between credential {association_data.credential_id} and tag {association_data.tag_id}")
            return credential_tag
        except IntegrityError as e:
            await self._db_session.rollback()
            logger.error(f"DB integrity error creating credential-tag association: {e}")
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Association between credential {association_data.credential_id} and tag {association_data.tag_id} already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create association due to constraint violation"
            )
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error creating credential-tag association: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create association due to an internal error"
            )

    async def remove_credential_from_tag(self, credential_id: str, tag_id: str) -> bool:
        """Removes the association between a credential and a tag."""
        logger.debug(f"Removing credential {credential_id} from tag {tag_id}")
        
        # Find the association
        stmt = (
            select(CredentialTagModel)
            .where(
                (CredentialTagModel.credential_id == credential_id) &
                (CredentialTagModel.tag_id == tag_id)
            )
        )
        result = await self._db_session.execute(stmt)
        association = result.scalar_one_or_none()
        
        if not association:
            logger.warning(f"Association between credential {credential_id} and tag {tag_id} not found")
            return False
        
        # Delete the association
        await self._db_session.delete(association)
        
        try:
            await self._db_session.flush()
            logger.info(f"Removed association between credential {credential_id} and tag {tag_id}")
            return True
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error removing credential-tag association: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove association due to an internal error"
            )

    # --- Credential Store Interaction Methods ---

    async def get_credential_stats(self) -> CredentialStats:
        """Gets global credential statistics from the store."""
        # Placeholder - Directly call store method (assuming it's safe/sync for now)
        logger.debug("Getting global credential stats from store.")
        try:
            # Assuming get_credential_stats doesn't need async session
            stats_dict = self._credential_store.get_credential_stats()
            return CredentialStats(**stats_dict) # Convert dict to Pydantic model
        except Exception as e:
            logger.error(f"Error getting global credential stats from store: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve credential statistics.")


    async def get_tag_credential_stats(self, tag_id: str) -> TagCredentialStats:
        """Gets credential statistics for a specific tag from the store."""
         # Placeholder - Directly call store method (assuming it's safe/sync for now)
        logger.debug(f"Getting credential stats for tag {tag_id} from store.")
         # 1. Verify tag exists (use self._tag_service) ? - Store might do this.
        tag = await self._tag_service.get_tag_by_id(tag_id)
        if not tag:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag with ID {tag_id} not found")
             
        try:
            # Assuming get_tag_credential_stats doesn't need async session
            stats_dict = self._credential_store.get_tag_credential_stats(tag_id)
            return TagCredentialStats(**stats_dict) # Convert dict to Pydantic model
        except Exception as e:
            logger.error(f"Error getting credential stats for tag {tag_id} from store: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve tag credential statistics.")

    async def test_credential(self, credential_id: str, test_data: CredentialTest) -> CredentialTestResult:
        """Tests a credential against a target using the store."""
        # Placeholder - Requires interaction with store's test method
        logger.warning("test_credential is not fully implemented.")
        # 1. Get credential details (potentially decrypted password from store?)
        # 2. Call self._credential_store.test_credential(...)
        raise NotImplementedError

    # --- Bulk Operations ---

    async def bulk_associate_credentials_with_tags(self, bulk_data: CredentialBulkOperation) -> Dict[str, Any]:
        """Bulk associates credentials with tags."""
        # Placeholder
        logger.warning("bulk_associate_credentials_with_tags is not fully implemented.")
        raise NotImplementedError

    async def bulk_remove_credentials_from_tags(self, bulk_data: CredentialBulkOperation) -> Dict[str, Any]:
        """Bulk removes associations between credentials and tags."""
        # Placeholder
        logger.warning("bulk_remove_credentials_from_tags is not fully implemented.")
        raise NotImplementedError

    # --- Advanced Credential Store Features ---

    async def get_smart_credentials(self, request_data: SmartCredentialRequest) -> SmartCredentialResponse:
        """Uses the store to find the best credential(s) for a target."""
        # Placeholder - Call store's smart select method
        logger.warning("get_smart_credentials is not fully implemented.")
        # result = self._credential_store.get_smart_credentials(...)
        raise NotImplementedError

    async def optimize_credential_priorities(self, tag_id: str) -> Dict[str, Any]:
        """Optimizes credential priorities for a tag using the store."""
        # Placeholder - Call store's optimize method
        logger.warning("optimize_credential_priorities is not fully implemented.")
        # 1. Verify tag exists
        # result = self._credential_store.optimize_priorities(tag_id)
        raise NotImplementedError

    async def reencrypt_credentials(self, batch_size: int) -> Dict[str, Any]:
        """Initiates re-encryption of credentials via the store."""
        # Placeholder - Call store's re-encryption method
        logger.warning("reencrypt_credentials is not fully implemented.")
        # result = self._credential_store.reencrypt_all(batch_size=batch_size, progress_callback=...)
        # Need to figure out how to handle progress callback in async context if needed
        raise NotImplementedError 