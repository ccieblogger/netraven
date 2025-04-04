"""
Asynchronous Tag Rule Management Service for NetRaven.

Handles CRUD for tag rules, testing rules, and applying them to devices.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

# Models and Schemas
from netraven.web.models.tag_rule import TagRule as TagRuleModel
from netraven.web.schemas.tag_rule import TagRule, TagRuleCreate, TagRuleUpdate, TagRuleTest, TagRuleTestResult

# Dependencies (Placeholder - To be injected via __init__)
# from .async_tag_service import AsyncTagService
# from .async_device_service import AsyncDeviceService

logger = logging.getLogger(__name__)

class AsyncTagRuleService:
    """
    Provides methods for managing tag rules asynchronously.
    """
    def __init__(self, db_session: AsyncSession, tag_service: Any, device_service: Any):
        """
        Initialize the tag rule service.
        Args:
            db_session: Async database session.
            tag_service: Instance of AsyncTagService.
            device_service: Instance of AsyncDeviceService.
        """
        self._db_session = db_session
        self._tag_service = tag_service # Store dependency
        self._device_service = device_service # Store dependency

    # --- CRUD Methods --- 

    async def get_rule_by_id(self, rule_id: str) -> Optional[TagRuleModel]:
        """Fetches a tag rule by ID."""
        # Placeholder for crud.get_tag_rule
        stmt = select(TagRuleModel).where(TagRuleModel.id == rule_id)
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_rules(self, tag_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[TagRuleModel]:
        """Lists tag rules, optionally filtered by tag_id."""
        # Placeholder for crud.get_tag_rules
        stmt = select(TagRuleModel).order_by(TagRuleModel.name).offset(skip).limit(limit)
        if tag_id:
            stmt = stmt.where(TagRuleModel.tag_id == tag_id)
        result = await self._db_session.execute(stmt)
        return result.scalars().all()

    async def create_rule(self, rule_data: TagRuleCreate) -> TagRuleModel:
        """Creates a new tag rule."""
        # Placeholder for crud.create_tag_rule & tag check logic
        # 1. Check if associated tag exists (using injected tag_service)
        tag = await self._tag_service.get_tag_by_id(rule_data.tag_id)
        if not tag:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag with ID {rule_data.tag_id} not found")

        # 2. Create rule object
        db_rule = TagRuleModel(**rule_data.dict())
        self._db_session.add(db_rule)
        try:
            await self._db_session.flush()
            await self._db_session.refresh(db_rule)
            return db_rule
        except IntegrityError as e:
             await self._db_session.rollback()
             logger.error(f"DB integrity error creating tag rule {rule_data.name}: {e}")
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag rule could not be created due to integrity constraint.")
        except Exception as e:
             await self._db_session.rollback()
             logger.error(f"Error during tag rule creation flush/refresh: {e}")
             raise

    async def update_rule(self, rule_id: str, rule_data: TagRuleUpdate) -> Optional[TagRuleModel]:
        """Updates an existing tag rule."""
        # Placeholder for crud.update_tag_rule & tag check logic
        db_rule = await self.get_rule_by_id(rule_id)
        if not db_rule:
            return None

        update_data = rule_data.dict(exclude_unset=True)
        
        # Check tag existence if tag_id is being changed
        if 'tag_id' in update_data and update_data['tag_id'] != db_rule.tag_id:
            tag = await self._tag_service.get_tag_by_id(update_data['tag_id'])
            if not tag:
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag with ID {update_data['tag_id']} not found")

        for key, value in update_data.items():
            if hasattr(db_rule, key):
                setattr(db_rule, key, value)
            else:
                logger.warning(f"Attempted to update non-existent attribute '{key}' on tag rule {rule_id}")

        try:
            await self._db_session.flush()
            await self._db_session.refresh(db_rule)
            return db_rule
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error during tag rule update flush/refresh: {e}")
            raise

    async def delete_rule(self, rule_id: str) -> bool:
        """Deletes a tag rule."""
        # Placeholder for crud.delete_tag_rule
        db_rule = await self.get_rule_by_id(rule_id)
        if not db_rule:
            return False
            
        await self._db_session.delete(db_rule)
        try:
            await self._db_session.flush()
            return True
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error during tag rule deletion flush: {e}")
            raise

    # --- Rule Application & Testing --- 

    async def apply_rule(self, rule_id: str) -> Dict[str, Any]:
        """Applies a rule to all devices. (Placeholder)"""
        # Placeholder for crud.apply_rule
        # 1. Get the rule
        rule = await self.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
        # 2. Get the associated tag
        tag = await self._tag_service.get_tag_by_id(rule.tag_id) 
        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated tag not found")
        # 3. Get all devices (potentially optimize with pagination/filtering later)
        all_devices = await self._device_service.list_devices(limit=10000) # Use high limit for now
        # 4. Evaluate rule against each device
        # 5. Add/remove tag from device using self._device_service methods
        # 6. Collect results
        logger.info(f"Placeholder: Applying rule {rule_id} ({rule.name}) for tag {tag.name}")
        applied_count = 0
        removed_count = 0
        # ... (evaluation loop placeholder) ...
        return {"message": f"Rule '{rule.name}' applied.", "tag_applied_count": applied_count, "tag_removed_count": removed_count}
        
    async def test_rule(self, rule_test_data: TagRuleTest) -> TagRuleTestResult:
        """Tests a rule against sample data. (Placeholder)"""
        # Placeholder for crud.test_rule
        # This likely involves parsing the rule conditions and evaluating them 
        # against the provided rule_test_data.device_attributes.
        logger.info(f"Placeholder: Testing rule conditions: {rule_test_data.conditions}")
        match = True # Fake result
        # ... (evaluation logic placeholder) ...
        return TagRuleTestResult(match=match, evaluated_conditions=rule_test_data.conditions) 