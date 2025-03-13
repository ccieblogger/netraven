"""
API router for the NetRaven web interface.

This module sets up the FastAPI router and includes all the
various sub-routers from other modules.
"""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from netraven.web.routers import auth, users, devices, backups, tags, tag_rules

# Setup OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Create API router
api_router = APIRouter()

# Include routers from other modules
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"],
)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
)
api_router.include_router(
    devices.router,
    prefix="/devices",
    tags=["devices"],
)
api_router.include_router(
    backups.router,
    prefix="/backups",
    tags=["backups"],
)
api_router.include_router(
    tags.router,
    prefix="/tags",
    tags=["tags"],
)
api_router.include_router(
    tag_rules.router,
    prefix="/tag-rules",
    tags=["tag_rules"],
) 