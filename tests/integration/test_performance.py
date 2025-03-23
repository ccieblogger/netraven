"""
Integration tests for performance and reliability.

This module tests the performance and reliability aspects of the NetRaven application, including:
- Large configuration file handling
- Concurrent API request handling
- Database query performance
- Resource usage
- Error handling and recovery
"""

import pytest
import time
import uuid
import os
import random
import tempfile
import threading
import concurrent.futures
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from netraven.web.app import app
from netraven.web.auth.jwt import create_access_token
from netraven.core.backup import BackupManager
from netraven.core.storage import LocalFileStorage
from netraven.core.device_comm import DeviceConnector

# Test client
client = TestClient(app)


@pytest.fixture
def admin_token():
    """Create an admin token for testing."""
    return create_access_token(
        data={"sub": "admin-user", "roles": ["admin"]},
        scopes=["admin:*"],
        expires_minutes=15
    )


@pytest.fixture
def user_token():
    """Create a regular user token for testing."""
    return create_access_token(
        data={"sub": "regular-user", "roles": ["user"]},
        scopes=["user:read", "user:write"],
        expires_minutes=15
    )


@pytest.fixture
def test_storage_dir():
    """Create a temporary directory for storage tests."""
    storage_dir = tempfile.mkdtemp(prefix="netraven_perf_test_")
    return storage_dir


@pytest.fixture
def local_storage(test_storage_dir):
    """Create a local file storage instance."""
    return LocalFileStorage(base_path=test_storage_dir)


def generate_large_config(size_kb=1000):
    """Generate a large configuration file of approximately the given size in KB."""
    # Create a config with many interfaces and routes
    lines = []
    lines.append("hostname LargeRouter")
    lines.append("!")
    
    # Add version and service info
    lines.append("version 16.9")
    lines.append("service timestamps debug datetime msec")
    lines.append("service timestamps log datetime msec")
    lines.append("service password-encryption")
    lines.append("!")
    
    # Add many interface configurations
    for i in range(1, 2000):  # This should generate a config > 1MB
        lines.append(f"interface GigabitEthernet0/{i}")
        lines.append(f" description Interface {i}")
        lines.append(f" ip address 10.{i//256}.{i%256}.1 255.255.255.0")
        if i % 2 == 0:
            lines.append(" duplex full")
        if i % 3 == 0:
            lines.append(" speed 1000")
        if i % 5 == 0:
            lines.append(" negotiation auto")
        lines.append(" no shutdown")
        lines.append("!")
    
    # Add routing configuration
    lines.append("ip routing")
    for i in range(1, 500):
        lines.append(f"ip route 192.168.{i}.0 255.255.255.0 10.0.0.{i}")
    
    # Add access lists
    lines.append("ip access-list extended LARGE-ACL")
    for i in range(1, 500):
        action = "permit" if i % 3 == 0 else "deny"
        lines.append(f" {action} ip host 10.1.1.{i} any")
    lines.append("!")
    
    # Add some other common configurations
    lines.append("ntp server 10.0.0.1")
    lines.append("ntp server 10.0.0.2")
    lines.append("!")
    lines.append("snmp-server community public RO")
    lines.append("snmp-server community private RW")
    lines.append("!")
    lines.append("line con 0")
    lines.append(" logging synchronous")
    lines.append("line vty 0 4")
    lines.append(" login local")
    lines.append(" transport input ssh")
    lines.append("!")
    lines.append("end")
    
    config = "\n".join(lines)
    actual_size_kb = len(config.encode('utf-8')) / 1024
    
    # If the config is not large enough, add more content
    while actual_size_kb < size_kb:
        # Add more interfaces
        for i in range(2000, 3000):
            lines.append(f"interface Vlan{i}")
            lines.append(f" description VLAN {i}")
            lines.append(f" ip address 172.16.{i//256}.{i%256} 255.255.255.0")
            lines.append(" no shutdown")
            lines.append("!")
        
        config = "\n".join(lines)
        actual_size_kb = len(config.encode('utf-8')) / 1024
        if actual_size_kb >= size_kb:
            break
    
    return config


