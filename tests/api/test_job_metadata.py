import pytest
from fastapi.testclient import TestClient
from netraven.api.main import app

@pytest.mark.usefixtures("db_session", "admin_headers")
def test_job_metadata_includes_schedule_schema(admin_headers):
    client = TestClient(app)
    # Use a known job_type, e.g., 'reachability' (should exist in registry)
    response = client.get("/jobs/metadata/reachability", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "schedule_schema" in data
    schedule_schema = data["schedule_schema"]
    assert schedule_schema["type"] == "object"
    assert "properties" in schedule_schema
    # Check for expected scheduling fields
    for field in ["schedule_type", "interval_seconds", "cron_string", "scheduled_for"]:
        assert field in schedule_schema["properties"]
    # schedule_type should have enum
    assert "enum" in schedule_schema["properties"]["schedule_type"]
