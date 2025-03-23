"""
Package containing FastAPI routers for the NetRaven web interface.
"""

from fastapi import APIRouter
from netraven.web.routers import (
    devices,
    users,
    tags,
    tag_rules,
    job_logs,
    scheduled_jobs,
    backups,
    credentials,
    keys,
    admin_settings,
)

# Create main router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(tag_rules.router, prefix="/tag-rules", tags=["tag-rules"])
api_router.include_router(job_logs.router, prefix="/job-logs", tags=["job-logs"])
api_router.include_router(scheduled_jobs.router, prefix="/scheduled-jobs", tags=["scheduled-jobs"])
api_router.include_router(backups.router, prefix="/backups", tags=["backups"])
api_router.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
api_router.include_router(keys.router, prefix="/keys", tags=["keys"])
api_router.include_router(admin_settings.router, prefix="/admin-settings", tags=["admin-settings"])

# Export the router
__all__ = ["api_router"] 