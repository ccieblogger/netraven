"""
Device Gateway API for NetRaven.

This module provides a REST API for secure communication with network devices.
It acts as a gateway between the application and external network devices.
"""

import os
import time
import datetime
import logging
import jwt
from fastapi import FastAPI, HTTPException, Depends, status, Request, Response, Header
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List, Any, Callable, Tuple

# Import device communication modules
from netraven.core.device_comm import DeviceConnector
from netraven.gateway.models import (
    DeviceConnectionRequest,
    DeviceCommandRequest,
    DeviceResponse,
    HealthResponse,
    TokenRequest,
    TokenResponse
)
from netraven.gateway import __version__
from netraven.gateway.auth import validate_api_key, create_access_token
from netraven.gateway.utils import sanitize_log_data
from netraven.gateway.metrics import metrics, MetricsCollector
from netraven.gateway.logging_config import (
    get_gateway_logger, 
    start_gateway_session, 
    end_gateway_session,
    log_with_context
)
from netraven.core.config import load_config, get_default_config_path
from netraven.core.logging import get_logger

# Configure logging
logger = get_logger("netraven.gateway")

# Create FastAPI application
app = FastAPI(
    title="NetRaven Device Gateway",
    description="Gateway service for secure communication with network devices",
    version=__version__
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

# Initialize metrics collector
metrics = MetricsCollector()

# Start time for uptime calculation
start_time = time.time()

# API key for authentication
API_KEY = os.environ.get("GATEWAY_API_KEY", "netraven-api-key")
JWT_SECRET = os.environ.get("GATEWAY_JWT_SECRET", "insecure-jwt-secret-change-in-production")

# Models
class DeviceCredentials(BaseModel):
    """Device credentials model."""
    host: str
    username: str
    password: str
    device_type: Optional[str] = None
    port: int = 22
    use_keys: bool = False
    key_file: Optional[str] = None

class CommandRequest(BaseModel):
    """Command request model."""
    device_id: str
    command: str
    credentials: DeviceCredentials

class ConnectRequest(BaseModel):
    """Connect request model."""
    device_id: str
    credentials: DeviceCredentials

class StatusResponse(BaseModel):
    """Status response model."""
    status: str
    version: str
    uptime: str
    connected_devices: int
    metrics: Dict[str, Any]

# Authentication dependency
async def verify_api_key(authorization: str = Header(None)):
    """Verify API key."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
        )
    
    if token != API_KEY:
        try:
            # Try to validate as JWT
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            # If we get here, the JWT is valid
            return payload
        except jwt.PyJWTError:
            # If JWT validation fails, raise exception
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key or JWT token",
            )
    
    return {"type": "api_key"}

# Add metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for collecting metrics about API requests.
    
    Args:
        request: FastAPI request
        call_next: Next middleware or endpoint
        
    Returns:
        Response from next middleware or endpoint
    """
    # Get client ID from API key header
    client_id = "unknown"
    api_key = request.headers.get("X-API-Key")
    
    if api_key:
        # In a real application, this would validate against a database
        client_map = {
            "netraven-api-key": "netraven-api",
            "netraven-scheduler-key": "netraven-scheduler"
        }
        client_id = client_map.get(api_key, "unknown")
    
    # Record start time
    start_time = time.time()
    
    # Start a gateway session for logging
    session_id = start_gateway_session(client_id)
    
    # Log the request
    log_with_context(
        logger, 
        level=20,  # INFO
        message=f"Request: {request.method} {request.url.path}",
        client_id=client_id,
        session_id=session_id
    )
    
    # Call next middleware or endpoint
    try:
        response = await call_next(request)
        
        # Record metrics
        response_time_ms = (time.time() - start_time) * 1000
        is_error = response.status_code >= 400
        
        metrics.record_request(
            endpoint=request.url.path,
            client_id=client_id,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            is_error=is_error
        )
        
        if is_error:
            metrics.record_error(f"HTTP_{response.status_code}")
            
            # Log error
            log_with_context(
                logger,
                level=40,  # ERROR
                message=f"Error response: {response.status_code}",
                client_id=client_id,
                session_id=session_id
            )
            
            # End gateway session with error
            end_gateway_session(
                success=False,
                result_message=f"HTTP error {response.status_code}"
            )
        else:
            # Log success
            log_with_context(
                logger,
                level=20,  # INFO
                message=f"Success response: {response.status_code}",
                client_id=client_id,
                session_id=session_id
            )
            
            # End gateway session with success
            end_gateway_session(
                success=True,
                result_message=f"HTTP success {response.status_code}"
            )
        
        return response
    except Exception as e:
        # Record error metrics
        response_time_ms = (time.time() - start_time) * 1000
        
        metrics.record_request(
            endpoint=request.url.path,
            client_id=client_id,
            status_code=500,
            response_time_ms=response_time_ms,
            is_error=True
        )
        
        metrics.record_error(type(e).__name__)
        
        # Log exception
        log_with_context(
            logger,
            level=40,  # ERROR
            message=f"Exception in request: {str(e)}",
            client_id=client_id,
            session_id=session_id,
            exc_info=e
        )
        
        # End gateway session with error
        end_gateway_session(
            success=False,
            result_message=f"Exception: {str(e)}"
        )
        
        # Re-raise the exception
        raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "version": __version__
    }

