import pytest
from unittest.mock import patch, MagicMock, call
import time
import logging
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

from netraven.worker.dispatcher import dispatch_tasks, task_with_retry
from netraven.worker.error_handler import ErrorCategory, ErrorInfo

# Mock device class for testing
class MockDevice:
    def __init__(self, id, hostname, ip_address):
        self.id = id
        self.hostname = hostname
        self.ip_address = ip_address
        self.device_type = "cisco_ios"
        self.username = "test"
        self.password = "test"

# --- Test task_with_retry function ---

@patch('netraven.worker.dispatcher.handle_device')
def test_task_with_retry_success_first_attempt(mock_handle_device):
    """Test successful task execution on first attempt."""
    # Mock a successful response
    mock_handle_device.return_value = {
        "success": True,
        "result": "abc123",
        "error": None
    }
    
    device = MockDevice(1, "test-device", "192.168.1.1")
    result = task_with_retry(device, 123)
    
    # Verify handle_device was called only once
    mock_handle_device.assert_called_once_with(device, 123, None, None)
    
    # Verify result includes success flag and retry count
    assert result["success"] is True
    assert result["retries"] == 0
    assert result["result"] == "abc123"

@patch('netraven.worker.dispatcher.handle_device')
@patch('netraven.worker.dispatcher.classify_exception')
@patch('netraven.worker.dispatcher.time.sleep')
def test_task_with_retry_success_after_retry(mock_sleep, mock_classify, mock_handle_device):
    """Test task succeeds after retry."""
    # First call fails, second succeeds
    mock_handle_device.side_effect = [
        {"success": False, "error": "Timeout"},
        {"success": True, "result": "abc123", "error": None}
    ]
    
    # Mock error classification
    error_info = ErrorInfo(
        category=ErrorCategory.TIMEOUT,
        message="Connection timed out",
        is_retriable=True,
        retry_count=0,
        max_retries=2,
        retry_delay=1
    )
    mock_classify.return_value = error_info
    
    device = MockDevice(1, "test-device", "192.168.1.1")
    result = task_with_retry(device, 123)
    
    # Verify handle_device was called twice
    assert mock_handle_device.call_count == 2
    
    # Verify sleep was called
    mock_sleep.assert_called_once()
    
    # Verify result
    assert result["success"] is True
    assert result["retries"] == 1
    assert result["result"] == "abc123"

@patch('netraven.worker.dispatcher.handle_device')
@patch('netraven.worker.dispatcher.classify_exception')
@patch('netraven.worker.dispatcher.time.sleep')
def test_task_with_retry_gives_up_after_max_retries(mock_sleep, mock_classify, mock_handle_device):
    """Test task fails after max retries."""
    # All attempts fail
    error_response = {"success": False, "error": "Timeout"}
    mock_handle_device.return_value = error_response
    
    # Mock error classification
    error_info = ErrorInfo(
        category=ErrorCategory.TIMEOUT,
        message="Connection timed out",
        is_retriable=True,
        retry_count=0,
        max_retries=2,
        retry_delay=1
    )
    mock_classify.return_value = error_info
    
    device = MockDevice(1, "test-device", "192.168.1.1")
    result = task_with_retry(device, 123, retry_config={"max_retries": 2, "retry_delay": 1})
    
    # Verify handle_device was called max+1 times (initial + retries)
    assert mock_handle_device.call_count == 3
    
    # Verify sleep was called for each retry
    assert mock_sleep.call_count == 2
    
    # Verify result shows failure and max retries
    assert result["success"] is False
    assert result["retries"] == 2
    assert result["max_retries"] == 2

@patch('netraven.worker.dispatcher.handle_device')
@patch('netraven.worker.dispatcher.classify_exception')
def test_task_with_retry_non_retriable_error(mock_classify, mock_handle_device):
    """Test task does not retry non-retriable errors."""
    # Simulate a non-retriable error
    mock_handle_device.side_effect = NetmikoAuthenticationException("Auth failed")
    
    # Mock error classification
    error_info = ErrorInfo(
        category=ErrorCategory.AUTHENTICATION,
        message="Authentication failed",
        exception=NetmikoAuthenticationException("Auth failed"),
        is_retriable=False
    )
    mock_classify.return_value = error_info
    
    device = MockDevice(1, "test-device", "192.168.1.1")
    result = task_with_retry(device, 123)
    
    # Verify handle_device was called only once
    mock_handle_device.assert_called_once()
    
    # Verify result
    assert result["success"] is False
    assert result["error"] == str(mock_handle_device.side_effect)
    assert result["retries"] == 0

