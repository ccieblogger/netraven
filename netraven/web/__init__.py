"""
Web package for the NetRaven application.

This package provides web-related functionality, including the FastAPI application
and database models.
"""

import os
import logging
from typing import List, Optional
import importlib

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from netraven.core.config import get_default_config_path, load_config
from netraven.core.logging import configure_logging, get_logger

# Setup logging
configure_logging()
logger = get_logger("netraven.web")

# Load configuration
config_path = get_default_config_path()
config, _ = load_config(config_path)

# Import database and models
from netraven.web.database import init_db

# Detect and include all routers
from netraven.web.routers import (
    auth,
    devices,
    backups,
    tags,
    tag_rules,
    users,
    job_logs,
    scheduled_jobs,
    gateway
)

# Create FastAPI app
app = FastAPI(
    title="NetRaven API",
    description="Network automation and management platform API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://0.0.0.0:8080",
        "http://0.0.0.0:8000",
    ],  # Explicitly list allowed origins
    allow_credentials=True,  # Allow credentials
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Authorization", "X-API-Key"],
    max_age=86400,  # Cache preflight requests for 24 hours
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

# Add OPTIONS handler for CORS preflight requests
@app.options("/{rest_of_path:path}")
async def options_handler(rest_of_path: str):
    """Handle OPTIONS requests for CORS preflight."""
    return {}

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
    """
    Global exception handler.
    
    Args:
        request: FastAPI request
        exc: Exception
    """
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
        },
    ) 