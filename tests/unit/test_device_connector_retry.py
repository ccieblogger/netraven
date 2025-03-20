"""
Tests for the device connector retry mechanism.

This module tests the retry and exponential backoff functionality
of the JobDeviceConnector class.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from netraven.jobs.device_connector import JobDeviceConnector
from tests.mock.mock_device_connector import MockDeviceConnector, MockJobDeviceConnector

# Test parameters
TEST_DEVICE_ID = "test-device-id"
TEST_HOST = "192.168.1.1"
TEST_USERNAME = "admin"
TEST_PASSWORD = "password"
TEST_DEVICE_TYPE = "cisco_ios"


def test_retry_mechanism_success_on_first_attempt():
    """Test that a successful connection on first attempt works correctly."""
    # Create a mock core device connector
    mock_core = MagicMock()
    mock_core.connect.return_value = True
    
    # Patch the CoreDeviceConnector to return our mock
    with patch("netraven.jobs.device_connector.CoreDeviceConnector", return_value=mock_core):
        # Create the connector with max_retries=3
        connector = JobDeviceConnector(
            device_id=TEST_DEVICE_ID,
            host=TEST_HOST,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            device_type=TEST_DEVICE_TYPE,
            max_retries=3
        )
        
        # Connect should succeed immediately
        start_time = time.time()
        result = connector.connect()
        elapsed_time = time.time() - start_time
        
        # Verify connection was successful
        assert result is True
        assert connector.is_connected is True
        
        # Verify the mock was called exactly once
        mock_core.connect.assert_called_once()
        
        # No backoff should have occurred
        assert elapsed_time < 0.5  # Allow some overhead


def test_retry_mechanism_success_on_second_attempt():
    """Test that a connection that succeeds on second attempt works with retry."""
    # Create a mock core device connector
    mock_core = MagicMock()
    # Fail first time, succeed second time
    mock_core.connect.side_effect = [False, True]
    
    # Patch the CoreDeviceConnector to return our mock
    with patch("netraven.jobs.device_connector.CoreDeviceConnector", return_value=mock_core):
        # Create the connector with max_retries=3
        connector = JobDeviceConnector(
            device_id=TEST_DEVICE_ID,
            host=TEST_HOST,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            device_type=TEST_DEVICE_TYPE,
            max_retries=3
        )
        
        # Connect should eventually succeed
        result = connector.connect()
        
        # Verify connection was successful
        assert result is True
        assert connector.is_connected is True
        
        # Verify the mock was called twice
        assert mock_core.connect.call_count == 2


def test_retry_mechanism_all_attempts_fail():
    """Test that a connection fails after all retry attempts fail."""
    # Create a mock core device connector
    mock_core = MagicMock()
    # Always return False
    mock_core.connect.return_value = False
    
    # Patch the CoreDeviceConnector to return our mock
    with patch("netraven.jobs.device_connector.CoreDeviceConnector", return_value=mock_core):
        # Create the connector with max_retries=3
        connector = JobDeviceConnector(
            device_id=TEST_DEVICE_ID,
            host=TEST_HOST,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            device_type=TEST_DEVICE_TYPE,
            max_retries=3
        )
        
        # Connect should fail after all retries
        result = connector.connect()
        
        # Verify connection failed
        assert result is False
        assert connector.is_connected is False
        
        # Verify the mock was called the expected number of times
        assert mock_core.connect.call_count == 3


def test_retry_mechanism_exception():
    """Test that exceptions during connection attempts are handled correctly."""
    # Create a mock core device connector
    mock_core = MagicMock()
    # Raise exception on connect
    mock_core.connect.side_effect = Exception("Connection error")
    
    # Patch the CoreDeviceConnector to return our mock
    with patch("netraven.jobs.device_connector.CoreDeviceConnector", return_value=mock_core):
        # Create the connector with max_retries=3
        connector = JobDeviceConnector(
            device_id=TEST_DEVICE_ID,
            host=TEST_HOST,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            device_type=TEST_DEVICE_TYPE,
            max_retries=3
        )
        
        # Connect should fail after all retries
        result = connector.connect()
        
        # Verify connection failed
        assert result is False
        assert connector.is_connected is False
        
        # Verify the mock was called the expected number of times
        assert mock_core.connect.call_count == 3


def test_retry_mechanism_config_based():
    """Test that the retry mechanism uses the config value when no parameter is provided."""
    # Create a configuration with a different max_retries value
    mock_config = {
        "device": {
            "connection": {
                "max_retries": 5
            }
        }
    }
    
    # Patch get_config to return our mock config
    with patch("netraven.jobs.device_connector.get_config", return_value=mock_config):
        # Create the connector without specifying max_retries
        connector = JobDeviceConnector(
            device_id=TEST_DEVICE_ID,
            host=TEST_HOST,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            device_type=TEST_DEVICE_TYPE
        )
        
        # Verify max_retries was set from config
        assert connector.max_retries == 5


def test_retry_mechanism_backoff():
    """Test that the exponential backoff mechanism works correctly."""
    # Create a mock core device connector
    mock_core = MagicMock()
    # Always return False to ensure we go through all retries
    mock_core.connect.return_value = False
    
    # Patch the CoreDeviceConnector to return our mock and sleep to track calls
    with patch("netraven.jobs.device_connector.CoreDeviceConnector", return_value=mock_core), \
         patch("netraven.jobs.device_connector.time.sleep") as mock_sleep:
        
        # Create the connector with max_retries=3
        connector = JobDeviceConnector(
            device_id=TEST_DEVICE_ID,
            host=TEST_HOST,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            device_type=TEST_DEVICE_TYPE,
            max_retries=3
        )
        
        # Connect should fail after all retries
        connector.connect()
        
        # Verify sleep was called for backoff
        assert mock_sleep.call_count == 2  # Called after first and second failures
        
        # First backoff should be around 1 second (plus jitter)
        assert 1.0 <= mock_sleep.call_args_list[0][0][0] <= 2.0
        
        # Second backoff should be around 2 seconds (plus jitter)
        assert 2.0 <= mock_sleep.call_args_list[1][0][0] <= 4.0


def test_mock_device_connector():
    """Test that the MockDeviceConnector behaves as expected."""
    # Create a mock device connector that succeeds on first attempt
    connector = MockDeviceConnector(
        host=TEST_HOST,
        username=TEST_USERNAME,
        password=TEST_PASSWORD
    )
    
    # Connect should succeed
    assert connector.connect() is True
    assert connector.is_connected is True
    
    # Get running config
    config = connector.get_running()
    assert config is not None
    assert TEST_HOST in config  # Should contain hostname
    
    # Disconnect
    assert connector.disconnect() is True
    assert connector.is_connected is False


def test_mock_device_connector_failure():
    """Test that the MockDeviceConnector can simulate failures."""
    # Create a mock device connector that fails first 2 attempts
    connector = MockDeviceConnector(
        host=TEST_HOST,
        username=TEST_USERNAME,
        password=TEST_PASSWORD,
        failure_mode="intermittent",
        failure_count=2
    )
    
    # First connect might fail or succeed due to randomness in intermittent mode
    first_attempt = connector.connect()
    
    if not first_attempt:
        # If it failed, try again
        assert connector.connect() is True
    
    # Should be connected now
    assert connector.is_connected is True


def test_mock_job_device_connector_retry():
    """Test that the MockJobDeviceConnector retry mechanism works."""
    # Create a connector that fails first 2 attempts
    connector = MockJobDeviceConnector(
        device_id=TEST_DEVICE_ID,
        host=TEST_HOST,
        username=TEST_USERNAME,
        password=TEST_PASSWORD,
        max_retries=3,
        failure_mode="fixed",  # Always fail until failure_count is reached
        failure_count=2
    )
    
    # Connect should succeed after 3 attempts
    assert connector.connect() is True
    assert connector.is_connected is True
    
    # Verify log calls
    assert len(connector.log_calls["connect"]) == 1
    assert len(connector.log_calls["connect_failure"]) == 2
    assert len(connector.log_calls["connect_success"]) == 1 