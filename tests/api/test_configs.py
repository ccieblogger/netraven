import pytest
from fastapi.testclient import TestClient
from netraven.api.main import app
from netraven.db import models
from netraven.db.session import SessionLocal
from netraven.api.auth import get_password_hash  # Correct import for password hashing

@pytest.fixture(scope="function")
def auth_token(db_session):
    # Ensure admin user exists in the test DB using the same session as the app
    admin = db_session.query(models.User).filter_by(username="admin").first()
    if not admin:
        hashed_pw = get_password_hash("admin123")
        admin = models.User(
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_pw,
            is_active=True,
            role="admin",
            full_name="Test Admin"
        )
        db_session.add(admin)
        db_session.commit()
    client = TestClient(app)
    data = {"username": "admin", "password": "admin123"}
    response = client.post("/auth/token", data=data)
    assert response.status_code == 200, f"Auth failed: {response.text}"
    return response.json()["access_token"]

@pytest.mark.usefixtures("db_session", "create_test_device")
def test_search_configs_empty(monkeypatch, db_session, auth_token):
    from fastapi.testclient import TestClient
    from netraven.api.main import app
    client = TestClient(app)
    # Patch DB to return empty for FTS
    class DummyResult:
        def fetchall(self):
            return []
    def dummy_execute(*args, **kwargs):
        return DummyResult()
    monkeypatch.setattr("netraven.api.routers.configs.get_db", lambda: None)
    monkeypatch.setattr("sqlalchemy.orm.Session.execute", dummy_execute)
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/configs/search?q=test", headers=headers)
    assert response.status_code == 200
    assert response.json() == []

def test_list_configs_empty(db_session, create_test_device, auth_token):
    from fastapi.testclient import TestClient
    from netraven.api.main import app
    client = TestClient(app)
    # Create a device to get a valid device_id
    device = create_test_device()
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Use query parameter endpoint instead of the conflicting path
    response = client.get(f"/api/configs?device_id={device.id}", headers=headers)
    # Print response for debugging
    print(f"Response: {response.status_code}, {response.text}")
    assert response.status_code == 200
    assert response.json() == []

def test_delete_config_not_found(db_session, auth_token):
    from fastapi.testclient import TestClient
    from netraven.api.main import app
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.delete("/api/configs/99999", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Config snapshot not found"

def test_restore_config_not_found(db_session, auth_token):
    from fastapi.testclient import TestClient
    from netraven.api.main import app
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/api/configs/99999/restore", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Config snapshot not found"

# Integration test for create/list/delete/restore
def test_config_crud_flow(db_session, create_test_device, auth_token):
    from netraven.db.models.device_config import DeviceConfiguration
    from netraven.db.models.device import Device
    from fastapi.testclient import TestClient
    from netraven.api.main import app
    client = TestClient(app)
    # Create device and config
    device = create_test_device()
    config = DeviceConfiguration(device_id=int(device.id), config_data="hostname test", data_hash="abc123", config_metadata={"job_id": 1})
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)
    headers = {"Authorization": f"Bearer {auth_token}"}
    # List configs
    resp = client.get(f"/api/configs?device_id={device.id}", headers=headers)
    assert resp.status_code == 200
    configs = resp.json()
    assert len(configs) == 1
    assert configs[0]["id"] == config.id
    # Restore config
    resp = client.post(f"/api/configs/{config.id}/restore", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["restored_id"] == config.id
    # Delete config
    resp = client.delete(f"/api/configs/{config.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["deleted_id"] == config.id
    # List again (should be empty)
    resp = client.get(f"/api/configs?device_id={device.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []

def test_list_configs_pagination_and_filter(db_session, create_test_device, auth_token):
    from netraven.db.models.device_config import DeviceConfiguration
    from netraven.db.models.device import Device
    from fastapi.testclient import TestClient
    from netraven.api.main import app
    client = TestClient(app)
    # Create two devices
    device1 = create_test_device()
    # Only use valid fields for Device
    device2 = Device(hostname="dev2", ip_address="10.0.0.2", device_type="cisco_ios")
    db_session.add(device2)
    db_session.commit()
    db_session.refresh(device2)
    # Add 60 configs for device1, 10 for device2
    for i in range(60):
        db_session.add(DeviceConfiguration(device_id=int(device1.id), config_data=f"conf {i}", data_hash=f"h{i}", config_metadata={"job_id": 1}))
    for i in range(10):
        db_session.add(DeviceConfiguration(device_id=int(device2.id), config_data=f"dev2 conf {i}", data_hash=f"d2h{i}", config_metadata={"job_id": 2}))
    db_session.commit()
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Test pagination: first page (default limit=50)
    resp = client.get(f"/api/configs?device_id={device1.id}", headers=headers)
    assert resp.status_code == 200
    configs = resp.json()
    assert len(configs) == 50
    # Second page
    resp = client.get(f"/api/configs?device_id={device1.id}&start=50&limit=50", headers=headers)
    assert resp.status_code == 200
    configs = resp.json()
    assert len(configs) == 10
    # Device filter: only device2
    resp = client.get(f"/api/configs?device_id={device2.id}", headers=headers)
    assert resp.status_code == 200
    configs = resp.json()
    assert len(configs) == 10
    for c in configs:
        assert c["device_id"] == device2.id