@app.get("/status", response_model=StatusResponse)
async def get_status(auth: Dict = Depends(verify_api_key)):
    """Get gateway status."""
    # Record request
    metrics.record_request("/status")
    
    # Calculate uptime
    uptime_seconds = time.time() - start_time
    uptime = str(datetime.timedelta(seconds=int(uptime_seconds)))
    
    return {
        "status": "running",
        "version": __version__,
        "uptime": uptime,
        "connected_devices": metrics.active_connections,
        "metrics": metrics.get_metrics()
    }

@app.get("/metrics")
async def get_metrics(auth: Dict = Depends(verify_api_key)):
    """Get gateway metrics."""
    # Record request
    metrics.record_request("/metrics")
    
    return metrics.get_metrics()

@app.post("/reset-metrics")
async def reset_metrics(auth: Dict = Depends(verify_api_key)):
    """Reset gateway metrics."""
    # Record request
    metrics.record_request("/reset-metrics")
    
    # Reset metrics
    metrics.reset_metrics()
    
    return {"status": "ok", "message": "Metrics reset successfully"}

@app.post("/check-device")
async def check_device(device: DeviceCredentials, auth: Dict = Depends(verify_api_key)):
    """Check device connectivity."""
    # Record request
    metrics.record_request("/check-device")
    
    # Import here to avoid circular imports
    from netraven.jobs.device_connector import check_device_connectivity
    
    try:
        # Check device connectivity
        reachable, error = check_device_connectivity(
            host=device.host,
            port=device.port
        )
        
        if reachable:
            metrics.record_success()
            return {"reachable": True}
        else:
            metrics.record_error("connectivity_error", error)
            return {"reachable": False, "error": error}
    except Exception as e:
        # Record error
        error_msg = str(e)
        metrics.record_error("exception", error_msg)
        
        # Return error
        return {"reachable": False, "error": error_msg}

