import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from netraven.worker.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    get_circuit_breaker
)

def test_circuit_breaker_init():
    """Test that CircuitBreaker initializes with correct values."""
    cb = CircuitBreaker(
        failure_threshold=3,
        reset_timeout=30,
        half_open_success_threshold=2
    )
    
    assert cb.failure_threshold == 3
    assert cb.reset_timeout == 30
    assert cb.half_open_success_threshold == 2
    assert cb._device_circuits == {}

def test_device_circuit_initialization():
    """Test that device circuits are initialized correctly."""
    cb = CircuitBreaker()
    device_id = 123
    
    # Get circuit for a new device
    circuit = cb._get_device_circuit(device_id)
    
    # Check that it was initialized with default values
    assert circuit["state"] == CircuitState.CLOSED
    assert circuit["failure_count"] == 0
    assert circuit["last_failure_time"] == 0
    assert "last_state_change" in circuit
    assert circuit["success_count"] == 0

def test_record_success_closed_circuit():
    """Test recording success for a closed circuit."""
    cb = CircuitBreaker()
    device_id = 123
    
    # Set up a device with some failures
    circuit = cb._get_device_circuit(device_id)
    circuit["failure_count"] = 2
    
    # Record success
    cb.record_success(device_id)
    
    # Check that failure count was reset
    assert circuit["failure_count"] == 0
    assert circuit["state"] == CircuitState.CLOSED

def test_record_success_half_open_circuit():
    """Test recording success for a half-open circuit."""
    cb = CircuitBreaker(half_open_success_threshold=2)
    device_id = 123
    
    # Set up a half-open circuit
    circuit = cb._get_device_circuit(device_id)
    circuit["state"] = CircuitState.HALF_OPEN
    
    # Record first success - should stay half-open
    cb.record_success(device_id)
    assert circuit["state"] == CircuitState.HALF_OPEN
    assert circuit["success_count"] == 1
    
    # Record second success - should transition to closed
    cb.record_success(device_id)
    assert circuit["state"] == CircuitState.CLOSED
    assert circuit["success_count"] == 0
    assert circuit["failure_count"] == 0

def test_record_failure_closed_circuit():
    """Test recording failure for a closed circuit."""
    cb = CircuitBreaker(failure_threshold=3)
    device_id = 123
    
    # Record failures
    cb.record_failure(device_id)
    cb.record_failure(device_id)
    
    # Check that we're still closed
    circuit = cb._get_device_circuit(device_id)
    assert circuit["state"] == CircuitState.CLOSED
    assert circuit["failure_count"] == 2
    
    # Record the threshold failure
    cb.record_failure(device_id)
    
    # Check that circuit opened
    assert circuit["state"] == CircuitState.OPEN
    assert circuit["failure_count"] == 3

def test_record_failure_half_open_circuit():
    """Test recording failure for a half-open circuit."""
    cb = CircuitBreaker()
    device_id = 123
    
    # Set up a half-open circuit with some successes
    circuit = cb._get_device_circuit(device_id)
    circuit["state"] = CircuitState.HALF_OPEN
    circuit["success_count"] = 1
    
    # Record a failure - should go back to open
    cb.record_failure(device_id)
    
    # Check circuit state
    assert circuit["state"] == CircuitState.OPEN
    assert circuit["success_count"] == 0

def test_can_connect_closed_circuit():
    """Test can_connect for a closed circuit."""
    cb = CircuitBreaker()
    device_id = 123
    
    # Check that connection is allowed
    assert cb.can_connect(device_id) is True

def test_can_connect_open_circuit():
    """Test can_connect for an open circuit."""
    cb = CircuitBreaker(reset_timeout=60)
    device_id = 123
    
    # Set up an open circuit
    circuit = cb._get_device_circuit(device_id)
    circuit["state"] = CircuitState.OPEN
    
    # Check that connection is blocked
    assert cb.can_connect(device_id) is False
    
    # Test after reset timeout has passed
    circuit["last_state_change"] = time.time() - 70  # 70 seconds ago
    
    # Check that connection is allowed and circuit is half-open
    assert cb.can_connect(device_id) is True
    assert circuit["state"] == CircuitState.HALF_OPEN

def test_can_connect_half_open_circuit():
    """Test can_connect for a half-open circuit."""
    cb = CircuitBreaker()
    device_id = 123
    
    # Set up a fresh half-open circuit
    circuit = cb._get_device_circuit(device_id)
    circuit["state"] = CircuitState.HALF_OPEN
    circuit["last_state_change"] = time.time()  # Just now
    
    # First connection should be allowed for testing
    assert cb.can_connect(device_id) is True
    
    # Wait "virtually" - pretend 10 seconds passed
    circuit["last_state_change"] = time.time() - 10
    
    # Without any success, should block additional connections
    assert cb.can_connect(device_id) is False
    
    # Add a success - should allow more connections
    circuit["success_count"] = 1
    assert cb.can_connect(device_id) is True

def test_reset_specific_device():
    """Test resetting a specific device circuit."""
    cb = CircuitBreaker()
    device_id = 123
    
    # Set up a troubled circuit
    circuit = cb._get_device_circuit(device_id)
    circuit["state"] = CircuitState.OPEN
    circuit["failure_count"] = 10
    
    # Reset the device
    cb.reset(device_id)
    
    # Check that it's back to defaults
    circuit = cb._get_device_circuit(device_id)
    assert circuit["state"] == CircuitState.CLOSED
    assert circuit["failure_count"] == 0

def test_reset_all_devices():
    """Test resetting all device circuits."""
    cb = CircuitBreaker()
    
    # Set up multiple troubled circuits
    circuit1 = cb._get_device_circuit(123)
    circuit1["state"] = CircuitState.OPEN
    
    circuit2 = cb._get_device_circuit(456)
    circuit2["state"] = CircuitState.HALF_OPEN
    
    # Reset all devices
    cb.reset()
    
    # Check that the devices are gone
    assert len(cb._device_circuits) == 0

def test_get_troubled_devices():
    """Test getting a list of troubled devices."""
    cb = CircuitBreaker()
    
    # Set up multiple circuits in different states
    circuit1 = cb._get_device_circuit(123)
    circuit1["state"] = CircuitState.OPEN
    
    circuit2 = cb._get_device_circuit(456)
    circuit2["state"] = CircuitState.CLOSED
    
    circuit3 = cb._get_device_circuit(789)
    circuit3["state"] = CircuitState.HALF_OPEN
    
    # Get troubled devices
    troubled = cb.get_troubled_devices()
    
    # Check results (order doesn't matter)
    assert len(troubled) == 2
    assert 123 in troubled
    assert 789 in troubled
    assert 456 not in troubled

def test_global_circuit_breaker():
    """Test that the global circuit breaker works correctly."""
    # Get global circuit breaker
    cb1 = get_circuit_breaker()
    cb2 = get_circuit_breaker()
    
    # They should be the same instance
    assert cb1 is cb2
    
    # Test it works correctly
    device_id = 999
    assert cb1.can_connect(device_id) is True 