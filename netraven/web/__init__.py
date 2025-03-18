"""
Web module for NetRaven.

This module provides the web interface for the NetRaven application,
using FastAPI to expose a REST API.
"""

import os
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from netraven.core.logging import get_logger
from netraven.web.database import init_db
from netraven.web.routers import gateway, auth
from netraven.web.api import api_router  # Import the API router
from netraven.scripts.init_container import setup_initial_tokens

# Setup logger
logger = get_logger("netraven.web")

# Create FastAPI app
app = FastAPI(
    title="NetRaven API",
    description="API for the NetRaven device management platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://0.0.0.0:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://frontend:8080",  # Docker service name
        "http://api:8000",       # Docker service name
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=86400  # 24 hours cache for preflight requests
)

# Register startup events
@app.on_event("startup")
async def startup_event():
    """Initialize services during app startup."""
    logger.info("Starting web service...")
    
    # Initialize database
    init_db()
    
    # Initialize authentication tokens
    try:
        setup_initial_tokens()
        logger.info("Authentication tokens initialized")
    except Exception as e:
        logger.error(f"Error initializing authentication tokens: {str(e)}")
    
    # Create default admin user if it doesn't exist
    try:
        from netraven.web.database import SessionLocal
        from netraven.web.startup import ensure_default_admin
        
        db = SessionLocal()
        try:
            ensure_default_admin(db)
            logger.info("Default admin user initialization complete")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error ensuring default admin user: {str(e)}")
    
    logger.info("Web service started")


# Add exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> Response:
    """Global exception handler for unhandled exceptions."""
    logger.exception(f"Unhandled exception for request {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/api/health", tags=["system"])
async def health_check():
    """
    Simple health check endpoint.
    
    Returns 200 OK if the service is running.
    """
    return {"status": "ok"}


# Custom OpenAPI schema
def custom_openapi() -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema.
    
    Returns:
        Dict[str, Any]: The OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Customize schema here if needed
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Include routers
app.include_router(api_router, prefix="/api")


__all__ = ["app"] 