"""
Circuit Breaker pattern implementation for device connections.

This module implements the circuit breaker pattern to prevent overwhelming
devices that are consistently failing. It tracks failure rates for devices
and temporarily stops connection attempts if a device has too many failures.
"""

import time
import logging
import threading
from enum import Enum
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """States for the circuit breaker."""
    CLOSED = "closed"      # Normal operation, connections allowed
    OPEN = "open"          # Connections blocked due to failures
    HALF_OPEN = "half_open"  # Testing if the circuit can be closed again

class CircuitBreaker:
    """
    Circuit breaker for managing device connections.
    
    Tracks device connection failures and prevents overwhelming failing devices
    by blocking connection attempts when a device has exceeded its failure threshold.
    
    The circuit breaker goes through three states:
    - CLOSED: Normal operation, connections allowed
    - OPEN: Connections are blocked due to too many failures
    - HALF_OPEN: After a cooldown period, one test connection is allowed
    
    If the test connection succeeds, the circuit returns to CLOSED state.
    If it fails, the circuit returns to OPEN state for another cooldown period.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        half_open_success_threshold: int = 1
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            reset_timeout: Time in seconds to wait before half-opening circuit
            half_open_success_threshold: Number of successful attempts needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_success_threshold = half_open_success_threshold
        
        # Device state tracking
        self._device_circuits: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def _get_device_circuit(self, device_id: int) -> Dict[str, Any]:
        """Get the circuit data for a device, creating it if needed."""
        with self._lock:
            if device_id not in self._device_circuits:
                self._device_circuits[device_id] = {
                    "state": CircuitState.CLOSED,
                    "failure_count": 0,
                    "last_failure_time": 0,
                    "last_state_change": time.time(),
                    "success_count": 0,
                }
            return self._device_circuits[device_id]
    
    def record_success(self, device_id: int) -> None:
        """
        Record a successful connection for a device.
        
        Args:
            device_id: ID of the device
        """
        with self._lock:
            circuit = self._get_device_circuit(device_id)
            
            # In closed state, just reset failure count
            if circuit["state"] == CircuitState.CLOSED:
                circuit["failure_count"] = 0
                return
                
            # In half-open state, increment success count
            if circuit["state"] == CircuitState.HALF_OPEN:
                circuit["success_count"] += 1
                
                # If we've reached the threshold, close the circuit
                if circuit["success_count"] >= self.half_open_success_threshold:
                    logger.info(f"Circuit for device {device_id} transitioning from HALF_OPEN to CLOSED")
                    circuit["state"] = CircuitState.CLOSED
                    circuit["failure_count"] = 0
                    circuit["success_count"] = 0
                    circuit["last_state_change"] = time.time()
    
    def record_failure(self, device_id: int) -> None:
        """
        Record a connection failure for a device.
        
        Args:
            device_id: ID of the device
        """
        with self._lock:
            circuit = self._get_device_circuit(device_id)
            current_time = time.time()
            
            # Update failure stats
            circuit["failure_count"] += 1
            circuit["last_failure_time"] = current_time
            
            # In closed state, check if we need to open the circuit
            if circuit["state"] == CircuitState.CLOSED:
                if circuit["failure_count"] >= self.failure_threshold:
                    logger.warning(
                        f"Circuit for device {device_id} transitioning from CLOSED to OPEN "
                        f"after {circuit['failure_count']} consecutive failures"
                    )
                    circuit["state"] = CircuitState.OPEN
                    circuit["last_state_change"] = current_time
            
            # In half-open state, any failure sends us back to open
            elif circuit["state"] == CircuitState.HALF_OPEN:
                logger.warning(
                    f"Circuit for device {device_id} transitioning from HALF_OPEN to OPEN "
                    f"after test connection failure"
                )
                circuit["state"] = CircuitState.OPEN
                circuit["success_count"] = 0
                circuit["last_state_change"] = current_time
    
    def can_connect(self, device_id: int) -> bool:
        """
        Check if a device connection is allowed.
        
        Args:
            device_id: ID of the device
            
        Returns:
            True if connection is allowed, False otherwise
        """
        with self._lock:
            circuit = self._get_device_circuit(device_id)
            current_time = time.time()
            
            # In closed state, always allow connections
            if circuit["state"] == CircuitState.CLOSED:
                return True
                
            # In open state, check if reset timeout has elapsed
            elif circuit["state"] == CircuitState.OPEN:
                time_since_last_change = current_time - circuit["last_state_change"]
                
                if time_since_last_change >= self.reset_timeout:
                    logger.info(
                        f"Circuit for device {device_id} transitioning from OPEN to HALF_OPEN "
                        f"after {time_since_last_change:.1f}s cooldown"
                    )
                    circuit["state"] = CircuitState.HALF_OPEN
                    circuit["success_count"] = 0
                    circuit["last_state_change"] = current_time
                    return True
                else:
                    logger.debug(
                        f"Circuit for device {device_id} is OPEN. "
                        f"Blocking connection attempt. "
                        f"Will try again in {self.reset_timeout - time_since_last_change:.1f}s"
                    )
                    return False
                    
            # In half-open state, only allow limited test connections
            elif circuit["state"] == CircuitState.HALF_OPEN:
                # Already have some successes, but not enough to close
                if circuit["success_count"] > 0:
                    return True
                # No successes yet, only allow one connection attempt
                else:
                    # If no success yet and fresh transition to half-open,
                    # allow one connection
                    time_since_state_change = current_time - circuit["last_state_change"]
                    if time_since_state_change < 5:  # Within 5 seconds of state change
                        return True
                    else:
                        return False
        
        # Default to allowing connection (should never reach here)
        return True
    
    def get_state(self, device_id: int) -> CircuitState:
        """
        Get the current circuit state for a device.
        
        Args:
            device_id: ID of the device
            
        Returns:
            Current circuit state
        """
        with self._lock:
            circuit = self._get_device_circuit(device_id)
            return circuit["state"]
    
    def get_failure_count(self, device_id: int) -> int:
        """
        Get the current failure count for a device.
        
        Args:
            device_id: ID of the device
            
        Returns:
            Current consecutive failure count
        """
        with self._lock:
            circuit = self._get_device_circuit(device_id)
            return circuit["failure_count"]
    
    def reset(self, device_id: Optional[int] = None) -> None:
        """
        Reset the circuit breaker for a device or all devices.
        
        Args:
            device_id: ID of the device to reset, or None to reset all devices
        """
        with self._lock:
            if device_id is not None:
                if device_id in self._device_circuits:
                    self._device_circuits[device_id] = {
                        "state": CircuitState.CLOSED,
                        "failure_count": 0,
                        "last_failure_time": 0,
                        "last_state_change": time.time(),
                        "success_count": 0,
                    }
            else:
                self._device_circuits.clear()
    
    def get_troubled_devices(self) -> List[int]:
        """
        Get a list of devices with circuits in non-CLOSED state.
        
        Returns:
            List of device IDs with open or half-open circuits
        """
        with self._lock:
            return [
                device_id for device_id, circuit in self._device_circuits.items()
                if circuit["state"] != CircuitState.CLOSED
            ]

# Global circuit breaker instance
_global_circuit_breaker = CircuitBreaker()

def get_circuit_breaker() -> CircuitBreaker:
    """Get the global circuit breaker instance."""
    return _global_circuit_breaker 