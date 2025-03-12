"""
Web interface for NetRaven.

This module provides a modern web interface for managing network device
backups, configuration management, and automation tasks.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from typing import Dict, Any

# Import internal modules
from netraven.core.config import load_config, get_default_config_path
from netraven.core.logging import get_logger
from netraven.web.database import init_db

# Create logger
logger = get_logger("netraven.web")

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, storage = load_config(config_path)

# Initialize the database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {e}")

# Create FastAPI app
app = FastAPI(
    title="NetRaven API",
    description="API for network device configuration management",
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
from netraven.web.routers import auth, devices, backups

# Mount routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(backups.router, prefix="/api/backups", tags=["Backups"])

@app.get("/api")
async def api_root() -> Dict[str, Any]:
    """Root API endpoint that provides information about available endpoints."""
    return {
        "name": "NetRaven API",
        "version": "0.1.0",
        "description": "API for network device configuration management",
        "endpoints": {
            "health": "/api/health",
            "authentication": {
                "login": "/api/auth/token",
                "current_user": "/api/auth/users/me"
            },
            "devices": {
                "list": "/api/devices",
                "detail": "/api/devices/{device_id}",
                "backup": "/api/devices/{device_id}/backup"
            },
            "backups": {
                "list": "/api/backups",
                "detail": "/api/backups/{backup_id}",
                "content": "/api/backups/{backup_id}/content",
                "compare": "/api/backups/compare",
                "restore": "/api/backups/{backup_id}/restore"
            }
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0"
    } 