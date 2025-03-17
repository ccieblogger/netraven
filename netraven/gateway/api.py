"""
API module for the gateway service.

This module provides the API endpoints for the gateway service.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, Response

from netraven.core.logging import get_logger
from netraven.gateway.auth import authenticate_request, authenticate_request_with_scope

# Setup logger
logger = get_logger("netraven.gateway.api")

# Create Flask app
app = Flask(__name__)

# Gateway metrics
gateway_metrics = {
    "request_count": 0,
    "error_count": 0,
    "device_connections": 0,
    "commands_executed": 0
}

# Gateway start time
start_time = datetime.now()


@app.route("/health", methods=["GET"])
def health_check() -> Response:
    """
    Health check endpoint.
    
    This endpoint does not require authentication.
    
    Returns:
        Response: JSON response with health status
    """
    # Update metrics
    gateway_metrics["request_count"] += 1
    
    # Return health status
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })


@app.route("/status", methods=["GET"])
def get_status() -> Response:
    """
    Get the status of the gateway service.
    
    This endpoint does not require authentication.
    
    Returns:
        Response: JSON response with gateway status
    """
    # Update metrics
    gateway_metrics["request_count"] += 1
    
    # Calculate uptime
    uptime = datetime.now() - start_time
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    
    # Return status
    return jsonify({
        "status": "running",
        "version": "1.0.0",
        "uptime": uptime_str,
        "connected_devices": gateway_metrics["device_connections"],
        "metrics": gateway_metrics
    })


@app.route("/devices", methods=["GET"])
def get_devices() -> Response:
    """
    Get a list of connected devices.
    
    This endpoint requires authentication with the 'read:devices' scope.
    
    Returns:
        Response: JSON response with device information
    """
    # Authenticate request
    token_data = authenticate_request_with_scope(request.headers, "read:devices")
    if not token_data:
        logger.warning("Unauthorized access attempt to devices endpoint")
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 401
    
    # Update metrics
    gateway_metrics["request_count"] += 1
    
    # Return device data - in a real implementation, this would query actual device data
    return jsonify({
        "devices": [
            {
                "id": "device-001",
                "name": "Router-01",
                "type": "router",
                "status": "connected",
                "last_seen": datetime.now().isoformat(),
                "ip_address": "192.168.1.1"
            },
            {
                "id": "device-002",
                "name": "Switch-01",
                "type": "switch",
                "status": "connected",
                "last_seen": datetime.now().isoformat(),
                "ip_address": "192.168.1.2"
            }
        ]
    })


@app.route("/metrics", methods=["GET"])
def get_metrics() -> Response:
    """
    Get gateway metrics.
    
    This endpoint requires authentication with the 'read:metrics' scope.
    
    Returns:
        Response: JSON response with gateway metrics
    """
    # Authenticate request
    token_data = authenticate_request_with_scope(request.headers, "read:metrics")
    if not token_data:
        logger.warning("Unauthorized access attempt to metrics endpoint")
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 401
    
    # Update metrics
    gateway_metrics["request_count"] += 1
    
    # Return metrics
    return jsonify(gateway_metrics)


@app.errorhandler(Exception)
def handle_error(error: Exception) -> Response:
    """
    Handle exceptions and return appropriate error response.
    
    Args:
        error: The exception that occurred
        
    Returns:
        Response: JSON error response
    """
    logger.exception(f"Unexpected error: {str(error)}")
    gateway_metrics["error_count"] += 1
    
    return jsonify({
        "status": "error",
        "message": f"Internal server error: {str(error)}"
    }), 500 