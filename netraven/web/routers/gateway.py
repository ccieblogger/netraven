"""
Gateway API routes.

This module provides API routes for interacting with the device gateway service,
including status checks, metrics, and configuration.
"""

from typing import Dict, Any, List, Optional
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from netraven.core.config import get_config
from netraven.web.auth import get_current_active_user
from netraven.web.models.user import User

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

@router.get("/status", response_model=GatewayStatus)
async def get_gateway_status(current_user: User = Depends(get_current_active_user)):
    """
    Get the current status of the gateway service.
    
    Returns:
        GatewayStatus: Gateway status information
    """
    config = get_config()
    gateway_url = config.get("gateway", {}).get("url", "http://localhost:8001")
    api_key = config.get("gateway", {}).get("api_key", "")
    
    try:
        response = requests.get(
            f"{gateway_url}/status",
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
    Get the current gateway configuration.
    
    Returns:
        Dict[str, Any]: Gateway configuration
    """
    config = get_config()
    gateway_config = config.get("gateway", {})
    
    # Remove sensitive information
    if "api_key" in gateway_config:
        gateway_config["api_key"] = "********"
    if "jwt_secret" in gateway_config:
        gateway_config["jwt_secret"] = "********"
    
    return gateway_config 