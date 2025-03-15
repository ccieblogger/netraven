"""
Metrics collection for the Device Gateway.

This module provides functionality for collecting and reporting metrics
about the gateway service, such as request counts, response times, and errors.
"""

import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from netraven.core.logging import get_logger

# Configure logging
logger = get_logger("netraven.gateway.metrics")

class MetricsCollector:
    """Collector for gateway metrics"""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.metrics = {
            "requests": {
                "total": 0,
                "success": 0,
                "error": 0,
                "by_endpoint": {},
                "by_client": {}
            },
            "response_times": {
                "avg_ms": 0,
                "min_ms": float('inf'),
                "max_ms": 0,
                "by_endpoint": {}
            },
            "devices": {
                "total_connections": 0,
                "successful_connections": 0,
                "failed_connections": 0,
                "by_host": {}
            },
            "errors": {
                "total": 0,
                "by_type": {}
            },
            "start_time": datetime.now(),
            "uptime_seconds": 0
        }
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def record_request(
        self,
        endpoint: str,
        client_id: str,
        status_code: int,
        response_time_ms: float,
        is_error: bool = False
    ) -> None:
        """
        Record a request to the gateway.
        
        Args:
            endpoint: API endpoint
            client_id: Client ID
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            is_error: Whether the request resulted in an error
        """
        with self.lock:
            # Update request counts
            self.metrics["requests"]["total"] += 1
            
            if is_error:
                self.metrics["requests"]["error"] += 1
                self.metrics["errors"]["total"] += 1
            else:
                self.metrics["requests"]["success"] += 1
            
            # Update by endpoint
            if endpoint not in self.metrics["requests"]["by_endpoint"]:
                self.metrics["requests"]["by_endpoint"][endpoint] = {
                    "total": 0,
                    "success": 0,
                    "error": 0
                }
            
            self.metrics["requests"]["by_endpoint"][endpoint]["total"] += 1
            if is_error:
                self.metrics["requests"]["by_endpoint"][endpoint]["error"] += 1
            else:
                self.metrics["requests"]["by_endpoint"][endpoint]["success"] += 1
            
            # Update by client
            if client_id not in self.metrics["requests"]["by_client"]:
                self.metrics["requests"]["by_client"][client_id] = {
                    "total": 0,
                    "success": 0,
                    "error": 0
                }
            
            self.metrics["requests"]["by_client"][client_id]["total"] += 1
            if is_error:
                self.metrics["requests"]["by_client"][client_id]["error"] += 1
            else:
                self.metrics["requests"]["by_client"][client_id]["success"] += 1
            
            # Update response times
            current_total = self.metrics["requests"]["total"] - 1
            current_avg = self.metrics["response_times"]["avg_ms"]
            
            # Calculate new average
            if current_total > 0:
                self.metrics["response_times"]["avg_ms"] = (
                    (current_avg * current_total) + response_time_ms
                ) / self.metrics["requests"]["total"]
            else:
                self.metrics["response_times"]["avg_ms"] = response_time_ms
            
            # Update min/max
            if response_time_ms < self.metrics["response_times"]["min_ms"]:
                self.metrics["response_times"]["min_ms"] = response_time_ms
            
            if response_time_ms > self.metrics["response_times"]["max_ms"]:
                self.metrics["response_times"]["max_ms"] = response_time_ms
            
            # Update by endpoint
            if endpoint not in self.metrics["response_times"]["by_endpoint"]:
                self.metrics["response_times"]["by_endpoint"][endpoint] = {
                    "avg_ms": 0,
                    "min_ms": float('inf'),
                    "max_ms": 0,
                    "count": 0
                }
            
            endpoint_metrics = self.metrics["response_times"]["by_endpoint"][endpoint]
            current_endpoint_count = endpoint_metrics["count"]
            current_endpoint_avg = endpoint_metrics["avg_ms"]
            
            # Calculate new endpoint average
            if current_endpoint_count > 0:
                endpoint_metrics["avg_ms"] = (
                    (current_endpoint_avg * current_endpoint_count) + response_time_ms
                ) / (current_endpoint_count + 1)
            else:
                endpoint_metrics["avg_ms"] = response_time_ms
            
            # Update endpoint min/max
            if response_time_ms < endpoint_metrics["min_ms"]:
                endpoint_metrics["min_ms"] = response_time_ms
            
            if response_time_ms > endpoint_metrics["max_ms"]:
                endpoint_metrics["max_ms"] = response_time_ms
            
            endpoint_metrics["count"] += 1
            
            # Update uptime
            self.metrics["uptime_seconds"] = (
                datetime.now() - self.metrics["start_time"]
            ).total_seconds()
    
    def record_device_connection(
        self,
        host: str,
        success: bool,
        response_time_ms: float
    ) -> None:
        """
        Record a device connection attempt.
        
        Args:
            host: Device hostname or IP address
            success: Whether the connection was successful
            response_time_ms: Response time in milliseconds
        """
        with self.lock:
            # Update device connection counts
            self.metrics["devices"]["total_connections"] += 1
            
            if success:
                self.metrics["devices"]["successful_connections"] += 1
            else:
                self.metrics["devices"]["failed_connections"] += 1
            
            # Update by host
            if host not in self.metrics["devices"]["by_host"]:
                self.metrics["devices"]["by_host"][host] = {
                    "total": 0,
                    "success": 0,
                    "failure": 0,
                    "avg_response_time_ms": 0
                }
            
            host_metrics = self.metrics["devices"]["by_host"][host]
            host_metrics["total"] += 1
            
            if success:
                host_metrics["success"] += 1
            else:
                host_metrics["failure"] += 1
            
            # Update average response time
            current_host_count = host_metrics["total"] - 1
            current_host_avg = host_metrics["avg_response_time_ms"]
            
            if current_host_count > 0:
                host_metrics["avg_response_time_ms"] = (
                    (current_host_avg * current_host_count) + response_time_ms
                ) / host_metrics["total"]
            else:
                host_metrics["avg_response_time_ms"] = response_time_ms
    
    def record_error(self, error_type: str) -> None:
        """
        Record an error.
        
        Args:
            error_type: Type of error
        """
        with self.lock:
            # Update error counts
            if error_type not in self.metrics["errors"]["by_type"]:
                self.metrics["errors"]["by_type"][error_type] = 0
            
            self.metrics["errors"]["by_type"][error_type] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the current metrics.
        
        Returns:
            Dict containing metrics
        """
        with self.lock:
            # Update uptime
            self.metrics["uptime_seconds"] = (
                datetime.now() - self.metrics["start_time"]
            ).total_seconds()
            
            # Return a copy of the metrics
            return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        with self.lock:
            self.metrics = {
                "requests": {
                    "total": 0,
                    "success": 0,
                    "error": 0,
                    "by_endpoint": {},
                    "by_client": {}
                },
                "response_times": {
                    "avg_ms": 0,
                    "min_ms": float('inf'),
                    "max_ms": 0,
                    "by_endpoint": {}
                },
                "devices": {
                    "total_connections": 0,
                    "successful_connections": 0,
                    "failed_connections": 0,
                    "by_host": {}
                },
                "errors": {
                    "total": 0,
                    "by_type": {}
                },
                "start_time": datetime.now(),
                "uptime_seconds": 0
            }

# Create a singleton instance
metrics = MetricsCollector() 