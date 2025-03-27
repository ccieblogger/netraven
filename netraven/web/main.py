"""
Main FastAPI application for NetRaven.

This module provides the main FastAPI application instance and configuration.
"""

import logging
from typing import Dict, Any
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from netraven.web.database import get_async_session, init_db, close_db
from netraven.core.services.service_factory import get_service_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NetRaven API",
    description="API for network device management and automation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_async_session)) -> Dict[str, Any]:
    """
    Health check endpoint.
    
    This endpoint checks the health of the application and its dependencies.
    
    Returns:
        Dict containing health status information
    """
    try:
        # Get service factory
        factory = get_service_factory(db)
        
        # Check scheduler service
        scheduler_status = "healthy" if factory.scheduler_service else "unavailable"
        
        # Check device communication service
        device_comm_status = "healthy" if factory.device_comm_service else "unavailable"
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "services": {
                "database": "healthy",
                "scheduler": scheduler_status,
                "device_communication": device_comm_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        } 