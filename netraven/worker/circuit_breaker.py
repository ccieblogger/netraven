"""
Circuit breaker pattern implementation for device connections.

This module implements the circuit breaker pattern to prevent overwhelming
devices that are consistently failing. It tracks failure rates for devices
and temporarily stops connection attempts if a device has too many failures.

The circuit breaker pattern protects both the system and target devices by:
1. Preventing waste of resources on connections likely to fail
2. Allowing failing devices time to recover
3. Avoiding cascading failures across the system
4. Providing graceful degradation during partial outages

The implementation follows a state machine model with three states:
- CLOSED: Normal operation, connections are allowed
- OPEN: Circuit is tripped, connections are blocked
- HALF-OPEN: Testing if recovery has occurred

Key features:
- Thread-safe state management with proper locking
- Configurable failure thresholds and timeout periods
- Automatic state transitions based on success/failure patterns
- Singleton instance for global access throughout the application
"""

import time
import logging
import threading
from enum import Enum
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """States for the circuit breaker state machine.
    
    The circuit breaker follows a state machine pattern with three states
    that determine whether connections to devices are allowed or blocked.
    
    Attributes:
        CLOSED: Normal operation state where connections are allowed
        OPEN: Failed state where connections are blocked to prevent
              overwhelming a failing device
        HALF_OPEN: Testing state where a single connection is allowed
                  to determine if the device has recovered
    """
    CLOSED = "closed"      # Normal operation, connections allowed
    OPEN = "open"          # Connections blocked due to failures
    HALF_OPEN = "half_open"  # Testing if the circuit can be closed again

