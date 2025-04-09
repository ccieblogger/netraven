from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user, require_admin_role
from netraven.db import models
from netraven.api import auth

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    # Most user routes require admin, apply dependency here or per-route
    dependencies=[Depends(require_admin_role)] 
)

@router.post("/", response_model=schemas.user.User, status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.user.UserCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new user (requires admin privileges)."""
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(**user.model_dump(exclude={'password'}), hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Allow user to get their own info without needing admin role
@router.get("/me", response_model=schemas.user.User, tags=["Current User"])
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    """Get current logged in user."""
    return current_user

# Admin routes
@router.get("/", response_model=schemas.user.PaginatedUserPublicResponse)
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    username: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db_session)
):
    """
    Retrieve a list of users with pagination and filtering (requires admin privileges).
    
    - **page**: Page number (starts at 1)
    - **size**: Number of items per page
    - **username**: Filter by username (partial match)
    - **role**: Filter by role (admin, user)
    - **is_active**: Filter by active status
    """
    query = db.query(models.User)
    
    # Apply filters
    filters = []
    if username:
        filters.append(models.User.username.ilike(f"%{username}%"))
    if role:
        filters.append(models.User.role == role)
    if is_active is not None:
        filters.append(models.User.is_active == is_active)
    
    # Apply all filters
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count for pagination
    total = query.count()
    
    # Calculate pagination values
    pages = (total + size - 1) // size if total > 0 else 1
    offset = (page - 1) * size
    
    # Get paginated users
    users = query.offset(offset).limit(size).all()
    
    # Return paginated response
    return {
        "items": users,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/{user_id}", response_model=schemas.user.User)
def get_user(
    user_id: int,
    db: Session = Depends(get_db_session)
):
    """Retrieve a specific user by ID (requires admin privileges)."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=schemas.user.User)
def update_user(
    user_id: int,
    user: schemas.user.UserUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a user (requires admin privileges)."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user.model_dump(exclude_unset=True)

    if "password" in update_data:
        if update_data["password"]:
            hashed_password = auth.get_password_hash(update_data["password"])
            db_user.hashed_password = hashed_password
        del update_data["password"] # Remove password from dict before iterating

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db_session)
):
    """Delete a user (requires admin privileges)."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Add check: prevent deleting the last admin user?

    db.delete(db_user)
    db.commit()
    return None