def test_large_config_file_handling(admin_token, local_storage, monkeypatch):
    """Test handling of large configuration files."""
    # Generate a large config file (1MB+)
    large_config = generate_large_config(size_kb=1024)  # 1MB
    
    # Verify the config is indeed large
    assert len(large_config.encode('utf-8')) > 1024 * 1024  # > 1MB
    
    # Setup a mock device and device connector
    device_id = str(uuid.uuid4())
    device = {
        "id": device_id,
        "hostname": "large-config-router",
        "ip_address": "192.168.1.100",
        "device_type": "cisco_ios",
        "status": "active"
    }
    
    # Patch necessary functions
    import netraven.web.routers.devices
    monkeypatch.setattr(netraven.web.routers.devices, "get_device_by_id", lambda db, id: device)
    
    with patch("netraven.core.device_comm.DeviceConnector.get_config") as mock_get_config:
        mock_get_config.return_value = large_config
        
        # Measure time to retrieve and process the large config
        start_time = time.time()
        
        response = client.get(
            f"/api/devices/{device_id}/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        end_time = time.time()
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert "raw_config" in data
        assert data["raw_config"] == large_config
        
        # Check performance
        processing_time = end_time - start_time
        print(f"Large config processing time: {processing_time:.2f} seconds")
        
        # The actual threshold may vary depending on the system, but we expect it to be reasonable
        assert processing_time < 5.0, f"Processing time too long: {processing_time:.2f} seconds"
    
    # Test storing a large backup
    with patch("netraven.web.routers.backups.get_storage", return_value=local_storage):
        with patch("netraven.web.routers.devices.get_device_config") as mock_get_device_config:
            mock_get_device_config.return_value = large_config
            
            # Create a backup with the large config
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{device_id}/backups/{timestamp}.cfg"
            
            # Store the large config
            start_time = time.time()
            
            local_storage.store(backup_path, large_config, {
                "device_id": device_id,
                "timestamp": timestamp,
                "file_size": len(large_config.encode('utf-8')),
                "device_type": "cisco_ios"
            })
            
            end_time = time.time()
            storage_time = end_time - start_time
            
            print(f"Large config storage time: {storage_time:.2f} seconds")
            assert storage_time < 2.0, f"Storage time too long: {storage_time:.2f} seconds"
            
            # Verify the file was stored correctly
            assert os.path.exists(os.path.join(local_storage.base_path, backup_path))
            
            # Retrieve the large config
            start_time = time.time()
            
            retrieved_config = local_storage.retrieve(backup_path)
            
            end_time = time.time()
            retrieval_time = end_time - start_time
            
            print(f"Large config retrieval time: {retrieval_time:.2f} seconds")
            assert retrieval_time < 1.0, f"Retrieval time too long: {retrieval_time:.2f} seconds"
            
            # Verify the retrieved config is correct
            assert retrieved_config == large_config


def test_concurrent_api_requests(admin_token, monkeypatch):
    """Test concurrent API requests."""
    # Create 10 devices for testing
    devices = []
    for i in range(10):
        device_id = str(uuid.uuid4())
        devices.append({
            "id": device_id,
            "hostname": f"device-{i}",
            "ip_address": f"192.168.1.{10+i}",
            "device_type": "cisco_ios",
            "status": "active"
        })
    
    # Patch the get_devices function
    with patch("netraven.web.routers.devices.get_devices") as mock_get_devices:
        mock_get_devices.return_value = devices
        
        # Function to make a request to get all devices
        def make_request():
            try:
                response = client.get(
                    "/api/devices",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                return response.status_code, response.elapsed.total_seconds()
            except Exception as e:
                return str(e), None
        
        # Make 50 concurrent requests
        num_requests = 50
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Check results
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results if result[1] is not None]
        
        # All requests should be successful
        assert all(code == 200 for code in status_codes), f"Not all requests were successful: {status_codes}"
        
        # Calculate average response time
        avg_response_time = sum(response_times) / len(response_times)
        print(f"Average response time for {num_requests} concurrent requests: {avg_response_time:.4f} seconds")
        print(f"Total time for {num_requests} concurrent requests: {total_time:.2f} seconds")
        
        # Response time should be reasonable
        assert avg_response_time < 0.5, f"Average response time too high: {avg_response_time:.4f} seconds"


def test_database_query_performance(admin_token, monkeypatch):
    """Test database query performance."""
    # Create many devices for testing database performance
    num_devices = 500
    devices = []
    device_ids = []
    
    for i in range(num_devices):
        device_id = str(uuid.uuid4())
        device_ids.append(device_id)
        
        # Create a device with random properties
        devices.append({
            "id": device_id,
            "hostname": f"device-{i}",
            "ip_address": f"10.{i//256}.{i%256}.1",
            "device_type": random.choice(["cisco_ios", "cisco_nxos", "arista_eos", "juniper_junos"]),
            "status": random.choice(["active", "inactive", "maintenance"]),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "updated_at": datetime.now().isoformat()
        })
    
    # Patch the get_devices function with pagination
    with patch("netraven.web.routers.devices.get_devices") as mock_get_devices:
        def paginated_get_devices(db, skip=0, limit=10, filters=None):
            filtered_devices = devices
            if filters:
                # Apply filters
                if 'device_type' in filters:
                    filtered_devices = [d for d in filtered_devices if d["device_type"] == filters['device_type']]
                if 'status' in filters:
                    filtered_devices = [d for d in filtered_devices if d["status"] == filters['status']]
            
            # Apply pagination
            return filtered_devices[skip:skip+limit]
        
        mock_get_devices.side_effect = paginated_get_devices
        
        # Test basic pagination
        start_time = time.time()
        
        response = client.get(
            "/api/devices?skip=0&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        end_time = time.time()
        basic_query_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        print(f"Basic pagination query time: {basic_query_time:.4f} seconds")
        assert basic_query_time < 0.1, f"Basic query time too high: {basic_query_time:.4f} seconds"
        
        # Test filtered query
        start_time = time.time()
        
        response = client.get(
            "/api/devices?skip=0&limit=10&device_type=cisco_ios&status=active",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        end_time = time.time()
        filtered_query_time = end_time - start_time
        
        assert response.status_code == 200
        
        print(f"Filtered query time: {filtered_query_time:.4f} seconds")
        assert filtered_query_time < 0.2, f"Filtered query time too high: {filtered_query_time:.4f} seconds"
        
        # Test last page query (should not load all data)
        start_time = time.time()
        
        response = client.get(
            f"/api/devices?skip={num_devices-10}&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        end_time = time.time()
        last_page_query_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10
        
        print(f"Last page query time: {last_page_query_time:.4f} seconds")
        assert last_page_query_time < 0.2, f"Last page query time too high: {last_page_query_time:.4f} seconds"


def test_error_handling_and_recovery(admin_token, monkeypatch):
    """Test error handling and recovery."""
    device_id = str(uuid.uuid4())
    
    # Test handling of non-existent device
    with patch("netraven.web.routers.devices.get_device_by_id") as mock_get_device:
        mock_get_device.return_value = None
        
        response = client.get(
            f"/api/devices/{device_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    # Test handling of connection errors
    with patch("netraven.web.routers.devices.get_device_by_id") as mock_get_device:
        mock_get_device.return_value = {
            "id": device_id,
            "hostname": "test-device",
            "ip_address": "192.168.1.100",
            "device_type": "cisco_ios",
            "status": "active"
        }
        
        with patch("netraven.core.device_comm.DeviceConnector.connect") as mock_connect:
            # Simulate a connection error
            mock_connect.side_effect = Exception("Connection timeout")
            
            response = client.post(
                f"/api/devices/{device_id}/connect",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code in [500, 503]
            assert "connection" in response.json()["detail"].lower()
            assert "timeout" in response.json()["detail"].lower()
    
    # Test automatic retry mechanism
    with patch("netraven.web.routers.devices.get_device_by_id") as mock_get_device:
        mock_get_device.return_value = {
            "id": device_id,
            "hostname": "test-device",
            "ip_address": "192.168.1.100",
            "device_type": "cisco_ios",
            "status": "active"
        }
        
        with patch("netraven.core.device_comm.DeviceConnector.connect") as mock_connect:
            # Fail on first attempt, succeed on second
            attempt_count = 0
            
            def connect_with_retry(*args, **kwargs):
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count == 1:
                    raise Exception("Connection timeout")
                return True
            
            mock_connect.side_effect = connect_with_retry
            
            with patch("netraven.web.routers.devices.should_retry_connection", return_value=True):
                response = client.post(
                    f"/api/devices/{device_id}/connect?retry=true",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                assert response.status_code == 200
                assert attempt_count == 2  # Should have retried once


def test_resource_intensive_operations(admin_token, local_storage, monkeypatch):
    """Test resource-intensive operations."""
    # Create a large set of devices
    num_devices = 50
    devices = []
    
    for i in range(num_devices):
        device_id = str(uuid.uuid4())
        devices.append({
            "id": device_id,
            "hostname": f"device-{i}",
            "ip_address": f"10.{i//256}.{i%256}.1",
            "device_type": random.choice(["cisco_ios", "cisco_nxos", "arista_eos", "juniper_junos"]),
            "status": "active"
        })
    
    # Patch the necessary functions
    with patch("netraven.web.routers.devices.get_devices") as mock_get_devices:
        mock_get_devices.return_value = devices
        
        with patch("netraven.web.routers.backups.get_storage", return_value=local_storage):
            with patch("netraven.core.device_comm.DeviceConnector.get_config") as mock_get_config:
                # Generate different configs for different devices
                def get_device_config(device_id):
                    # Generate a config of varying size (100KB to 500KB)
                    size_kb = random.randint(100, 500)
                    device_index = next((i for i, d in enumerate(devices) if d["id"] == device_id), 0)
                    config = f"hostname device-{device_index}\n"
                    
                    # Add interfaces based on device index
                    for j in range(100 * (device_index % 10 + 1)):
                        config += f"interface GigabitEthernet0/{j}\n"
                        config += f" description Interface {j}\n"
                        config += f" ip address 10.{j//256}.{j%256}.1 255.255.255.0\n"
                        config += " no shutdown\n"
                    
                    # Add more content to reach the desired size
                    while len(config.encode('utf-8')) < size_kb * 1024:
                        config += f"! Padding line {len(config)}\n"
                    
                    return config
                
                mock_get_config.side_effect = get_device_config
                
                # Test creating backups for all devices
                start_time = time.time()
                
                with patch("netraven.web.routers.devices.create_backup") as mock_create_backup:
                    def simulate_backup(db, device_id):
                        config = get_device_config(device_id)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = f"{device_id}/backups/{timestamp}.cfg"
                        
                        # Actually store the config to test storage performance
                        local_storage.store(path, config, {
                            "device_id": device_id,
                            "timestamp": timestamp,
                            "file_size": len(config.encode('utf-8'))
                        })
                        
                        return {
                            "id": str(uuid.uuid4()),
                            "device_id": device_id,
                            "timestamp": timestamp,
                            "file_path": path,
                            "file_size": len(config.encode('utf-8')),
                            "status": "completed"
                        }
                    
                    mock_create_backup.side_effect = simulate_backup
                    
                    # Create backups for all devices in parallel
                    def backup_device(device_id):
                        response = client.post(
                            f"/api/devices/{device_id}/backup",
                            headers={"Authorization": f"Bearer {admin_token}"}
                        )
                        return response.status_code
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                        futures = [executor.submit(backup_device, device["id"]) for device in devices]
                        results = [future.result() for future in concurrent.futures.as_completed(futures)]
                    
                    end_time = time.time()
                    total_time = end_time - start_time
                    
                    # All backups should be successful
                    assert all(code == 200 for code in results)
                    
                    print(f"Time to backup {num_devices} devices in parallel: {total_time:.2f} seconds")
                    # The timeout threshold depends on the system, but let's set a reasonable limit
                    assert total_time < 60.0, f"Parallel backup took too long: {total_time:.2f} seconds"


def test_system_degradation_under_load(admin_token, monkeypatch):
    """Test system behavior under heavy load."""
    # Create a function that makes a simple API request and measures the response time
    def measure_response_time():
        start = time.time()
        response = client.get(
            "/api/health",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        end = time.time()
        return end - start, response.status_code
    
    # Measure baseline response time
    baseline_times = []
    for _ in range(5):
        time_taken, status_code = measure_response_time()
        if status_code == 200:
            baseline_times.append(time_taken)
        time.sleep(0.1)  # Short delay between baseline measurements
    
    # Calculate baseline average
    baseline_avg = sum(baseline_times) / len(baseline_times)
    print(f"Baseline average response time: {baseline_avg:.4f} seconds")
    
    # Now simulate heavy load by making many concurrent requests
    def make_heavy_request():
        # Make a more intensive request
        response = client.get(
            "/api/devices?limit=100",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        return response.status_code
    
    # Start many threads making heavy requests
    num_heavy_threads = 20
    heavy_threads = []
    
    for _ in range(num_heavy_threads):
        thread = threading.Thread(target=make_heavy_request)
        thread.daemon = True
        heavy_threads.append(thread)
        thread.start()
    
    # While heavy requests are running, measure response time of the health endpoint
    loaded_times = []
    for _ in range(10):
        time_taken, status_code = measure_response_time()
        if status_code == 200:
            loaded_times.append(time_taken)
        time.sleep(0.2)  # Small delay between measurements
    
    # Wait for all heavy threads to complete
    for thread in heavy_threads:
        thread.join(timeout=10)
    
    # Calculate loaded average
    if loaded_times:
        loaded_avg = sum(loaded_times) / len(loaded_times)
        print(f"Loaded average response time: {loaded_avg:.4f} seconds")
        
        # Calculate degradation factor
        degradation_factor = loaded_avg / baseline_avg
        print(f"Degradation factor under load: {degradation_factor:.2f}x")
        
        # Some degradation is expected, but it shouldn't be too severe
        # Adjust threshold as needed based on the application's characteristics
        assert degradation_factor < 10.0, f"Excessive degradation under load: {degradation_factor:.2f}x"
    else:
        print("No valid measurements under load - system may be severely degraded")
        assert False, "No valid measurements under load"


def test_memory_usage_for_large_operations(admin_token, local_storage, monkeypatch):
    """Test memory usage for large operations."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
    except ImportError:
        print("psutil not available, skipping memory usage test")
        return
    
    # Measure baseline memory usage
    baseline_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    print(f"Baseline memory usage: {baseline_memory:.2f} MB")
    
    # Generate a large configuration (5MB)
    large_config = generate_large_config(size_kb=5120)  # 5MB
    
    # Verify the size
    config_size_mb = len(large_config.encode('utf-8')) / (1024 * 1024)
    print(f"Generated configuration size: {config_size_mb:.2f} MB")
    
    # Setup a mock device
    device_id = str(uuid.uuid4())
    device = {
        "id": device_id,
        "hostname": "memory-test-device",
        "ip_address": "192.168.1.200",
        "device_type": "cisco_ios",
        "status": "active"
    }
    
    # Patch the necessary functions
    import netraven.web.routers.devices
    monkeypatch.setattr(netraven.web.routers.devices, "get_device_by_id", lambda db, id: device)
    
    with patch("netraven.core.device_comm.DeviceConnector.get_config") as mock_get_config:
        mock_get_config.return_value = large_config
        
        with patch("netraven.web.routers.backups.get_storage", return_value=local_storage):
            # Create a backup with the large config
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Test memory usage during processing
            response = client.get(
                f"/api/devices/{device_id}/config",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            # Measure memory after processing
            processing_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
            print(f"Memory usage after processing: {processing_memory:.2f} MB")
            
            # Memory usage should increase due to processing,
            # but not by an excessive amount relative to the config size
            memory_increase = processing_memory - baseline_memory
            print(f"Memory increase during processing: {memory_increase:.2f} MB")
            
            # The increase shouldn't be more than a few times the size of the config
            # This is a heuristic that may need adjustment
            assert memory_increase < config_size_mb * 5, f"Excessive memory usage: {memory_increase:.2f} MB"
            
            # Test memory usage for backup creation
            with patch("netraven.web.routers.devices.create_backup") as mock_create_backup:
                def simulate_backup(db, device_id):
                    path = f"{device_id}/backups/{timestamp}.cfg"
                    
                    # Actually store the config to test storage memory usage
                    local_storage.store(path, large_config, {
                        "device_id": device_id,
                        "timestamp": timestamp,
                        "file_size": len(large_config.encode('utf-8'))
                    })
                    
                    return {
                        "id": str(uuid.uuid4()),
                        "device_id": device_id,
                        "timestamp": timestamp,
                        "file_path": path,
                        "file_size": len(large_config.encode('utf-8')),
                        "status": "completed"
                    }
                
                mock_create_backup.side_effect = simulate_backup
                
                response = client.post(
                    f"/api/devices/{device_id}/backup",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                # Measure memory after backup
                backup_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
                print(f"Memory usage after backup: {backup_memory:.2f} MB")
                
                # Memory usage should not grow exponentially
                memory_increase = backup_memory - baseline_memory
                print(f"Memory increase during backup: {memory_increase:.2f} MB")
                
                # Similar heuristic as above
                assert memory_increase < config_size_mb * 5, f"Excessive memory usage during backup: {memory_increase:.2f} MB" 