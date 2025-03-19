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
from netraven.core.auth import get_authorization_header, extract_token_from_header
from netraven.web.auth import get_current_principal, require_scope, Principal, optional_auth

# Setup logger
logger = get_logger("netraven.web.routers.gateway")

# Create router
router = APIRouter(prefix="", tags=["gateway"])


class GatewayMetrics(BaseModel):
    """Gateway metrics model."""
    request_count: int = 0
    error_count: int = 0
    device_connections: int = 0
    commands_executed: int = 0


@router.get("/status")
async def get_gateway_status(
    request: Request,
    principal: Optional[Principal] = Depends(optional_auth(["read:gateway"]))
):
    """
    Get the status of the gateway service.
    
    This endpoint queries the device gateway service for its status,
    including uptime, connected devices, and metrics.
    
    Requires authentication with the 'read:gateway' scope.
    """
    # Log access if principal is provided
    if principal:
        logger.info(f"Access granted: user={principal.username}, resource=gateway, scope=read:gateway, action=status")
    
    try:
        gateway_url = "http://device_gateway:8001/status"
        
        # Use the same token for calling the gateway if available
        # Otherwise, use the API token for internal communication
        headers = {}
        if principal:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                headers = {"Authorization": auth_header}
        
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
            logger.warning(f"Gateway service returned non-200 status: code={response.status_code}, body={response.text[:100]}")
            return {
                "status": "error",
                "message": f"Gateway returned status code {response.status_code}"
            }
    except requests.RequestException as e:
        # Standardized error handling for request exceptions
        logger.error(f"Error connecting to gateway service: {str(e)}")
        return {
            "status": "error",
            "message": f"Error connecting to gateway: {str(e)}"
        }
    except Exception as e:
        # Standardized error handling for other exceptions
        logger.exception(f"Unexpected error fetching gateway status: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }


@router.get("/devices")
async def get_devices(
    request: Request,
    principal: Principal = Depends(require_scope(["read:devices"]))
):
    """
    Get a list of devices connected to the gateway.
    
    This endpoint queries the device gateway service for connected devices.
    
    Requires authentication with the 'read:devices' scope.
    """
    try:
        # Log access granted
        logger.info(f"Access granted: user={principal.username}, resource=gateway:devices, scope=read:devices, action=list")
        
        gateway_url = "http://device_gateway:8001/devices"
        
        # Use the same token for calling the gateway
        headers = {}
        auth_header = request.headers.get("Authorization")
        if auth_header:
            headers = {"Authorization": auth_header}
        
        logger.debug(f"Calling gateway devices endpoint: {gateway_url}")
        response = requests.get(gateway_url, headers=headers, timeout=10.0)
        
        if response.status_code != 200:
            logger.error(f"Gateway returned error: {response.status_code} - {response.text[:100]}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gateway service error: {response.status_code}"
            )
                
        return response.json()
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except requests.RequestException as e:
        # Standardized error handling for request exceptions
        logger.error(f"Error communicating with gateway: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with gateway: {str(e)}"
        )
    except Exception as e:
        # Standardized error handling for other exceptions
        logger.exception(f"Unexpected error retrieving devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error retrieving devices: {str(e)}"
        )


@router.get("/metrics", response_model=GatewayMetrics)
async def get_gateway_metrics(
    request: Request,
    principal: Optional[Principal] = Depends(optional_auth(["read:metrics"]))
):
    """
    Get gateway metrics.
    
    This endpoint queries the device gateway service for metrics on
    requests, errors, device connections, and commands executed.
    
    Requires authentication with the 'read:metrics' scope.
    """
    try:
        # Log access if principal is provided
        if principal:
            logger.info(f"Access granted: user={principal.username}, resource=gateway:metrics, scope=read:metrics, action=get")
        
        gateway_url = "http://device_gateway:8001/metrics"
        
        # Use the same token for calling the gateway if available
        headers = {}
        if principal:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                headers = {"Authorization": auth_header}
        
        logger.debug(f"Calling gateway metrics endpoint: {gateway_url}")
        response = requests.get(gateway_url, headers=headers, timeout=10.0)
        
        if response.status_code != 200:
            logger.error(f"Gateway returned error: {response.status_code} - {response.text[:100]}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gateway service error: {response.status_code}"
            )
                
        metrics_data = response.json()
        return GatewayMetrics(**metrics_data)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except requests.RequestException as e:
        # Standardized error handling for request exceptions
        logger.error(f"Error communicating with gateway: {str(e)}")
        # Return default metrics instead of raising an exception for better user experience
        return GatewayMetrics(
            request_count=0,
            error_count=0,
            device_connections=0,
            commands_executed=0
        )
    except Exception as e:
        # Standardized error handling for other exceptions
        logger.exception(f"Unexpected error retrieving metrics: {str(e)}")
        return GatewayMetrics(
            request_count=0,
            error_count=0,
            device_connections=0,
            commands_executed=0
        )


@router.get("/config")
async def get_gateway_config(
    request: Request,
    principal: Optional[Principal] = Depends(optional_auth(["read:gateway"]))
):
    """
    Get the configuration of the gateway service.
    
    This endpoint queries the device gateway service for its configuration.
    
    Requires authentication with the 'read:gateway' scope.
    """
    try:
        # Log access if principal is provided
        if principal:
            logger.info(f"Access granted: user={principal.username}, resource=gateway:config, scope=read:gateway, action=get")
        
        gateway_url = "http://device_gateway:8001/config"
        
        # Use the same token for calling the gateway if available
        headers = {}
        if principal:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                headers = {"Authorization": auth_header}
        
        logger.debug(f"Calling gateway config endpoint: {gateway_url}")
        response = requests.get(gateway_url, headers=headers, timeout=10.0)
        
        if response.status_code != 200:
            logger.error(f"Gateway returned error: {response.status_code} - {response.text[:100]}")
            return {
                "status": "error",
                "message": f"Gateway service error: {response.status_code}"
            }
                
        return response.json()
    except requests.RequestException as e:
        # Standardized error handling for request exceptions
        logger.error(f"Error communicating with gateway: {str(e)}")
        return {
            "status": "error",
            "message": f"Error communicating with gateway: {str(e)}"
        }
    except Exception as e:
        # Standardized error handling for other exceptions
        logger.exception(f"Unexpected error retrieving configuration: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }


# Helper function to extract current token from request context
def get_current_token(request: Request) -> str:
    """
    Get the current token from request context.
    
    This extracts the token from the Authorization header in the request.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        str: The current token
        
    Raises:
        HTTPException: If no token is found
    """
    auth_header = request.headers.get("Authorization")
    token = extract_token_from_header(auth_header)
    
    if not token:
        logger.warning(f"No token found in request to {request.url}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token 