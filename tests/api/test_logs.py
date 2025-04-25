import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from datetime import datetime, timedelta

from netraven.api.main import app
from netraven.db import models
from tests.api.base import BaseAPITest

class TestLogsAPI(BaseAPITest):
    """Test suite for the Unified Logs API endpoints."""

    @pytest.fixture
    def create_test_logs(self, db_session: Session):
        """Fixture to create test log entries."""
        def _create_logs(count=5, job_id=None, device_id=None, base_timestamp=None, log_type="job", level=None, source="test_source"):
            if base_timestamp is None:
                base_timestamp = datetime.now()
            logs = []
            for i in range(count):
                log = models.Log(
                    timestamp=base_timestamp - timedelta(minutes=i),
                    log_type=log_type,
                    level=level or ("INFO" if i % 2 == 0 else "ERROR"),
                    source=source,
                    message=f"Test log message {i}",
                    job_id=job_id,
                    device_id=device_id
                )
                db_session.add(log)
                logs.append(log)
            db_session.commit()
            for log in logs:
                db_session.refresh(log)
            return logs
        return _create_logs

    def test_get_logs(self, client: TestClient, admin_headers: Dict, create_test_logs):
        """Test getting log entries."""
        logs = create_test_logs(count=5)
        response = client.get("/logs/", headers=admin_headers)
        self.assert_pagination_response(response)
        data = response.json()
        assert len(data["items"]) >= 5
        log_item = data["items"][0]
        assert "id" in log_item
        assert "timestamp" in log_item
        assert "level" in log_item
        assert "message" in log_item
        assert "source" in log_item
        assert "log_type" in log_item

    def test_get_logs_pagination(self, client: TestClient, admin_headers: Dict, create_test_logs):
        logs = create_test_logs(count=10)
        response = client.get("/logs/?page=1&size=3", headers=admin_headers)
        self.assert_pagination_response(response)
        assert len(response.json()["items"]) == 3
        assert response.json()["page"] == 1
        response = client.get("/logs/?page=2&size=3", headers=admin_headers)
        self.assert_pagination_response(response)
        assert len(response.json()["items"]) == 3
        assert response.json()["page"] == 2

    def test_get_logs_by_level(self, client: TestClient, admin_headers: Dict, create_test_logs):
        logs = create_test_logs(count=6)
        response = client.get("/logs/?level=INFO", headers=admin_headers)
        self.assert_pagination_response(response)
        for log in response.json()["items"]:
            assert log["level"] == "INFO"
        response = client.get("/logs/?level=ERROR", headers=admin_headers)
        self.assert_pagination_response(response)
        for log in response.json()["items"]:
            assert log["level"] == "ERROR"

    def test_get_logs_by_job(self, client: TestClient, admin_headers: Dict, create_test_logs):
        logs = create_test_logs(count=3, job_id=123)
        other_logs = create_test_logs(count=3)
        response = client.get(f"/logs/?job_id=123", headers=admin_headers)
        self.assert_pagination_response(response)
        data = response.json()
        assert all(log["job_id"] == 123 for log in data["items"])

    def test_get_logs_by_device(self, client: TestClient, admin_headers: Dict, create_test_logs):
        logs = create_test_logs(count=4, device_id=456)
        other_logs = create_test_logs(count=2)
        response = client.get(f"/logs/?device_id=456", headers=admin_headers)
        self.assert_pagination_response(response)
        data = response.json()
        assert all(log["device_id"] == 456 for log in data["items"])

    def test_get_logs_by_source(self, client: TestClient, admin_headers: Dict, create_test_logs):
        specific_source = "specific_test_source"
        specific_logs = create_test_logs(count=3, source=specific_source)
        other_logs = create_test_logs(count=3)
        response = client.get(f"/logs/?source={specific_source}", headers=admin_headers)
        self.assert_pagination_response(response)
        for log in response.json()["items"]:
            assert log["source"] == specific_source

    def test_get_logs_date_range(self, client: TestClient, admin_headers: Dict, create_test_logs):
        base_time = datetime.now()
        day_ago_logs = create_test_logs(count=2, base_timestamp=base_time - timedelta(days=1))
        week_ago_logs = create_test_logs(count=2, base_timestamp=base_time - timedelta(days=7))
        month_ago_logs = create_test_logs(count=2, base_timestamp=base_time - timedelta(days=30))
        start_time = (base_time - timedelta(days=10)).isoformat()
        end_time = (base_time - timedelta(hours=12)).isoformat()
        response = client.get(f"/logs/?start_time={start_time}&end_time={end_time}", headers=admin_headers)
        self.assert_pagination_response(response)
        for log in response.json()["items"]:
            log_time = datetime.fromisoformat(log["timestamp"])
            assert (base_time - timedelta(days=10)) <= log_time <= (base_time - timedelta(hours=12))

    def test_get_single_log(self, client: TestClient, admin_headers: Dict, create_test_logs):
        logs = create_test_logs(count=1)
        log_id = logs[0].id
        response = client.get(f"/logs/{log_id}", headers=admin_headers)
        assert response.status_code == 200
        log = response.json()
        assert log["id"] == log_id

    def test_get_log_types(self, client: TestClient, admin_headers: Dict):
        response = client.get("/logs/types", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert any("job" in t["log_type"] for t in data)

    def test_get_log_levels(self, client: TestClient, admin_headers: Dict):
        response = client.get("/logs/levels", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert any("info" in t["level"].lower() for t in data)

    def test_get_log_stats(self, client: TestClient, admin_headers: Dict, create_test_logs):
        create_test_logs(count=5)
        response = client.get("/logs/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_type" in data
        assert "by_level" in data
        assert "last_log_time" in data 