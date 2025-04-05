"""
Integration tests for system functionality.

This module tests the core system functionality of the NetRaven application, including:
- Scheduled operations (backups, key rotation)
- Health monitoring and status reporting
- Device connectivity testing
- Configuration comparison
- System metrics and usage statistics
"""

import pytest
import time
import uuid
import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from typing import Dict, Tuple

from fastapi.testclient import TestClient
from netraven.web.app import app
from netraven.web.auth.jwt import create_access_token
from netraven.core.scheduler import Scheduler, ScheduledTask
from netraven.core.monitoring import SystemStatus, DeviceStatus
from netraven.core.metrics import MetricsCollector
from netraven.core.backup import BackupManager
from netraven.core.device_comm import DeviceConnector
from tests.utils.api_test_utils import create_auth_headers

# Test client
client = TestClient(app)

# Test client - Use httpx for async tests
from httpx import AsyncClient
import pytest_asyncio

# Use the actual app for integration tests
from netraven.web.main import app 

# --- Fixtures ---

@pytest_asyncio.fixture(scope="module")
async def async_client() -> AsyncClient:
    """Provides an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(scope="module")
async def test_user(async_client: AsyncClient) -> Dict[str, Any]:
    """Creates a standard user for testing system flows."""
    # Requires admin privileges to create users - assumes an admin exists
    # TODO: Use a proper admin fixture or ensure admin exists in test DB setup
    
    # For now, skip user creation if admin setup is complex, assume testuser exists
    # username = f"systest-{uuid.uuid4().hex[:6]}"
    # user_data = {
    #     "username": username,
    #     "email": f"{username}@example.com",
    #     "password": "testpassword",
    #     "is_admin": False,
    #     "is_active": True
    # }
    # Need admin token here
    # response = await async_client.post("/api/v1/users", json=user_data, headers=admin_headers)
    # response.raise_for_status()
    # return response.json()
    
    # Assume 'testuser' with password 'testpassword' exists from seeding/conftest
    return {"username": "testuser", "password": "testpassword"}

@pytest_asyncio.fixture(scope="module")
async def logged_in_client(async_client: AsyncClient, test_user: Dict[str, Any]) -> Tuple[AsyncClient, str]:
    """Provides an authenticated async client and the access token."""
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"],
    }
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    response.raise_for_status()
    token = response.json()["access_token"]
    async_client.headers = {"Authorization": f"Bearer {token}"}
    yield async_client, token
    # Teardown: remove auth headers after tests in this scope are done
    async_client.headers = {}

@pytest.fixture
def admin_token():
    """Create an admin token for testing."""
    return create_access_token(
        data={"sub": "admin-user", "roles": ["admin"]},
        scopes=["admin:*"],
        expires_minutes=15
    )


@pytest.fixture
def test_dirs():
    """Create temporary directories for testing."""
    temp_dirs = {
        "backup_dir": tempfile.mkdtemp(prefix="netraven_backup_test_"),
        "db_dir": tempfile.mkdtemp(prefix="netraven_db_test_"),
        "keys_dir": tempfile.mkdtemp(prefix="netraven_keys_test_")
    }
    yield temp_dirs
    # Cleanup is handled by the tempfile module


@pytest.fixture
def mock_scheduler():
    """Create a mock scheduler for testing."""
    scheduler = MagicMock(spec=Scheduler)
    scheduler.tasks = []
    
    def add_task(task_id, func, schedule, **kwargs):
        task = ScheduledTask(task_id, func, schedule, **kwargs)
        scheduler.tasks.append(task)
        return task
    
    def get_task(task_id):
        for task in scheduler.tasks:
            if task.id == task_id:
                return task
        return None
    
    def list_tasks():
        return scheduler.tasks
    
    # Setup mock methods
    scheduler.add_task.side_effect = add_task
    scheduler.get_task.side_effect = get_task
    scheduler.list_tasks.side_effect = list_tasks
    
    return scheduler


@pytest.fixture
def mock_device():
    """Create a mock device for testing."""
    device = {
        "id": str(uuid.uuid4()),
        "hostname": "test-device",
        "ip_address": "192.168.1.100",
        "device_type": "cisco_ios",
        "status": "active",
        "last_backup": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    return device


def test_scheduler_add_backup_task(mock_scheduler, admin_token, monkeypatch):
    """Test adding a scheduled backup task."""
    # Patch the application to use our mock scheduler
    import netraven.web.routers.admin
    monkeypatch.setattr(netraven.web.routers.admin, "get_scheduler", lambda: mock_scheduler)
    
    # Schedule data to submit
    schedule_data = {
        "task_type": "backup",
        "schedule": "0 0 * * *",  # Daily at midnight
        "device_id": str(uuid.uuid4()),
        "description": "Daily backup of test device"
    }
    
    # Add a scheduled task
    response = client.post(
        "/api/admin/scheduler/tasks",
        json=schedule_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["task_type"] == "backup"
    assert data["schedule"] == "0 0 * * *"
    assert "id" in data
    
    # Verify the task was added to the scheduler
    task_id = data["id"]
    mock_scheduler.add_task.assert_called_once()
    assert len(mock_scheduler.tasks) == 1
    assert mock_scheduler.tasks[0].id == task_id
    
    # Get the scheduled task
    response = client.get(
        f"/api/admin/scheduler/tasks/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    task_data = response.json()
    assert task_data["id"] == task_id
    assert task_data["schedule"] == "0 0 * * *"
    
    # List all tasks
    response = client.get(
        "/api/admin/scheduler/tasks",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == task_id
    
    # Delete the task
    response = client.delete(
        f"/api/admin/scheduler/tasks/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200


def test_scheduler_key_rotation_task(mock_scheduler, admin_token, monkeypatch):
    """Test adding a scheduled key rotation task."""
    # Patch the application to use our mock scheduler
    import netraven.web.routers.admin
    monkeypatch.setattr(netraven.web.routers.admin, "get_scheduler", lambda: mock_scheduler)
    
    # Schedule data to submit
    schedule_data = {
        "task_type": "key_rotation",
        "schedule": "0 0 1 * *",  # Monthly on the 1st
        "description": "Monthly key rotation"
    }
    
    # Add a scheduled task
    response = client.post(
        "/api/admin/scheduler/tasks",
        json=schedule_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["task_type"] == "key_rotation"
    assert data["schedule"] == "0 0 1 * *"
    assert "id" in data
    
    # Verify the task was added to the scheduler
    mock_scheduler.add_task.assert_called_once()
    
    # Update the task
    task_id = data["id"]
    update_data = {
        "schedule": "0 0 15 * *",  # Change to the 15th of each month
        "description": "Updated key rotation schedule"
    }
    
    response = client.put(
        f"/api/admin/scheduler/tasks/{task_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["schedule"] == "0 0 15 * *"
    assert updated_data["description"] == "Updated key rotation schedule"


def test_task_execution_history(mock_scheduler, admin_token, monkeypatch):
    """Test viewing task execution history."""
    # Patch the application to use our mock scheduler
    import netraven.web.routers.admin
    monkeypatch.setattr(netraven.web.routers.admin, "get_scheduler", lambda: mock_scheduler)
    
    # Add a task first
    schedule_data = {
        "task_type": "backup",
        "schedule": "0 0 * * *",
        "device_id": str(uuid.uuid4()),
        "description": "Daily backup"
    }
    
    response = client.post(
        "/api/admin/scheduler/tasks",
        json=schedule_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    task_id = response.json()["id"]
    
    # Mock task execution history
    history_data = [
        {
            "task_id": task_id,
            "started_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "finished_at": (datetime.now() - timedelta(days=1) + timedelta(minutes=5)).isoformat(),
            "status": "success",
            "result": "Backup created successfully"
        },
        {
            "task_id": task_id,
            "started_at": datetime.now().isoformat(),
            "finished_at": (datetime.now() + timedelta(minutes=5)).isoformat(),
            "status": "success",
            "result": "Backup created successfully"
        }
    ]
    
    # Patch the get_task_history function
    with patch("netraven.web.routers.admin.get_task_history") as mock_history:
        mock_history.return_value = history_data
        
        # Get task execution history
        response = client.get(
            f"/api/admin/scheduler/tasks/{task_id}/history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        history = response.json()
        assert len(history) == 2
        assert history[0]["task_id"] == task_id
        assert history[0]["status"] == "success"


def test_system_health_monitoring(admin_token, monkeypatch):
    """Test system health monitoring."""
    # Create a mock system status
    system_status = {
        "status": "healthy",
        "components": {
            "database": {
                "status": "healthy",
                "message": "Database is connected and responding"
            },
            "scheduler": {
                "status": "healthy",
                "message": "Scheduler is running with 5 active tasks"
            },
            "device_connector": {
                "status": "healthy",
                "message": "Device connector service is operational"
            },
            "storage": {
                "status": "healthy",
                "message": "Storage service is operational",
                "details": {
                    "disk_usage": "45%",
                    "available_space": "100GB"
                }
            }
        },
        "last_updated": datetime.now().isoformat()
    }
    
    # Patch the get_system_status function
    with patch("netraven.web.routers.health.get_system_status") as mock_status:
        mock_status.return_value = system_status
        
        # Get system health
        response = client.get(
            "/api/health/system",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert "database" in data["components"]
        assert data["components"]["database"]["status"] == "healthy"


def test_device_connectivity_monitoring(admin_token, mock_device, monkeypatch):
    """Test device connectivity monitoring."""
    device_id = mock_device["id"]
    
    # Mock device status
    device_status = {
        "device_id": device_id,
        "hostname": mock_device["hostname"],
        "ip_address": mock_device["ip_address"],
        "status": "online",
        "last_checked": datetime.now().isoformat(),
        "response_time": 25,  # ms
        "connectivity_history": [
            {"timestamp": (datetime.now() - timedelta(hours=1)).isoformat(), "status": "online", "response_time": 30},
            {"timestamp": (datetime.now() - timedelta(hours=2)).isoformat(), "status": "online", "response_time": 28},
            {"timestamp": (datetime.now() - timedelta(hours=3)).isoformat(), "status": "offline", "response_time": None}
        ]
    }
    
    # Patch functions to return mock data
    with patch("netraven.web.routers.devices.get_device_by_id") as mock_get_device:
        mock_get_device.return_value = mock_device
        
        with patch("netraven.web.routers.devices.get_device_status") as mock_get_status:
            mock_get_status.return_value = device_status
            
            # Get device connectivity status
            response = client.get(
                f"/api/devices/{device_id}/status",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["device_id"] == device_id
            assert data["status"] == "online"
            assert "connectivity_history" in data


def test_scheduled_device_connectivity_check(mock_scheduler, admin_token, monkeypatch):
    """Test scheduled device connectivity checks."""
    # Patch the application to use our mock scheduler
    import netraven.web.routers.admin
    monkeypatch.setattr(netraven.web.routers.admin, "get_scheduler", lambda: mock_scheduler)
    
    # Create schedule for connectivity checks
    schedule_data = {
        "task_type": "connectivity_check",
        "schedule": "*/5 * * * *",  # Every 5 minutes
        "description": "Check device connectivity every 5 minutes"
    }
    
    # Add a scheduled task
    response = client.post(
        "/api/admin/scheduler/tasks",
        json=schedule_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["task_type"] == "connectivity_check"
    assert data["schedule"] == "*/5 * * * *"
    
    # Mock task execution
    with patch("netraven.core.monitoring.check_all_devices") as mock_check:
        mock_check.return_value = {
            "checked": 10,
            "online": 8,
            "offline": 2,
            "results": {
                "device1": {"status": "online", "response_time": 25},
                "device2": {"status": "offline", "response_time": None}
            }
        }
        
        # Get the task
        task_id = data["id"]
        task = mock_scheduler.get_task(task_id)
        
        # Manually run the task (simulating scheduler execution)
        if task and hasattr(task, "func"):
            result = task.func()
            assert result["checked"] == 10
            assert result["online"] == 8


def test_metrics_collection(admin_token, monkeypatch):
    """Test metrics collection and retrieval."""
    # Mock metrics data
    metrics_data = {
        "system": {
            "cpu_usage": 35.5,
            "memory_usage": 42.8,
            "disk_usage": 68.2,
            "uptime": 86400,  # 1 day in seconds
            "timestamp": datetime.now().isoformat()
        },
        "application": {
            "active_users": 12,
            "api_requests": 1568,
            "failed_requests": 23,
            "average_response_time": 0.128,
            "timestamp": datetime.now().isoformat()
        },
        "devices": {
            "total": 87,
            "online": 81,
            "offline": 6,
            "timestamp": datetime.now().isoformat()
        },
        "backups": {
            "total": 356,
            "last_24h": 87,
            "failed": 3,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # Patch the get_metrics function
    with patch("netraven.web.routers.admin.get_metrics") as mock_get_metrics:
        mock_get_metrics.return_value = metrics_data
        
        # Get metrics
        response = client.get(
            "/api/admin/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "system" in data
        assert "application" in data
        assert "devices" in data
        assert "backups" in data
        
        # Check specific metrics
        assert data["system"]["cpu_usage"] == 35.5
        assert data["application"]["active_users"] == 12
        assert data["devices"]["total"] == 87
        assert data["backups"]["total"] == 356


def test_backup_comparison(admin_token, test_dirs, monkeypatch):
    """Test backup comparison functionality."""
    # Create mock backup manager
    backup_dir = test_dirs["backup_dir"]
    backup_manager = MagicMock(spec=BackupManager)
    
    # Create two mock backups
    device_id = str(uuid.uuid4())
    backup1_path = os.path.join(backup_dir, f"{device_id}_backup1.cfg")
    backup2_path = os.path.join(backup_dir, f"{device_id}_backup2.cfg")
    
    # Write config content to files
    with open(backup1_path, "w") as f:
        f.write("hostname Router1\ninterface GigabitEthernet0/1\n ip address 192.168.1.1 255.255.255.0\n no shutdown")
    
    with open(backup2_path, "w") as f:
        f.write("hostname Router1\ninterface GigabitEthernet0/1\n ip address 192.168.1.100 255.255.255.0\n description LAN\n no shutdown")
    
    # Mock backups data
    backup1 = {
        "id": str(uuid.uuid4()),
        "device_id": device_id,
        "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
        "file_path": backup1_path,
        "file_size": os.path.getsize(backup1_path),
        "status": "completed"
    }
    
    backup2 = {
        "id": str(uuid.uuid4()),
        "device_id": device_id,
        "timestamp": datetime.now().isoformat(),
        "file_path": backup2_path,
        "file_size": os.path.getsize(backup2_path),
        "status": "completed"
    }
    
    # Mock the comparison function
    def mock_compare_backups(backup1_id, backup2_id):
        return {
            "files": {
                backup1_path: backup1,
                backup2_path: backup2
            },
            "differences": [
                "-ip address 192.168.1.1 255.255.255.0",
                "+ip address 192.168.1.100 255.255.255.0",
                "+description LAN"
            ],
            "summary": {
                "lines_added": 1,
                "lines_removed": 0,
                "lines_changed": 1,
                "total_changes": 2
            }
        }
    
    # Patch the necessary functions
    import netraven.web.routers.backups
    monkeypatch.setattr(netraven.web.routers.backups, "get_backup", lambda db, backup_id: 
                        backup1 if backup_id == backup1["id"] else backup2)
    monkeypatch.setattr(netraven.web.routers.backups, "compare_backups", mock_compare_backups)
    
    # Compare backups
    response = client.get(
        f"/api/backups/compare?backup1_id={backup1['id']}&backup2_id={backup2['id']}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "differences" in data
    assert "summary" in data
    assert data["summary"]["total_changes"] == 2


def test_device_config_retrieval_and_parsing(admin_token, monkeypatch):
    """Test device configuration retrieval and parsing."""
    # Create mock device
    device_id = str(uuid.uuid4())
    device = {
        "id": device_id,
        "hostname": "test-router",
        "ip_address": "192.168.1.100",
        "device_type": "cisco_ios",
        "status": "active"
    }
    
    # Mock configuration data
    config_data = """
    hostname test-router
    !
    interface GigabitEthernet0/1
     description LAN
     ip address 192.168.1.1 255.255.255.0
     no shutdown
    !
    interface GigabitEthernet0/2
     description WAN
     ip address 10.0.0.1 255.255.255.0
     no shutdown
    !
    ip route 0.0.0.0 0.0.0.0 10.0.0.2
    !
    ntp server 10.0.0.10
    !
    snmp-server community public RO
    snmp-server community private RW
    !
    end
    """
    
    # Mock the parsed configuration structure
    parsed_config = {
        "hostname": "test-router",
        "interfaces": [
            {
                "name": "GigabitEthernet0/1",
                "description": "LAN",
                "ip_address": "192.168.1.1",
                "subnet_mask": "255.255.255.0",
                "shutdown": False
            },
            {
                "name": "GigabitEthernet0/2",
                "description": "WAN",
                "ip_address": "10.0.0.1",
                "subnet_mask": "255.255.255.0",
                "shutdown": False
            }
        ],
        "routes": [
            {
                "destination": "0.0.0.0",
                "mask": "0.0.0.0",
                "next_hop": "10.0.0.2"
            }
        ],
        "ntp": {
            "servers": ["10.0.0.10"]
        },
        "snmp": {
            "communities": [
                {"name": "public", "access": "RO"},
                {"name": "private", "access": "RW"}
            ]
        }
    }
    
    # Patch the necessary functions
    import netraven.web.routers.devices
    monkeypatch.setattr(netraven.web.routers.devices, "get_device_by_id", lambda db, id: device)
    
    with patch("netraven.core.device_comm.DeviceConnector.get_config") as mock_get_config:
        mock_get_config.return_value = config_data
        
        with patch("netraven.core.config_parser.parse_config") as mock_parse_config:
            mock_parse_config.return_value = parsed_config
            
            # Get device configuration
            response = client.get(
                f"/api/devices/{device_id}/config",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "raw_config" in data
            assert "parsed_config" in data
            assert data["raw_config"] == config_data
            assert data["parsed_config"] == parsed_config
            
            # Get specific configuration section
            response = client.get(
                f"/api/devices/{device_id}/config?section=interfaces",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "parsed_config" in data
            assert data["parsed_config"] == parsed_config["interfaces"]


def test_scheduled_tasks_execution_stats(mock_scheduler, admin_token, monkeypatch):
    """Test scheduled tasks execution statistics."""
    # Patch the application to use our mock scheduler
    import netraven.web.routers.admin
    monkeypatch.setattr(netraven.web.routers.admin, "get_scheduler", lambda: mock_scheduler)
    
    # Create some tasks first
    tasks_data = [
        {
            "task_type": "backup",
            "schedule": "0 0 * * *",
            "device_id": str(uuid.uuid4()),
            "description": "Daily backup"
        },
        {
            "task_type": "key_rotation",
            "schedule": "0 0 1 * *",
            "description": "Monthly key rotation"
        },
        {
            "task_type": "connectivity_check",
            "schedule": "*/15 * * * *",
            "description": "Check connectivity every 15 minutes"
        }
    ]
    
    for task_data in tasks_data:
        client.post(
            "/api/admin/scheduler/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    # Mock execution statistics
    execution_stats = {
        "total_executions": 145,
        "successful_executions": 142,
        "failed_executions": 3,
        "task_stats": {
            "backup": {
                "total": 30,
                "successful": 29,
                "failed": 1
            },
            "key_rotation": {
                "total": 5,
                "successful": 5,
                "failed": 0
            },
            "connectivity_check": {
                "total": 110,
                "successful": 108,
                "failed": 2
            }
        },
        "last_failed_tasks": [
            {
                "task_id": "backup-task-123",
                "task_type": "backup",
                "started_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "error": "Connection timeout"
            },
            {
                "task_id": "connectivity-check-456",
                "task_type": "connectivity_check",
                "started_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "error": "Device unreachable"
            }
        ]
    }
    
    # Patch the get_execution_stats function
    with patch("netraven.web.routers.admin.get_execution_stats") as mock_stats:
        mock_stats.return_value = execution_stats
        
        # Get execution statistics
        response = client.get(
            "/api/admin/scheduler/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_executions"] == 145
        assert data["successful_executions"] == 142
        assert data["failed_executions"] == 3
        assert "task_stats" in data
        assert "last_failed_tasks" in data 

# --- New System Workflow Test ---

@pytest.mark.asyncio
async def test_basic_user_workflow(logged_in_client: Tuple[AsyncClient, str]):
    """Tests a simple user flow: login, access resource, logout."""
    client, access_token = logged_in_client # Client already has auth header
    
    # 1. Access a protected resource (e.g., /users/me)
    response_me = await client.get("/api/v1/users/me")
    assert response_me.status_code == 200
    user_info = response_me.json()
    assert "username" in user_info
    # assert user_info["username"] == test_user["username"] # Verify username if test_user fixture provided it
    
    # 2. List devices (should be allowed with default scope)
    response_devices = await client.get("/api/v1/devices")
    assert response_devices.status_code == 200
    assert isinstance(response_devices.json(), list)
    
    # 3. Attempt an admin action (should fail)
    response_admin = await client.get("/api/v1/users/") # List all users requires admin
    assert response_admin.status_code == 403 # Forbidden
    
    # 4. Logout
    response_logout = await client.post("/api/v1/auth/logout")
    assert response_logout.status_code == 200
    assert "Logout successful" in response_logout.json().get("message", "")
    
    # 5. Verify token is now invalid
    response_me_after_logout = await client.get("/api/v1/users/me") # Auth header is still set from fixture
    assert response_me_after_logout.status_code == 401 # Unauthorized
    
    # 6. Verify accessing without token still fails
    client.headers = {} # Remove auth header
    response_me_no_token = await client.get("/api/v1/users/me")
    assert response_me_no_token.status_code == 401

# Add more complex workflow tests as needed
# e.g., create device -> assign tag -> create backup -> view backup -> delete device 