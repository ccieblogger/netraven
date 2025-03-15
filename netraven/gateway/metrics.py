"""
Metrics collection for the NetRaven gateway.

This module provides metrics collection for the NetRaven gateway.
"""

import time
from typing import Dict, Any, Optional, List
from prometheus_client import Counter, Histogram, Gauge, Summary

# Define metrics
REQUEST_COUNT = Counter(
    "gateway_request_total",
    "Total number of requests",
    ["endpoint"]
)

ERROR_COUNT = Counter(
    "gateway_error_total",
    "Total number of errors",
    ["error_type"]
)

REQUEST_LATENCY = Histogram(
    "gateway_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"]
)

DEVICE_CONNECTION_COUNT = Counter(
    "gateway_device_connection_total",
    "Total number of device connections",
    ["host", "success"]
)

DEVICE_CONNECTION_LATENCY = Histogram(
    "gateway_device_connection_latency_seconds",
    "Device connection latency in seconds",
    ["host", "success"]
)

DEVICE_COMMAND_COUNT = Counter(
    "gateway_device_command_total",
    "Total number of device commands",
    ["host", "success"]
)

DEVICE_COMMAND_LATENCY = Histogram(
    "gateway_device_command_latency_seconds",
    "Device command latency in seconds",
    ["host", "success"]
)

DEVICE_BACKUP_COUNT = Counter(
    "gateway_device_backup_total",
    "Total number of device backups",
    ["host", "success"]
)

DEVICE_BACKUP_LATENCY = Histogram(
    "gateway_device_backup_latency_seconds",
    "Device backup latency in seconds",
    ["host", "success"]
)

DEVICE_BACKUP_SIZE = Summary(
    "gateway_device_backup_size_bytes",
    "Device backup size in bytes",
    ["host"]
)

DEVICE_REACHABILITY_COUNT = Counter(
    "gateway_device_reachability_total",
    "Total number of device reachability checks",
    ["host", "success"]
)

DEVICE_REACHABILITY_LATENCY = Histogram(
    "gateway_device_reachability_latency_seconds",
    "Device reachability check latency in seconds",
    ["host", "success"]
)

CONNECTED_DEVICES = Gauge(
    "gateway_connected_devices",
    "Number of currently connected devices"
)

class MetricsCollector:
    """Metrics collector for the NetRaven gateway."""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.metrics = {
            "request_count": 0,
            "error_count": 0,
            "device_connections": 0,
            "device_commands": 0,
            "device_backups": 0,
            "device_reachability_checks": 0,
            "connected_devices": 0,
            "errors_by_type": {}
        }
        self.connected_devices = set()
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = {
            "request_count": 0,
            "error_count": 0,
            "device_connections": 0,
            "device_commands": 0,
            "device_backups": 0,
            "device_reachability_checks": 0,
            "connected_devices": 0,
            "errors_by_type": {}
        }
        self.connected_devices = set()
    
    def record_request(self, endpoint: str):
        """
        Record a request.
        
        Args:
            endpoint: API endpoint
        """
        self.metrics["request_count"] += 1
        REQUEST_COUNT.labels(endpoint=endpoint).inc()
    
    def record_error(self, error_type: str, error_message: Optional[str] = None):
        """
        Record an error.
        
        Args:
            error_type: Type of error
            error_message: Error message (optional)
        """
        self.metrics["error_count"] += 1
        
        if error_type not in self.metrics["errors_by_type"]:
            self.metrics["errors_by_type"][error_type] = 0
        
        self.metrics["errors_by_type"][error_type] += 1
        ERROR_COUNT.labels(error_type=error_type).inc()
    
    def record_latency(self, endpoint: str, latency_seconds: float):
        """
        Record request latency.
        
        Args:
            endpoint: API endpoint
            latency_seconds: Latency in seconds
        """
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency_seconds)
    
    def record_device_connection(self, host: str, success: bool, response_time_ms: float):
        """
        Record a device connection.
        
        Args:
            host: Device hostname or IP address
            success: Whether the connection was successful
            response_time_ms: Response time in milliseconds
        """
        self.metrics["device_connections"] += 1
        
        # Update connected devices count
        if success:
            self.connected_devices.add(host)
            CONNECTED_DEVICES.set(len(self.connected_devices))
        
        # Record connection metrics
        DEVICE_CONNECTION_COUNT.labels(
            host=host,
            success=str(success)
        ).inc()
        
        DEVICE_CONNECTION_LATENCY.labels(
            host=host,
            success=str(success)
        ).observe(response_time_ms / 1000)  # Convert to seconds
    
    def record_device_command(self, host: str, success: bool, response_time_ms: float):
        """
        Record a device command.
        
        Args:
            host: Device hostname or IP address
            success: Whether the command was successful
            response_time_ms: Response time in milliseconds
        """
        self.metrics["device_commands"] += 1
        
        # Record command metrics
        DEVICE_COMMAND_COUNT.labels(
            host=host,
            success=str(success)
        ).inc()
        
        DEVICE_COMMAND_LATENCY.labels(
            host=host,
            success=str(success)
        ).observe(response_time_ms / 1000)  # Convert to seconds
    
    def record_device_backup(self, host: str, success: bool, response_time_ms: float, config_size: int = 0):
        """
        Record a device backup.
        
        Args:
            host: Device hostname or IP address
            success: Whether the backup was successful
            response_time_ms: Response time in milliseconds
            config_size: Size of the configuration in bytes
        """
        self.metrics["device_backups"] += 1
        
        # Record backup metrics
        DEVICE_BACKUP_COUNT.labels(
            host=host,
            success=str(success)
        ).inc()
        
        DEVICE_BACKUP_LATENCY.labels(
            host=host,
            success=str(success)
        ).observe(response_time_ms / 1000)  # Convert to seconds
        
        if success and config_size > 0:
            DEVICE_BACKUP_SIZE.labels(host=host).observe(config_size)
    
    def record_device_reachability(self, host: str, success: bool, response_time_ms: float):
        """
        Record a device reachability check.
        
        Args:
            host: Device hostname or IP address
            success: Whether the device was reachable
            response_time_ms: Response time in milliseconds
        """
        self.metrics["device_reachability_checks"] += 1
        
        # Record reachability metrics
        DEVICE_REACHABILITY_COUNT.labels(
            host=host,
            success=str(success)
        ).inc()
        
        DEVICE_REACHABILITY_LATENCY.labels(
            host=host,
            success=str(success)
        ).observe(response_time_ms / 1000)  # Convert to seconds
    
    def record_device_disconnect(self, host: str):
        """
        Record a device disconnection.
        
        Args:
            host: Device hostname or IP address
        """
        if host in self.connected_devices:
            self.connected_devices.remove(host)
            CONNECTED_DEVICES.set(len(self.connected_devices))
    
    def record_success(self):
        """Record a successful operation."""
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics.
        
        Returns:
            Dict[str, Any]: Metrics dictionary
        """
        return {
            "request_count": self.metrics["request_count"],
            "error_count": self.metrics["error_count"],
            "device_connections": self.metrics["device_connections"],
            "device_commands": self.metrics["device_commands"],
            "device_backups": self.metrics["device_backups"],
            "device_reachability_checks": self.metrics["device_reachability_checks"],
            "connected_devices": len(self.connected_devices),
            "errors_by_type": self.metrics["errors_by_type"]
        }

# Create a global metrics collector instance
metrics = MetricsCollector() 