@patch('netraven.worker.dispatcher.handle_device')
@patch('netraven.worker.dispatcher.classify_exception')
@patch('netraven.worker.dispatcher.time.sleep')
def test_task_with_retry_exponential_backoff(mock_sleep, mock_classify, mock_handle_device):
    """Test exponential backoff is applied correctly."""
    # All attempts fail
    error_response = {"success": False, "error": "Timeout"}
    mock_handle_device.return_value = error_response
    
    # Create error_info with next_retry_delay that returns increasing values
    error_info = MagicMock()
    error_info.is_retriable = True
    error_info.next_retry_delay.side_effect = [5, 10]  # First and second retry delays
    error_info.to_dict.return_value = {}
    error_info.increment_retry.return_value = error_info  # Return self for simplicity
    mock_classify.return_value = error_info
    
    device = MockDevice(1, "test-device", "192.168.1.1")
    task_with_retry(device, 123, retry_config={"max_retries": 2, "retry_delay": 5})
    
    # Verify sleep was called with increasing durations
    mock_sleep.assert_has_calls([call(5), call(10)])

# --- Test dispatch_tasks function ---

@patch('netraven.worker.dispatcher.ThreadPoolExecutor')
def test_dispatch_tasks_empty_device_list(mock_executor):
    """Test dispatcher handles empty device list."""
    result = dispatch_tasks([], 123)
    
    # Verify no thread pool was created
    mock_executor.assert_not_called()
    
    # Verify empty result
    assert result == []

@patch('netraven.worker.dispatcher.ThreadPoolExecutor')
@patch('concurrent.futures.as_completed')
@patch('netraven.worker.dispatcher.task_with_retry')
def test_dispatch_tasks_thread_pool_size(mock_task, mock_as_completed, mock_executor_class):
    """Test thread pool size configuration."""
    # Setup mock executor
    mock_executor = MagicMock()
    mock_executor_class.return_value.__enter__.return_value = mock_executor
    mock_as_completed.return_value = []  # No futures to process
    
    # Test with default size
    dispatch_tasks([MockDevice(1, "device1", "192.168.1.1")], 123)
    mock_executor_class.assert_called_with(max_workers=5)  # Default size
    
    # Test with custom size
    dispatch_tasks(
        [MockDevice(1, "device1", "192.168.1.1")], 
        123, 
        config={"worker": {"thread_pool_size": 10}}
    )
    mock_executor_class.assert_called_with(max_workers=10)  # Custom size

@patch('netraven.worker.dispatcher.ThreadPoolExecutor')
def test_dispatch_tasks_results_collection(mock_executor_class):
    """Test dispatcher collects results from all devices."""
    # Setup mock executor and futures
    mock_executor = MagicMock()
    mock_executor_class.return_value.__enter__.return_value = mock_executor
    
    # Create mock futures with results
    future1 = MagicMock()
    future1.result.return_value = {"device_id": 1, "success": True}
    
    future2 = MagicMock()
    future2.result.return_value = {"device_id": 2, "success": False, "error": "Failed"}
    
    # Setup mock as_completed to return our futures
    with patch('concurrent.futures.as_completed', return_value=[future1, future2]):
        # Mock task_with_retry to be a no-op since we're mocking futures directly
        with patch('netraven.worker.dispatcher.task_with_retry'):
            devices = [
                MockDevice(1, "device1", "192.168.1.1"),
                MockDevice(2, "device2", "192.168.1.2")
            ]
            
            # Run dispatcher
            results = dispatch_tasks(devices, 123)
            
            # Verify results were collected
            assert len(results) == 2
            assert any(r["device_id"] == 1 and r["success"] for r in results)
            assert any(r["device_id"] == 2 and not r["success"] for r in results)

@patch('netraven.worker.dispatcher.ThreadPoolExecutor')
def test_dispatch_tasks_handles_thread_exceptions(mock_executor_class):
    """Test that dispatcher handles thread exceptions gracefully."""
    # Setup mock executor
    mock_executor = MagicMock()
    mock_executor_class.return_value.__enter__.return_value = mock_executor
    
    # Create a future that raises exception
    error_future = MagicMock()
    error_future.result.side_effect = Exception("Thread error")
    
    # Setup as_completed to return our future
    with patch('concurrent.futures.as_completed', return_value=[error_future]):
        # Mock task_with_retry and classify_exception
        with patch('netraven.worker.dispatcher.task_with_retry'):
            with patch('netraven.worker.dispatcher.classify_exception') as mock_classify:
                # Mock error classification
                error_info = MagicMock()
                error_info.to_dict.return_value = {"category": "UNKNOWN"}
                mock_classify.return_value = error_info
                
                devices = [MockDevice(1, "device1", "192.168.1.1")]
                
                # Run dispatcher
                results = dispatch_tasks(devices, 123)
                
                # Verify error was handled and result created
                assert len(results) == 1
                assert results[0]["success"] is False
                assert "Thread error" in results[0]["error"] 