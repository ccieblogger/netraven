from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user, require_admin_role
from netraven.db import models

router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
    dependencies=[Depends(get_current_active_user)] # Apply auth to all tag routes
)

@router.post("/", response_model=schemas.tag.Tag, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag: schemas.tag.TagCreate,
    db: Session = Depends(get_db_session),
):
    """Create a new tag."""
    existing_tag = db.query(models.Tag).filter(models.Tag.name == tag.name).first()
    if existing_tag:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag name already exists")

    db_tag = models.Tag(**tag.model_dump())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.get("/", response_model=List[schemas.tag.Tag])
def list_tags(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Retrieve a list of tags."""
    tags = db.query(models.Tag).offset(skip).limit(limit).all()
    return tags

@router.get("/{tag_id}", response_model=schemas.tag.Tag)
def get_tag(
    tag_id: int,
    db: Session = Depends(get_db_session)
):
    """Retrieve a specific tag by ID."""
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return db_tag

@router.put("/{tag_id}", response_model=schemas.tag.Tag)
def update_tag(
    tag_id: int,
    tag: schemas.tag.TagUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a tag."""
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    update_data = tag.model_dump(exclude_unset=True)

    # Check for name conflict if name is being changed
    if 'name' in update_data and update_data['name'] != db_tag.name:
        if db.query(models.Tag).filter(models.Tag.name == update_data['name']).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag name already exists")

    for key, value in update_data.items():
        setattr(db_tag, key, value)

    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db_session),
    #_: models.User = Depends(require_admin_role) # Example: Protect deletion
):
    """Delete a tag.

    Note: Deleting a tag might affect associated devices/jobs/credentials.
    Consider implications or add cascading behavior if needed.
    """
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    db.delete(db_tag)
    db.commit()
    return None 