class CircuitBreaker:
    """Circuit breaker for managing device connections.
    
    Tracks device connection failures and prevents overwhelming failing devices
    by blocking connection attempts when a device has exceeded its failure threshold.
    
    The circuit breaker goes through three states:
    - CLOSED: Normal operation, connections allowed
    - OPEN: Connections are blocked due to too many failures
    - HALF_OPEN: After a cooldown period, one test connection is allowed
    
    If the test connection succeeds, the circuit returns to CLOSED state.
    If it fails, the circuit returns to OPEN state for another cooldown period.
    
    This implementation is thread-safe, using a reentrant lock to protect
    the internal state during concurrent access from multiple threads.
    
    Attributes:
        failure_threshold (int): Number of consecutive failures before opening circuit
        reset_timeout (int): Time in seconds to wait before half-opening circuit
        half_open_success_threshold (int): Successful connections needed to close circuit
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        half_open_success_threshold: int = 1
    ):
        """Initialize the circuit breaker with configurable thresholds.
        
        Args:
            failure_threshold (int): Number of consecutive failures before
                                   the circuit transitions from CLOSED to OPEN.
                                   Default is 5 failures.
            reset_timeout (int): Time in seconds to wait before transitioning
                               from OPEN to HALF_OPEN to test if the device
                               has recovered. Default is 60 seconds.
            half_open_success_threshold (int): Number of successful connections
                                             needed while in HALF_OPEN state
                                             before returning to CLOSED state.
                                             Default is 1 success.
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_success_threshold = half_open_success_threshold
        
        # Device state tracking
        self._device_circuits: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def _get_device_circuit(self, device_id: int) -> Dict[str, Any]:
        """Get the circuit data for a device, creating it if needed.
        
        This internal method retrieves the circuit state information for a
        device, initializing it with default values if it doesn't exist yet.
        The method is thread-safe and used by all public methods.
        
        Args:
            device_id (int): ID of the device to get circuit data for
            
        Returns:
            Dict[str, Any]: Dictionary containing the device's circuit state:
                          - state: Current CircuitState
                          - failure_count: Number of consecutive failures
                          - last_failure_time: Timestamp of last failure
                          - last_state_change: Timestamp of last state transition
                          - success_count: Number of consecutive successes
        """
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
        """Record a successful connection for a device.
        
        Updates the device's circuit state based on a successful connection:
        - In CLOSED state: Resets the failure counter
        - In HALF_OPEN state: Increments success counter and potentially
          transitions to CLOSED if the success threshold is reached
        - In OPEN state: No effect (should not be called in this state)
        
        This method is thread-safe and can be called from multiple threads.
        
        Args:
            device_id (int): ID of the device that had a successful connection
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
        """Record a connection failure for a device.
        
        Updates the device's circuit state based on a failed connection:
        - In CLOSED state: Increments failure counter and potentially
          transitions to OPEN if the failure threshold is reached
        - In HALF_OPEN state: Transitions back to OPEN state
        - In OPEN state: Updates failure timestamp (should not be called in this state)
        
        This method is thread-safe and can be called from multiple threads.
        
        Args:
            device_id (int): ID of the device that had a failed connection
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
        """Check if a device connection is allowed based on circuit state.
        
        This is the primary method used by clients to determine if a connection
        attempt should be made. The decision is based on:
        - In CLOSED state: Always allows connections
        - In OPEN state: Blocks connections unless the reset timeout has elapsed,
          in which case it transitions to HALF_OPEN
        - In HALF_OPEN state: Allows limited test connections to determine
          if the device has recovered
        
        This method is thread-safe and can be called from multiple threads.
        
        Args:
            device_id (int): ID of the device to check connection permission for
            
        Returns:
            bool: True if connection is allowed, False if connection should be blocked
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
        """Get the current circuit state for a device.
        
        Retrieves the current state of the circuit breaker for a specific device.
        This is useful for diagnostics, logging, and monitoring.
        
        This method is thread-safe and can be called from multiple threads.
        
        Args:
            device_id (int): ID of the device to get circuit state for
            
        Returns:
            CircuitState: Current state of the circuit (CLOSED, OPEN, or HALF_OPEN)
        """
        with self._lock:
            circuit = self._get_device_circuit(device_id)
            return circuit["state"]
    
    def get_failure_count(self, device_id: int) -> int:
        """Get the current failure count for a device.
        
        Retrieves the number of consecutive failures recorded for a device.
        This is useful for diagnostics, logging, and monitoring.
        
        This method is thread-safe and can be called from multiple threads.
        
        Args:
            device_id (int): ID of the device to get failure count for
            
        Returns:
            int: Number of consecutive failures recorded for the device
        """
        with self._lock:
            circuit = self._get_device_circuit(device_id)
            return circuit["failure_count"]
    
    def reset(self, device_id: Optional[int] = None) -> None:
        """Reset the circuit breaker for a device or all devices.
        
        Resets the circuit state to CLOSED and clears all failure counters.
        This can be used for:
        - Manual intervention after resolving a device issue
        - System restart or reconfiguration
        - Testing purposes
        
        This method is thread-safe and can be called from multiple threads.
        
        Args:
            device_id (Optional[int]): ID of the device to reset, or None to reset all devices
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
        """Get a list of devices with circuits in non-CLOSED state.
        
        Retrieves a list of device IDs that have open or half-open circuits,
        indicating devices that are currently experiencing issues.
        This is useful for monitoring and diagnostics.
        
        This method is thread-safe and can be called from multiple threads.
        
        Returns:
            List[int]: List of device IDs with non-CLOSED circuit states
        """
        with self._lock:
            return [
                device_id for device_id, circuit in self._device_circuits.items()
                if circuit["state"] != CircuitState.CLOSED
            ]

# Singleton instance for global access
_circuit_breaker: Optional[CircuitBreaker] = None

def get_circuit_breaker() -> CircuitBreaker:
    """Get the global circuit breaker instance.
    
    Returns a singleton instance of the CircuitBreaker class,
    ensuring that the same instance is used throughout the application.
    This allows consistent tracking of device states across different
    components and threads.
    
    The instance is created on first call with default settings.
    
    Returns:
        CircuitBreaker: Singleton instance of the circuit breaker
    """
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    return _circuit_breaker 