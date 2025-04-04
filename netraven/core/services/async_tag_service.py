"""
Asynchronous Tag Management Service for NetRaven.

Handles CRUD operations for tags and managing associations with devices/credentials.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

# Models and Schemas
from netraven.web.models.tag import Tag as TagModel
from netraven.web.schemas.tag import Tag, TagCreate, TagUpdate
from netraven.web.models.device import Device as DeviceModel # For association logic

logger = logging.getLogger(__name__)

class AsyncTagService:
    """
    Provides methods for managing tag entities asynchronously.
    """
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the tag service.
        Args:
            db_session: Async database session.
        """
        self._db_session = db_session

    async def get_tag_by_id(self, tag_id: str) -> Optional[TagModel]:
        """Fetches a tag by ID."""
        stmt = select(TagModel).where(TagModel.id == tag_id)
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tag_by_name(self, name: str) -> Optional[TagModel]:
        """Fetches a tag by name (case-insensitive)."""
        stmt = select(TagModel).where(TagModel.name.ilike(name))
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tags(self, skip: int = 0, limit: int = 100) -> List[TagModel]:
        """Lists tags with pagination."""
        stmt = select(TagModel).order_by(TagModel.name).offset(skip).limit(limit)
        result = await self._db_session.execute(stmt)
        return result.scalars().all()

    async def create_tag(self, tag_data: TagCreate) -> TagModel:
        """Creates a new tag."""
        existing_tag = await self.get_tag_by_name(tag_data.name)
        if existing_tag:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tag with name '{tag_data.name}' already exists")
        
        db_tag = TagModel(**tag_data.dict())
        self._db_session.add(db_tag)
        try:
            await self._db_session.flush()
            await self._db_session.refresh(db_tag)
            return db_tag
        except IntegrityError as e:
             await self._db_session.rollback()
             logger.error(f"DB integrity error creating tag {tag_data.name}: {e}")
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tag {tag_data.name} could not be created due to integrity constraint.")
        except Exception as e:
             await self._db_session.rollback()
             logger.error(f"Error during tag creation flush/refresh: {e}")
             raise

    async def update_tag(self, tag_id: str, tag_data: TagUpdate) -> Optional[TagModel]:
        """Updates an existing tag."""
        db_tag = await self.get_tag_by_id(tag_id)
        if not db_tag:
            return None
        
        update_data = tag_data.dict(exclude_unset=True)
        
        # Check for duplicate name if name is being changed
        if 'name' in update_data and update_data['name'].lower() != db_tag.name.lower():
            existing_tag = await self.get_tag_by_name(update_data['name'])
            if existing_tag and existing_tag.id != tag_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tag with name '{update_data['name']}' already exists")
                
        for key, value in update_data.items():
            if hasattr(db_tag, key):
                setattr(db_tag, key, value)
            else:
                logger.warning(f"Attempted to update non-existent attribute '{key}' on tag {tag_id}")
        
        try:
            await self._db_session.flush()
            await self._db_session.refresh(db_tag)
            return db_tag
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error during tag update flush/refresh: {e}")
            raise

    async def delete_tag(self, tag_id: str) -> bool:
        """Deletes a tag. Ensures associations are handled (or prevented)."""
        # Check associations first? Or let DB handle constraint?
        # For now, assume DB constraint or cascade will handle. Fetch tag first.
        db_tag = await self.get_tag_by_id(tag_id)
        if not db_tag:
            return False

        # TODO: Check if tag is associated with devices/credentials? 
        # Prevent deletion if associated, or handle cascade?
        # stmt_assoc_count = select(func.count()).select_from(device_tags).where(device_tags.c.tag_id == tag_id) # Example
        # count = await self._db_session.scalar(stmt_assoc_count)
        # if count > 0:
        #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete tag: Still associated with resources.")
            
        await self._db_session.delete(db_tag)
        try:
            await self._db_session.flush()
            return True
        except IntegrityError as e: # Catch potential FK violations if not checked above
            await self._db_session.rollback()
            logger.warning(f"Could not delete tag {tag_id} due to existing associations: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete tag: Still associated with resources.")
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error during tag deletion flush: {e}")
            raise
            
    # --- Association Methods --- 
    async def get_devices_for_tag(self, tag_id: str, skip: int = 0, limit: int = 100) -> List[DeviceModel]:
        """Get devices associated with a specific tag."""
        # Need efficient query - potentially query DeviceModel filtering by tags relationship
        stmt = (
            select(DeviceModel)
            .join(DeviceModel.tags)
            .where(TagModel.id == tag_id)
            .options(selectinload(DeviceModel.tags)) # Optional: reload tags if needed
            .order_by(DeviceModel.hostname)
            .offset(skip)
            .limit(limit)
        )
        result = await self._db_session.execute(stmt)
        return result.scalars().unique().all()
        
    # TODO: Add methods for bulk_assign, bulk_unassign 