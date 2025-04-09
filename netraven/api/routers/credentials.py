from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user, require_admin_role
from netraven.db import models
from netraven.api import auth # Import auth utils for hashing

router = APIRouter(
    prefix="/credentials",
    tags=["Credentials"],
    dependencies=[Depends(get_current_active_user)] # Apply auth to all credential routes
)

# Helper to get tags (reuse from devices.py or keep local? Reusing might be better)
# For now, copy the helper here. Consider moving to a utils module later.
def get_tags_by_ids(db: Session, tag_ids: List[int]) -> List[models.Tag]:
    tags = db.query(models.Tag).filter(models.Tag.id.in_(tag_ids)).all()
    if len(tags) != len(tag_ids):
        found_ids = {tag.id for tag in tags}
        missing_ids = [tag_id for tag_id in tag_ids if tag_id not in found_ids]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag(s) not found: {missing_ids}")
    return tags

@router.post("/", response_model=schemas.credential.Credential, status_code=status.HTTP_201_CREATED)
def create_credential(
    credential: schemas.credential.CredentialCreate,
    db: Session = Depends(get_db_session),
):
    """Create a new credential set.

    Password will be hashed before storing.
    """
    # Optionally check for duplicate username/description? Depends on requirements.
    
    hashed_password = auth.get_password_hash(credential.password)
    
    db_credential = models.Credential(
        **credential.model_dump(exclude={'tags', 'password'}), 
        hashed_password=hashed_password # Store the hash
    )
    
    # Handle tags if provided
    if credential.tags:
        tags = get_tags_by_ids(db, credential.tags)
        db_credential.tags = tags

    db.add(db_credential)
    db.commit()
    db.refresh(db_credential)
    # Eager load tags for response
    db.query(models.Credential).options(selectinload(models.Credential.tags)).filter(models.Credential.id == db_credential.id).first()
    return db_credential

@router.get("/", response_model=schemas.credential.PaginatedCredentialResponse)
def list_credentials(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    username: Optional[str] = None,
    priority: Optional[int] = None,
    tag_id: Optional[List[int]] = Query(None, description="Filter by tag IDs"),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve a list of credentials with pagination and filtering (passwords are not returned).
    
    - **page**: Page number (starts at 1)
    - **size**: Number of items per page
    - **username**: Filter by username (partial match)
    - **priority**: Filter by exact priority value
    - **tag_id**: Filter by tag IDs (multiple allowed)
    """
    query = db.query(models.Credential).options(selectinload(models.Credential.tags))
    
    # Apply filters
    filters = []
    if username:
        filters.append(models.Credential.username.ilike(f"%{username}%"))
    if priority is not None:
        filters.append(models.Credential.priority == priority)
    
    # Apply all filters
    if filters:
        query = query.filter(and_(*filters))
    
    # Apply tag filter if specified
    if tag_id:
        query = query.join(models.Credential.tags).filter(models.Tag.id.in_(tag_id)).group_by(models.Credential.id)
    
    # Get total count for pagination
    total = query.count()
    
    # Calculate pagination values
    pages = (total + size - 1) // size
    offset = (page - 1) * size
    
    # Get paginated credentials
    credentials = query.offset(offset).limit(size).all()
    
    # Return paginated response
    return {
        "items": credentials,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/{credential_id}", response_model=schemas.credential.Credential)
def get_credential(
    credential_id: int,
    db: Session = Depends(get_db_session)
):
    """Retrieve a specific credential set by ID (password is not returned)."""
    db_credential = (
        db.query(models.Credential)
        .options(selectinload(models.Credential.tags))
        .filter(models.Credential.id == credential_id)
        .first()
    )
    if db_credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
    return db_credential

@router.put("/{credential_id}", response_model=schemas.credential.Credential)
def update_credential(
    credential_id: int,
    credential: schemas.credential.CredentialUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a credential set.
    
    If password is provided, it will be re-hashed.
    """
    db_credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
    if db_credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")

    update_data = credential.model_dump(exclude_unset=True)

    # Update simple attributes and hash password if provided
    for key, value in update_data.items():
        if key == "password":
            if value: # Check if password is actually provided
                db_credential.hashed_password = auth.get_password_hash(value)
        elif key != "tags":
            setattr(db_credential, key, value)

    # Handle tags update
    if "tags" in update_data:
        if update_data["tags"] is None:
            db_credential.tags = []
        else:
            tags = get_tags_by_ids(db, update_data["tags"])
            db_credential.tags = tags

    db.commit()
    db.refresh(db_credential)
    # Eager load tags again for the response model
    db.query(models.Credential).options(selectinload(models.Credential.tags)).filter(models.Credential.id == credential_id).first()
    return db_credential

@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credential(
    credential_id: int,
    db: Session = Depends(get_db_session),
    _: models.User = Depends(require_admin_role) # Protect deletion
):
    """Delete a credential set."""
    db_credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
    if db_credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")

    db.delete(db_credential)
    db.commit()
    return None 