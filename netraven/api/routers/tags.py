from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_

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

@router.get("/", response_model=schemas.tag.PaginatedTagResponse)
def list_tags(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    name: Optional[str] = None,
    tag_type: Optional[str] = Query(None, alias="type", description="Filter by tag type"),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve a list of tags with pagination and filtering.
    
    - **page**: Page number (starts at 1)
    - **size**: Number of items per page
    - **name**: Filter by tag name (partial match)
    - **type**: Filter by tag type
    """
    query = db.query(models.Tag)
    
    # Apply filters
    filters = []
    if name:
        filters.append(models.Tag.name.ilike(f"%{name}%"))
    if tag_type:
        filters.append(models.Tag.type == tag_type)
    
    # Apply all filters
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count for pagination
    total = query.count()
    
    # Calculate pagination values
    pages = (total + size - 1) // size
    offset = (page - 1) * size
    
    # Get paginated tags
    tags = query.offset(offset).limit(size).all()
    
    # Return paginated response
    return {
        "items": tags,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

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