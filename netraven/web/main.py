"""
Main FastAPI application for NetRaven.

This module provides the main FastAPI application instance and configuration.
"""

import logging
from typing import Dict, Any
from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.responses import JSONResponse

from netraven.web.database import get_async_session, init_db, close_db
from netraven.core.services.service_factory import get_service_factory
# Import the main API router
from netraven.web.api import api_router
# Import rate limiter startup/shutdown
from netraven.web.auth.rate_limiting import start_rate_limit_cleanup, stop_rate_limit_cleanup
# Import Token Validation Middleware
from netraven.web.middleware.token_validation import TokenValidationMiddleware
# Import Global Error Handling Middleware
from netraven.web.middleware.error_handling import GlobalErrorHandlingMiddleware

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

# Add Global Error Handling Middleware (early in the stack)
app.add_middleware(GlobalErrorHandlingMiddleware)

# Add Token Validation Middleware (add this before CORS or other middleware that might depend on auth)
app.add_middleware(TokenValidationMiddleware)

# Include the main API router with a prefix
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        # Start rate limiter cleanup task
        await start_rate_limit_cleanup()
        logger.info("Rate limiter cleanup task started")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        # Stop rate limiter cleanup task
        await stop_rate_limit_cleanup()
        logger.info("Rate limiter cleanup task stopped")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/health", tags=["health"])
async def health_check(request: Request, db: AsyncSession = Depends(get_async_session)) -> Dict[str, Any]:
    """
    Health check endpoint.
    
    This endpoint checks the health of the application and its core dependencies,
    such as the database connection. Requires authentication for detailed checks.
    
    Returns:
        Dict containing health status information
    """
    # Basic check - always check DB connection
    db_status = "healthy"
    db_error = None
    try:
        # Perform a simple query to check DB connection
        await db.execute(select(1))
        logger.debug("Health check: Database connection successful.")
    except Exception as e:
        logger.error(f"Health check failed: Database connection error: {e}", exc_info=True)
        db_status = "unhealthy"
        db_error = str(e)

    # Default status is unhealthy if DB fails
    overall_status = db_status
    
    # Detailed checks (optional, potentially require auth)
    scheduler_status = "unknown"
    device_comm_status = "unknown"
    token_store_status = "unknown"
    
    # Check if a principal exists (meaning token validation likely ran)
    # This is a proxy for checking if auth-requiring checks can proceed
    # A dedicated health check token might be better for production.
    principal = getattr(request.state, "principal", None)
    if principal: 
        try:
            # Use factory for more detailed checks if authenticated
            factory = get_service_factory(db)
            
            # Check scheduler service (example: check connection or basic function)
            # Replace with actual check if scheduler client exists/has health check
            scheduler_status = "healthy" # Assume healthy if factory has it
            
            # Check device communication service (example)
            # Replace with actual check
            device_comm_status = "healthy" # Assume healthy
            
            # Check token store (example: can we retrieve a known key or info?)
            # Replace with actual check if token store has health check method
            # await factory.token_store.health_check() # hypothetical
            token_store_status = "healthy" # Assume healthy
            
            # If all checks passed (including DB), overall status is healthy
            if db_status == "healthy" and scheduler_status == "healthy" and device_comm_status == "healthy" and token_store_status == "healthy":
                overall_status = "healthy"
        except Exception as e:
            logger.error(f"Health check failed during detailed checks: {e}", exc_info=True)
            overall_status = "unhealthy" # Mark unhealthy if detailed checks fail
            # Optionally add specific component error details

    response_body = {
        "status": overall_status,
        "version": app.version,
        "services": {
            "database": {"status": db_status, "error": db_error},
            "scheduler": {"status": scheduler_status}, 
            "device_communication": {"status": device_comm_status},
            "token_store": {"status": token_store_status}
        }
    }

    # Return 503 if overall status is unhealthy
    status_code = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=response_body, status_code=status_code)

# --- Add other application routes below --- 