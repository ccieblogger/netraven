"""
Gateway API routes.

This module provides API routes for interacting with the device gateway service,
including status checks, metrics, and configuration.
"""

from typing import Dict, Any, List, Optional
import requests
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel
import os
import logging
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

from netraven.core.config import get_config, get_default_config_path, load_config
from netraven.core.auth import get_authorization_header
from netraven.web.auth import get_api_key, get_current_active_user, SECRET_KEY, ALGORITHM, API_KEY
from netraven.web.database import get_db
from netraven.web.models import User
from netraven.core.logging import get_logger

# Create logger
logger = get_logger("netraven.web.routers.gateway")

# Load configuration
config_path = get_default_config_path()
config, _ = load_config(config_path)

# Get gateway URL from config or environment
gateway_url = os.environ.get(
    "NETRAVEN_GATEWAY_URL", 
    config.get("gateway", {}).get("url", "http://device_gateway:8001")
)

# Get API key from config or environment
api_key = os.environ.get(
    "NETRAVEN_API_KEY",
    config.get("web", {}).get("api_key", "netraven-api-key")
)

# Create the router
router = APIRouter(
    prefix="/api/gateway",
    tags=["gateway"],
    responses={404: {"description": "Not found"}},
)

# Add an optional OAuth2 scheme that doesn't raise exceptions
class OAuth2PasswordBearerOptional(OAuth2PasswordBearer):
    """
    An OAuth2 password bearer that doesn't raise exceptions.
    """
    async def __call__(self, request: Request) -> Optional[str]:
        try:
            return await super().__call__(request)
        except HTTPException:
            # Return None instead of raising an exception
            return None
        except Exception as e:
            logger.exception(f"Unexpected OAuth2 error: {str(e)}")
            return None

# Create the optional OAuth2 scheme
oauth2_scheme_optional = OAuth2PasswordBearerOptional(tokenUrl="api/auth/token")

async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional)):
    """
    Optional version of get_current_user that doesn't raise exceptions.
    
    Args:
        token: Optional JWT token
        
    Returns:
        User: The current active user or None if not authenticated
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        
        if user is None:
            return None
            
        return user
    except JWTError:
        return None
    except Exception as e:
        logger.exception(f"Unexpected error in get_current_user_optional: {str(e)}")
        return None

def get_current_active_user_optional(current_user: Optional[User] = Depends(get_current_user_optional)):
    """
    Optional version of get_current_active_user that doesn't raise exceptions.
    
    Args:
        current_user: The current user or None if not authenticated
        
    Returns:
        User: The current active user or None if not authenticated
    """
    if not current_user:
        return None
    
    if not current_user.is_active:
        return None
    
    return current_user

class GatewayStatus(BaseModel):
    """Gateway status model."""
    status: str
    version: str
    uptime: str
    connected_devices: int
    metrics: Dict[str, Any]

class GatewayMetrics(BaseModel):
    """Gateway metrics model."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    active_connections: int
    total_connections: int
    error_counts: Dict[str, int]
    device_metrics: Dict[str, Any]

