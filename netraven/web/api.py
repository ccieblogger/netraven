"""
API router for the NetRaven web interface.

This module sets up the FastAPI router and includes all the
various sub-routers from other modules.
"""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from netraven.web.routers import (
    auth, users, devices, tags, tag_rules, job_logs, scheduled_jobs, 
    gateway, credentials, audit_logs
)
from netraven.web.routers.backups import router as backups_router, test_router as backups_test_router

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
    backups_router,
    prefix="/backups",
    tags=["backups"],
)
api_router.include_router(
    backups_test_router,
    prefix="/backups-test",
    tags=["backups-test"],
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
api_router.include_router(
    job_logs.router,
    prefix="/job-logs",
    tags=["job_logs"],
)
api_router.include_router(
    scheduled_jobs.router,
    prefix="/scheduled-jobs",
    tags=["scheduled_jobs"],
)
api_router.include_router(
    gateway.router,
    prefix="/gateway",
    tags=["gateway"],
)
api_router.include_router(
    credentials.router,
    prefix="/credentials",
    tags=["credentials"],
)
api_router.include_router(
    audit_logs.router,
    prefix="/audit-logs",
    tags=["audit_logs"],
) 