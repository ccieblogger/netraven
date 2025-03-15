"""
Web interface for NetRaven.

This module provides a modern web interface for managing network device
backups, configuration management, and automation tasks.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from pathlib import Path
from typing import Dict, Any
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import internal modules
from netraven.core.config import load_config, get_default_config_path
from netraven.core.logging import get_logger
from netraven.web.database import init_db, SessionLocal
from netraven.web.routes import (
    auth,
    users,
    devices,
    jobs,
    backups,
    dashboard,
    gateway
)

# Create logger
logger = get_logger("netraven.web")

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, storage = load_config(config_path)

# Initialize the database
try:
    init_db()
    logger.info("Database initialized successfully")
    
    # Ensure default admin user exists
    from netraven.web.startup import ensure_default_admin
    
    # Create a database session
    db = SessionLocal()
    try:
        ensure_default_admin(db)
    except Exception as e:
        logger.warning(f"Could not create default admin user: {e}")
    finally:
        db.close()
        
except Exception as e:
    logger.error(f"Error initializing database: {e}")

# Create FastAPI app
app = FastAPI(
    title="NetRaven",
    description="API for network device configuration management and backup.",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config["web"]["allowed_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
# These imports are placed here to avoid circular imports
from netraven.web.routers import auth, devices, backups, tags, tag_rules, users, job_logs, scheduled_jobs

# Mount routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(backups.router, prefix="/api/backups", tags=["Backups"])
app.include_router(tags.router, prefix="/api/tags", tags=["Tags"])
app.include_router(tag_rules.router, prefix="/api/tag-rules", tags=["Tag Rules"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(job_logs.router, prefix="/api/job-logs", tags=["Job Logs"])
app.include_router(scheduled_jobs.router, prefix="/api/scheduled-jobs", tags=["Scheduled Jobs"])

# Initialize scheduler service
try:
    from netraven.web.services import get_scheduler_service
    scheduler_service = get_scheduler_service()
    scheduler_service.start()
    logger.info("Scheduler service started successfully")
except Exception as e:
    logger.error(f"Error starting scheduler service: {e}")

# Include additional routers
app.include_router(jobs.router)
app.include_router(dashboard.router)
app.include_router(gateway.router)

@app.get("/api")
async def api_root(request: Request) -> JSONResponse:
    """Root API endpoint that provides information about available endpoints."""
    base_url = str(request.base_url).rstrip('/')
    
    # Create a response that resembles the example in the screenshot
    response_body = {
        "auth": f"{base_url}/api/auth",
        "devices": f"{base_url}/api/devices",
        "backups": f"{base_url}/api/backups",
        "tags": f"{base_url}/api/tags",
        "tag_rules": f"{base_url}/api/tag-rules",
        "job_logs": f"{base_url}/api/job-logs",
        "scheduled_jobs": f"{base_url}/api/scheduled-jobs",
        "health": f"{base_url}/api/health",
        "docs": f"{base_url}/docs"
    }
    
    return JSONResponse(
        content=response_body,
        headers={
            "Content-Type": "application/json",
            "Vary": "Accept"
        }
    )

@app.get("/")
async def redirect_to_api():
    """Redirect root to API root."""
    return {"message": "Welcome to NetRaven. API available at /api"}

@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0"
    }

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="netraven/web/static"), name="static")
    templates = Jinja2Templates(directory="netraven/web/templates")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    ) 