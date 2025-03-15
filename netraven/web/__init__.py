"""
Web package for the NetRaven application.

This package provides web-related functionality, including the FastAPI application
and database models.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from netraven.core.config import get_default_config_path, load_config
from netraven.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("netraven.web")

# Load configuration
config_path = get_default_config_path()
config, _ = load_config(config_path)

# Import database and models
from netraven.web.database import init_db, SessionLocal
from netraven.web.models import User, Device, Backup, Tag, TagRule, JobLog, ScheduledJob

# Import routers
from netraven.web.routers import (
    auth,
    devices,
    backups,
    tags,
    tag_rules,
    users,
    job_logs,
    scheduled_jobs,
)

# Create FastAPI app
app = FastAPI(
    title="NetRaven API",
    description="API for the NetRaven network device management system",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("web", {}).get("allowed_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(backups.router)
app.include_router(tags.router)
app.include_router(tag_rules.router)
app.include_router(users.router)
app.include_router(job_logs.router)
app.include_router(scheduled_jobs.router)

# Try to include gateway router if it exists
try:
    from netraven.web.routers import gateway
    app.include_router(gateway.router)
    logger.info("Gateway router included")
except ImportError:
    logger.warning("Gateway router not found, skipping")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Status information
    """
    return {"status": "ok"}

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    """
    # Initialize database
    init_db()
    logger.info("Web service started")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="netraven/web/static"), name="static")
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