@router.get("/status")
async def get_gateway_status(
    request: Request,
    current_user: Optional[User] = Depends(get_current_active_user_optional),
    x_api_key: Optional[str] = Depends(get_api_key)
):
    """
    Get the status of the device gateway service.
    
    This endpoint checks if the gateway service is available and returns its status.
    """
    
    logger.info("Gateway status endpoint called")
    
    # Log the request headers for debugging
    logger.info(f"Request headers: {dict(request.headers)}")
    
    # Log authentication info
    logger.info(f"Authentication info - User: {current_user is not None}, API Key: {x_api_key is not None}")
    
    # Authentication check
    if not current_user and not x_api_key:
        logger.warning("Authentication failed: No valid user or API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Use the direct container name URL for reliable communication
        gateway_status_url = "http://device_gateway:8001/status"
        logger.info(f"Checking gateway status at {gateway_status_url}")
        
        # Get the API key to use - prioritize the validated key from the dependency
        actual_api_key = x_api_key if x_api_key else api_key
        
        # Log the API key being used (masked for security)
        masked_key = actual_api_key[:4] + "..." if actual_api_key else "None"
        logger.info(f"Using API key for gateway request: {masked_key}")
        
        # Get proper authorization header from core auth module
        headers = get_authorization_header(actual_api_key)
        logger.info(f"Request headers for gateway: {headers}")
        
        # Make the request with sufficient timeout and proper headers
        try:
            response = requests.get(
                gateway_status_url, 
                headers=headers, 
                timeout=10.0
            )
            
            logger.info(f"Gateway response status: {response.status_code}")
            logger.info(f"Gateway response headers: {response.headers}")
            
            # Return a simple dictionary response rather than streaming
            if response.status_code == 200:
                data = response.json()
                result = {
                    "status": data.get("status", "unknown"),
                    "version": data.get("version", "unknown"),
                    "uptime": data.get("uptime", "0"),
                    "connected_devices": data.get("connected_devices", 0),
                    "metrics": data.get("metrics", {})
                }
                logger.info(f"Returning result: {result}")
                return result
            else:
                logger.error(f"Gateway service returned error: {response.status_code}")
                error_response = {
                    "status": "error",
                    "message": f"Gateway returned status code {response.status_code}"
                }
                logger.info(f"Returning error response: {error_response}")
                return error_response
        except requests.exceptions.RequestException as e:
            logger.exception(f"Request error: {str(e)}")
            return {
                "status": "error",
                "message": f"Request error: {str(e)}"
            }
    except Exception as e:
        # Catch all exceptions
        logger.exception(f"Unexpected error: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }

@router.get("/metrics", response_model=GatewayMetrics)
async def get_gateway_metrics(current_user: User = Depends(get_current_active_user)):
    """
    Get metrics from the gateway service.
    
    Returns:
        GatewayMetrics: Gateway metrics information
    """
    config = get_config()
    gateway_url = config.get("gateway", {}).get("url", "http://localhost:8001")
    api_key = config.get("gateway", {}).get("api_key", "")
    
    try:
        response = requests.get(
            f"{gateway_url}/metrics",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gateway service unavailable: {str(e)}"
        )

@router.post("/reset-metrics")
async def reset_gateway_metrics(current_user: User = Depends(get_current_active_user)):
    """
    Reset metrics on the gateway service.
    
    Returns:
        Dict[str, str]: Success message
    """
    config = get_config()
    gateway_url = config.get("gateway", {}).get("url", "http://localhost:8001")
    api_key = config.get("gateway", {}).get("api_key", "")
    
    try:
        response = requests.post(
            f"{gateway_url}/reset-metrics",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5
        )
        response.raise_for_status()
        return {"message": "Gateway metrics reset successfully"}
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gateway service unavailable: {str(e)}"
        )

@router.get("/config")
async def get_gateway_config(current_user: User = Depends(get_current_active_user)):
    """
    Get the configuration of the device gateway service.
    
    This endpoint returns the current configuration of the gateway service.
    """
    try:
        logger.debug(f"Getting gateway config from {gateway_url}/config")
        response = requests.get(
            f"{gateway_url}/config",
            headers={"Authorization": f"Bearer {current_user.id}"},
            timeout=5.0
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.error(f"Gateway connection error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gateway service unavailable: {str(exc)}"
        )
    except Exception as exc:
        logger.exception(f"Unexpected error getting gateway config: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting gateway config: {str(exc)}"
        )

@router.get("/test")
async def test_endpoint():
    """
    Simple test endpoint for the gateway router.
    
    Returns:
        dict: Test response
    """
    return {"status": "ok"}

@router.get("/api-key-test")
async def test_api_key(
    request: Request,
    x_api_key: Optional[str] = Depends(get_api_key)
):
    """
    Test endpoint for API key validation.
    
    Returns:
        dict: Test response with API key status
    """
    logger.info("API key test endpoint called")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"API Key: {x_api_key is not None}")
    
    if x_api_key:
        return {"status": "ok", "api_key_valid": True}
    else:
        return {"status": "error", "api_key_valid": False, "message": "No valid API key provided"}

@router.get("/status-no-auth")
async def get_gateway_status_no_auth(
    request: Request
):
    """
    Get the status of the device gateway service without authentication.
    
    This endpoint checks if the gateway service is available and returns its status.
    """
    
    logger.info("Gateway status-no-auth endpoint called")
    
    # Log the request headers for debugging
    logger.info(f"Request headers: {dict(request.headers)}")
    
    try:
        # Use the direct container name URL for reliable communication
        gateway_status_url = "http://device_gateway:8001/status"
        logger.info(f"Checking gateway status at {gateway_status_url}")
        
        # Get the API key from config
        actual_api_key = api_key
        
        # Log the API key being used (masked for security)
        masked_key = actual_api_key[:4] + "..." if actual_api_key else "None"
        logger.info(f"Using API key for gateway request: {masked_key}")
        
        # Get proper authorization header from core auth module
        headers = get_authorization_header(actual_api_key)
        logger.info(f"Request headers for gateway: {headers}")
        
        # Make the request with sufficient timeout and proper headers
        try:
            response = requests.get(
                gateway_status_url, 
                headers=headers, 
                timeout=10.0
            )
            
            logger.info(f"Gateway response status: {response.status_code}")
            logger.info(f"Gateway response headers: {response.headers}")
            
            # Return a simple dictionary response rather than streaming
            if response.status_code == 200:
                data = response.json()
                result = {
                    "status": data.get("status", "unknown"),
                    "version": data.get("version", "unknown"),
                    "uptime": data.get("uptime", "0"),
                    "connected_devices": data.get("connected_devices", 0),
                    "metrics": data.get("metrics", {})
                }
                logger.info(f"Returning result: {result}")
                return result
            else:
                logger.error(f"Gateway service returned error: {response.status_code}")
                error_response = {
                    "status": "error",
                    "message": f"Gateway returned status code {response.status_code}"
                }
                logger.info(f"Returning error response: {error_response}")
                return error_response
        except requests.exceptions.RequestException as e:
            logger.exception(f"Request error: {str(e)}")
            return {
                "status": "error",
                "message": f"Request error: {str(e)}"
            }
    except Exception as e:
        # Catch all exceptions
        logger.exception(f"Unexpected error: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        } 