@app.post("/connect", response_model=DeviceResponse)
async def connect_device(
    request: DeviceConnectionRequest,
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """
    Connect to a device and verify connectivity.
    
    This endpoint attempts to establish a connection to the specified device
    and returns the result of the connection attempt.
    """
    # Start a new gateway session for this device operation
    session_id = start_gateway_session(
        client_id=client_info['client_id'],
        device_id=request.host
    )
    
    log_with_context(
        logger,
        level=20,  # INFO
        message=f"Connection request to {request.host}",
        client_id=client_info['client_id'],
        device_id=request.host,
        session_id=session_id
    )
    
    try:
        # Record start time for device metrics
        start_time = time.time()
        
        # Create device connector
        device = DeviceConnector(
            host=request.host,
            username=request.username,
            password=request.password,
            device_type=request.device_type,
            port=request.port,
            use_keys=request.use_keys,
            key_file=request.key_file,
            timeout=request.timeout
        )
        
        log_with_context(
            logger,
            level=20,  # INFO
            message=f"Attempting connection to {request.host}",
            client_id=client_info['client_id'],
            device_id=request.host,
            session_id=session_id
        )
        
        # Attempt connection
        connected = device.connect()
        
        # Record device connection metrics
        response_time_ms = (time.time() - start_time) * 1000
        metrics.record_device_connection(
            host=request.host,
            success=connected,
            response_time_ms=response_time_ms
        )
        
        if not connected:
            log_with_context(
                logger,
                level=40,  # ERROR
                message=f"Failed to connect to {request.host}",
                client_id=client_info['client_id'],
                device_id=request.host,
                session_id=session_id
            )
            
            # End gateway session with error
            end_gateway_session(
                success=False,
                result_message=f"Failed to connect to {request.host}"
            )
            
            return {
                "status": "error",
                "message": f"Failed to connect to {request.host}",
                "data": None
            }
        
        log_with_context(
            logger,
            level=20,  # INFO
            message=f"Successfully connected to {request.host}",
            client_id=client_info['client_id'],
            device_id=request.host,
            session_id=session_id
        )
        
        # Get basic device info if connected
        serial = None
        os_info = None
        
        try:
            log_with_context(
                logger,
                level=20,  # INFO
                message=f"Getting device info from {request.host}",
                client_id=client_info['client_id'],
                device_id=request.host,
                session_id=session_id
            )
            
            serial = device.get_serial_number()
            os_info = device.get_os_info()
            
            log_with_context(
                logger,
                level=20,  # INFO
                message=f"Got device info: serial={serial}, os={os_info}",
                client_id=client_info['client_id'],
                device_id=request.host,
                session_id=session_id
            )
        except Exception as e:
            log_with_context(
                logger,
                level=30,  # WARNING
                message=f"Error getting device info: {str(e)}",
                client_id=client_info['client_id'],
                device_id=request.host,
                session_id=session_id,
                exc_info=e
            )
        
        # Disconnect
        device.disconnect()
        
        log_with_context(
            logger,
            level=20,  # INFO
            message=f"Disconnected from {request.host}",
            client_id=client_info['client_id'],
            device_id=request.host,
            session_id=session_id
        )
        
        # End gateway session with success
        end_gateway_session(
            success=True,
            result_message=f"Successfully connected to {request.host}"
        )
        
        return {
            "status": "success",
            "message": f"Successfully connected to {request.host}",
            "data": {
                "serial_number": serial,
                "os_info": os_info
            }
        }
    
    except Exception as e:
        log_with_context(
            logger,
            level=40,  # ERROR
            message=f"Error connecting to device: {str(e)}",
            client_id=client_info['client_id'],
            device_id=request.host,
            session_id=session_id,
            exc_info=e
        )
        
        # Record error metrics
        metrics.record_error(type(e).__name__)
        
        # End gateway session with error
        end_gateway_session(
            success=False,
            result_message=f"Error: {str(e)}"
        )
        
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

@app.post("/command", response_model=DeviceResponse)
async def execute_command(
    request: DeviceCommandRequest,
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """
    Execute a command on a device.
    
    This endpoint connects to the specified device, executes the requested
    command, and returns the result.
    """
    # Start a new gateway session for this device operation
    session_id = start_gateway_session(
        client_id=client_info['client_id'],
        device_id=request.host
    )
    
    log_with_context(
        logger,
        level=20,  # INFO
        message=f"Command request for {request.host}: {request.command}",
        client_id=client_info['client_id'],
        device_id=request.host,
        session_id=session_id
    )
    
    # Log sanitized request (without password)
    sanitized_request = sanitize_log_data(request.dict())
    log_with_context(
        logger,
        level=10,  # DEBUG
        message=f"Sanitized request: {sanitized_request}",
        client_id=client_info['client_id'],
        device_id=request.host,
        session_id=session_id
    )
    
    try:
        # Record start time for device metrics
        start_time = time.time()
        
        # Create device connector
        device = DeviceConnector(
            host=request.host,
            username=request.username,
            password=request.password,
            device_type=request.device_type,
            port=request.port,
            use_keys=request.use_keys,
            key_file=request.key_file,
            timeout=request.timeout
        )
        
        log_with_context(
            logger,
            level=20,  # INFO
            message=f"Connecting to {request.host} to execute {request.command}",
            client_id=client_info['client_id'],
            device_id=request.host,
            session_id=session_id
        )
        
        # Connect to device
        connected = device.connect()
        
        # Record device connection metrics
        response_time_ms = (time.time() - start_time) * 1000
        metrics.record_device_connection(
            host=request.host,
            success=connected,
            response_time_ms=response_time_ms
        )
        
        if not connected:
            log_with_context(
                logger,
                level=40,  # ERROR
                message=f"Failed to connect to {request.host}",
                client_id=client_info['client_id'],
                device_id=request.host,
                session_id=session_id
            )
            
            # End gateway session with error
            end_gateway_session(
                success=False,
                result_message=f"Failed to connect to {request.host}"
            )
            
            return {
                "status": "error",
                "message": f"Failed to connect to {request.host}",
                "data": None
            }
        
        log_with_context(
            logger,
            level=20,  # INFO
            message=f"Connected to {request.host}, executing command: {request.command}",
            client_id=client_info['client_id'],
            device_id=request.host,
            session_id=session_id
        )
        
        # Execute command
        result = None
        command_start_time = time.time()
        
        try:
            if request.command == "get_running_config":
                result = device.get_running_config()
            elif request.command == "get_serial_number":
                result = device.get_serial_number()
            elif request.command == "get_os_info":
                result = device.get_os_info()
            else:
                log_with_context(
                    logger,
                    level=40,  # ERROR
                    message=f"Unknown command: {request.command}",
                    client_id=client_info['client_id'],
                    device_id=request.host,
                    session_id=session_id
                )
                
                device.disconnect()
                
                # Record error metrics
                metrics.record_error("UnknownCommand")
                
                # End gateway session with error
                end_gateway_session(
                    success=False,
                    result_message=f"Unknown command: {request.command}"
                )
                
                return {
                    "status": "error",
                    "message": f"Unknown command: {request.command}",
                    "data": None
                }
                
            log_with_context(
                logger,
                level=20,  # INFO
                message=f"Command {request.command} executed successfully on {request.host}",
                client_id=client_info['client_id'],
                device_id=request.host,
                session_id=session_id
            )
        except Exception as e:
            log_with_context(
                logger,
                level=40,  # ERROR
                message=f"Error executing command: {str(e)}",
                client_id=client_info['client_id'],
                device_id=request.host,
                session_id=session_id,
                exc_info=e
            )
            
            device.disconnect()
            
            # Record error metrics
            metrics.record_error(type(e).__name__)
            
            # End gateway session with error
            end_gateway_session(
                success=False,
                result_message=f"Error executing command: {str(e)}"
            )
            
            return {
                "status": "error",
                "message": f"Error executing command: {str(e)}",
                "data": None
            }
        
        # Disconnect
        device.disconnect()
        
        log_with_context(
            logger,
            level=20,  # INFO
            message=f"Disconnected from {request.host}",
            client_id=client_info['client_id'],
            device_id=request.host,
            session_id=session_id
        )
        
        # End gateway session with success
        end_gateway_session(
            success=True,
            result_message=f"Successfully executed {request.command}"
        )
        
        return {
            "status": "success",
            "message": f"Successfully executed {request.command}",
            "data": result
        }
    
    except Exception as e:
        log_with_context(
            logger,
            level=40,  # ERROR
            message=f"Error in gateway: {str(e)}",
            client_id=client_info['client_id'],
            device_id=request.host,
            session_id=session_id,
            exc_info=e
        )
        
        # Record error metrics
        metrics.record_error(type(e).__name__)
        
        # End gateway session with error
        end_gateway_session(
            success=False,
            result_message=f"Error: {str(e)}"
        )
        
        return {
            "status": "error",
            "message": str(e),
            "data": None
        } 