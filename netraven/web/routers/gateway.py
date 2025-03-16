"""
Gateway router for the NetRaven web API.

This module handles gateway-related endpoints, providing access to
gateway status information and device management.
"""

import requests
from typing import Dict, Any, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status, Request

from netraven.core.logging import get_logger
from netraven.core.auth import get_authorization_header
from netraven.web.auth import get_current_principal, require_scope, Principal, optional_auth

# Setup logger
logger = get_logger("netraven.web.routers.gateway")

# Create router
router = APIRouter(prefix="/gateway", tags=["gateway"])


class GatewayMetrics(BaseModel):
    """Gateway metrics model."""
    request_count: int = 0
    error_count: int = 0
    device_connections: int = 0
    commands_executed: int = 0


@router.get("/status")
async def get_gateway_status(
    principal: Principal = Depends(require_scope(["read:gateway"]))
):
    """
    Get the status of the gateway service.
    
    This endpoint queries the device gateway service for its status,
    including uptime, connected devices, and metrics.
    
    Requires authentication with the 'read:gateway' scope.
    """
    try:
        gateway_url = "http://device_gateway:8001/status"
        
        # Use the same token for calling the gateway
        # In a production environment, consider using service tokens for internal communication
        headers = get_authorization_header(get_current_token())
        
        logger.debug(f"Calling gateway status endpoint: {gateway_url}")
        response = requests.get(gateway_url, headers=headers, timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": data.get("status", "unknown"),
                "version": data.get("version", "unknown"),
                "uptime": data.get("uptime", "0"),
                "connected_devices": data.get("connected_devices", 0),
                "metrics": data.get("metrics", {})
            }
        else:
            logger.warning(f"Gateway returned status code {response.status_code}")
            return {
                "status": "error",
                "message": f"Gateway returned {response.status_code}"
            }
    except Exception as e:
        logger.exception(f"Error fetching gateway status: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }


@router.get("/devices")
async def get_devices(
    principal: Principal = Depends(require_scope(["read:devices"]))
):
    """
    Get a list of connected devices.
    
    This endpoint queries the device gateway service for a list of
    currently connected devices and their status.
    
    Requires authentication with the 'read:devices' scope.
    """
    try:
        gateway_url = "http://device_gateway:8001/devices"
        
        # Use the same token for calling the gateway
        headers = get_authorization_header(get_current_token())
        
        logger.debug(f"Calling gateway devices endpoint: {gateway_url}")
        response = requests.get(gateway_url, headers=headers, timeout=10.0)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Gateway returned status code {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gateway returned status code {response.status_code}"
            )
    except Exception as e:
        logger.exception(f"Error fetching devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with gateway: {str(e)}"
        )


@router.get("/metrics", response_model=GatewayMetrics)
async def get_gateway_metrics(
    principal: Principal = Depends(require_scope(["read:metrics"]))
):
    """
    Get gateway metrics.
    
    This endpoint returns metrics for the device gateway service,
    including request counts, error counts, and device statistics.
    
    Requires authentication with the 'read:metrics' scope.
    """
    try:
        gateway_url = "http://device_gateway:8001/metrics"
        headers = get_authorization_header(get_current_token())
        
        logger.debug(f"Calling gateway metrics endpoint: {gateway_url}")
        response = requests.get(gateway_url, headers=headers, timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            return GatewayMetrics(
                request_count=data.get("request_count", 0),
                error_count=data.get("error_count", 0),
                device_connections=data.get("device_connections", 0),
                commands_executed=data.get("commands_executed", 0)
            )
        else:
            logger.warning(f"Gateway returned status code {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gateway returned status code {response.status_code}"
            )
    except Exception as e:
        logger.exception(f"Error fetching gateway metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with gateway: {str(e)}"
        )


# Helper function to extract current token from request context
def get_current_token() -> str:
    """
    Get the current token from request context.
    
    In a real implementation, this would extract the token from the request context.
    For now, we're using a placeholder API key.
    
    Returns:
        str: The current token or API key
    """
    # This is a placeholder - in a real app, this would extract the token
    # from the request context using something like httpx.AsyncClient context vars
    return "netraven-api-key" 