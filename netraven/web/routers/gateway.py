"""
Gateway API routes.

This module provides API routes for interacting with the device gateway service,
including status checks, metrics, and configuration.
"""

from typing import Dict, Any, List, Optional
import requests
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
import os
import logging

from netraven.core.config import get_config, get_default_config_path, load_config
from netraven.web.auth import get_current_active_user, get_api_key
from netraven.web.models.user import User
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

router = APIRouter(
    prefix="/api/gateway",
    tags=["gateway"],
    responses={404: {"description": "Not found"}},
)

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
    current_user: Optional[User] = Depends(get_current_active_user),
    x_api_key: Optional[str] = Depends(get_api_key)
):
    """
    Get the status of the device gateway service.
    
    This endpoint checks if the gateway service is available and returns its status.
    """
    logger.debug("Gateway status endpoint called")
    logger.debug(f"Current user: {current_user}")
    logger.debug(f"API key header: {x_api_key}")
    
    if not current_user and not x_api_key:
        logger.warning("Authentication failed: No valid user or API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Define a default response in case of errors
    default_response = {
        "status": "unknown",
        "version": "unknown",
        "uptime": 0,
        "connected_devices": 0,
        "message": "Gateway status unknown"
    }
    
    try:
        # Use direct container name for reliable communication
        gateway_health_url = "http://device_gateway:8001/health"
        logger.debug(f"Checking gateway status at {gateway_health_url}")
        
        # Make the request without headers first for simplicity
        response = requests.get(gateway_health_url, timeout=2.0)
        logger.debug(f"Gateway response status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                logger.debug(f"Gateway response data: {response_data}")
                
                # Ensure the response has the expected fields
                result = {
                    "status": response_data.get("status", "unknown"),
                    "version": response_data.get("version", "unknown"),
                    "uptime": response_data.get("uptime", 0),
                    "connected_devices": response_data.get("connected_devices", 0)
                }
                
                return result
            except ValueError as json_err:
                logger.error(f"Invalid JSON response from gateway: {json_err}")
                default_response["message"] = "Invalid response format from gateway"
                return default_response
        else:
            logger.error(f"Gateway returned non-200 status code: {response.status_code}")
            default_response["message"] = f"Gateway returned status code {response.status_code}"
            return default_response
            
    except requests.exceptions.Timeout:
        logger.error("Gateway connection timed out")
        default_response["status"] = "timeout"
        default_response["message"] = "Gateway service connection timed out"
        return default_response
        
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to gateway service")
        default_response["status"] = "offline"
        default_response["message"] = "Could not connect to gateway service"
        return default_response
        
    except Exception as exc:
        logger.exception(f"Unexpected error checking gateway status: {exc}")
        default_response["status"] = "error"
        default_response["message"] = f"Error checking gateway status: {str(exc)}"
        return default_response

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