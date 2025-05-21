import io
import json
import pytest
from fastapi.testclient import TestClient
from netraven.api.main import app
from netraven.db import models

@pytest.fixture
def admin_headers():
    # This should be replaced with a real fixture or helper for your auth system
    return {"Authorization": "Bearer test-admin-token"}

@pytest.fixture
def db_session():
    # This should be replaced with your real DB session fixture
    from netraven.db.session import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client():
    return TestClient(app)

def ensure_default_tag(db_session):
    default_tag = db_session.query(models.Tag).filter(models.Tag.name == "default").first()
    if not default_tag:
        default_tag = models.Tag(name="default", type="device")
        db_session.add(default_tag)
        db_session.commit()
        db_session.refresh(default_tag)
    return default_tag

def test_bulk_import_enforces_default_tag(client, db_session, admin_headers):
    default_tag = ensure_default_tag(db_session)
    # Prepare a CSV with no tags column
    csv_content = """hostname,ip_address,device_type,port,description\ntest-bulk-1,10.10.10.1,cisco_ios,22,Bulk import test\n"""
    files = {"file": ("devices.csv", csv_content, "text/csv")}
    response = client.post("/devices/bulk_import", files=files, headers=admin_headers)
    assert response.status_code == 201
    # Now fetch the device and check tags
    device = db_session.query(models.Device).filter(models.Device.hostname == "test-bulk-1").first()
    assert device is not None
    tag_names = [t.name for t in device.tags]
    assert "default" in tag_names

    # Now test with JSON with explicit tags (should still get default)
    json_content = json.dumps([
        {
            "hostname": "test-bulk-2",
            "ip_address": "10.10.10.2",
            "device_type": "cisco_ios",
            "tags": []
        }
    ])
    files = {"file": ("devices.json", json_content, "application/json")}
    response = client.post("/devices/bulk_import", files=files, headers=admin_headers)
    assert response.status_code == 201
    device = db_session.query(models.Device).filter(models.Device.hostname == "test-bulk-2").first()
    assert device is not None
    tag_names = [t.name for t in device.tags]
    assert "default" in tag_names

    # Test with tags present (should always include default)
    tag = models.Tag(name="extra-tag", type="device")
    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)
    json_content = json.dumps([
        {
            "hostname": "test-bulk-3",
            "ip_address": "10.10.10.3",
            "device_type": "cisco_ios",
            "tags": [tag.id]
        }
    ])
    files = {"file": ("devices.json", json_content, "application/json")}
    response = client.post("/devices/bulk_import", files=files, headers=admin_headers)
    assert response.status_code == 201
    device = db_session.query(models.Device).filter(models.Device.hostname == "test-bulk-3").first()
    assert device is not None
    tag_names = [t.name for t in device.tags]
    assert "default" in tag_names
    assert "extra-tag" in tag_names
