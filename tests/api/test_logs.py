import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from datetime import datetime, timedelta

from netraven.api.main import app
from netraven.db import models
from tests.api.base import BaseAPITest

class TestLogsAPI(BaseAPITest):
    """Test suite for the Logs API endpoints."""

    @pytest.fixture
    def create_test_logs(self, db_session: Session):
        """Fixture to create test log entries."""
        def _create_logs(count=5, job_id=None, device_id=None, base_timestamp=None):
            if base_timestamp is None:
                base_timestamp = datetime.now()
            
            logs = []
            for i in range(count):
                log = models.LogEntry(
                    timestamp=base_timestamp - timedelta(minutes=i),
                    level="INFO" if i % 2 == 0 else "ERROR",
                    source="test_source",
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

    @pytest.fixture
    def test_job(self, db_session: Session):
        """Create a test job for log association."""
        job = models.Job(
            name="log-test-job",
            command="show version",
            device_filter_type="tag",
            device_filter_value="test",
            schedule_type="onetime",
            is_enabled=True,
            status="complete"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        return job

    @pytest.fixture
    def test_device(self, db_session: Session):
        """Create a test device for log association."""
        device = models.Device(
            hostname="log-test-device",
            ip_address="192.168.100.100",
            device_type="cisco_ios"
        )
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        return device

    def test_get_logs(self, client: TestClient, admin_headers: Dict, create_test_logs):
        """Test getting log entries."""
        # Create test logs
        logs = create_test_logs(count=5)
        
        response = client.get("/logs/", headers=admin_headers)
        self.assert_pagination_response(response)
        
        data = response.json()
        assert len(data["items"]) >= 5  # At least our test logs
        
        # Verify log format
        log_item = data["items"][0]
        assert "id" in log_item
        assert "timestamp" in log_item
        assert "level" in log_item
        assert "message" in log_item
        assert "source" in log_item

    def test_get_logs_pagination(self, client: TestClient, admin_headers: Dict, create_test_logs):
        """Test logs pagination."""
        # Create more logs to test pagination
        logs = create_test_logs(count=10)
        
        # Test first page with size 3
        response = client.get("/logs/?page=1&size=3", headers=admin_headers)
        self.assert_pagination_response(response)
        assert len(response.json()["items"]) == 3
        assert response.json()["page"] == 1
        
        # Test second page
        response = client.get("/logs/?page=2&size=3", headers=admin_headers)
        self.assert_pagination_response(response)
        assert len(response.json()["items"]) == 3
        assert response.json()["page"] == 2

    def test_get_logs_by_level(self, client: TestClient, admin_headers: Dict, create_test_logs):
        """Test filtering logs by level."""
        # Create logs with mixed levels
        logs = create_test_logs(count=6)  # 3 INFO, 3 ERROR based on fixture
        
        # Filter by INFO level
        response = client.get("/logs/?level=INFO", headers=admin_headers)
        self.assert_pagination_response(response)
        
        # All returned logs should be INFO level
        for log in response.json()["items"]:
            assert log["level"] == "INFO"
        
        # Filter by ERROR level
        response = client.get("/logs/?level=ERROR", headers=admin_headers)
        self.assert_pagination_response(response)
        
        # All returned logs should be ERROR level
        for log in response.json()["items"]:
            assert log["level"] == "ERROR"

    def test_get_logs_by_job(self, client: TestClient, admin_headers: Dict, create_test_logs, test_job):
        """Test getting logs for a specific job."""
        # Create logs associated with job
        job_logs = create_test_logs(count=3, job_id=test_job.id)
        # Create some other logs not associated with job
        other_logs = create_test_logs(count=3)
        
        response = client.get(f"/logs/job/{test_job.id}", headers=admin_headers)
        self.assert_pagination_response(response)
        
        # Verify only logs for the job are returned
        data = response.json()
        assert len(data["items"]) == 3
        for log in data["items"]:
            assert log["job_id"] == test_job.id

    def test_get_logs_by_device(self, client: TestClient, admin_headers: Dict, create_test_logs, test_device):
        """Test getting logs for a specific device."""
        # Create logs associated with device
        device_logs = create_test_logs(count=4, device_id=test_device.id)
        # Create some other logs not associated with device
        other_logs = create_test_logs(count=2)
        
        response = client.get(f"/logs/device/{test_device.id}", headers=admin_headers)
        self.assert_pagination_response(response)
        
        # Verify only logs for the device are returned
        data = response.json()
        assert len(data["items"]) == 4
        for log in data["items"]:
            assert log["device_id"] == test_device.id

    def test_get_logs_by_source(self, client: TestClient, admin_headers: Dict, create_test_logs):
        """Test filtering logs by source."""
        # Create logs with a specific source
        specific_source = "specific_test_source"
        specific_logs = create_test_logs(count=3)
        
        # Update the source for these logs
        for log in specific_logs:
            log.source = specific_source
        db_session = next(iter([param for param in create_test_logs.__closure__ if param.cell_contents.__class__.__name__ == 'Session']))
        db_session.cell_contents.commit()
        
        # Create other logs with default source
        other_logs = create_test_logs(count=3)
        
        # Filter by specific source
        response = client.get(f"/logs/?source={specific_source}", headers=admin_headers)
        self.assert_pagination_response(response)
        
        # Verify only logs with the specific source are returned
        for log in response.json()["items"]:
            assert log["source"] == specific_source

    def test_get_logs_date_range(self, client: TestClient, admin_headers: Dict, create_test_logs):
        """Test filtering logs by date range."""
        base_time = datetime.now()
        
        # Create logs with specific timestamps spanning a week
        day_ago_logs = create_test_logs(count=2, base_timestamp=base_time - timedelta(days=1))
        week_ago_logs = create_test_logs(count=2, base_timestamp=base_time - timedelta(days=7))
        month_ago_logs = create_test_logs(count=2, base_timestamp=base_time - timedelta(days=30))
        
        # Calculate date range for query
        start_date = (base_time - timedelta(days=10)).strftime("%Y-%m-%d")
        end_date = (base_time - timedelta(hours=12)).strftime("%Y-%m-%d")
        
        # Query logs within the date range (should include day_ago but not month_ago logs)
        response = client.get(f"/logs/?start_date={start_date}&end_date={end_date}", headers=admin_headers)
        self.assert_pagination_response(response)
        
        # Verify returned logs are within date range
        data = response.json()
        for log in data["items"]:
            log_date = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
            # Convert to date only for comparison with date-only filter
            log_date_only = log_date.date()
            assert log_date_only >= datetime.fromisoformat(start_date).date()
            assert log_date_only <= datetime.fromisoformat(end_date).date()

    def test_get_logs_with_message_filter(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test filtering logs by message content."""
        # Create logs with specific message patterns
        log1 = models.LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            source="test_source",
            message="Connection established with device A"
        )
        log2 = models.LogEntry(
            timestamp=datetime.now(),
            level="ERROR",
            source="test_source",
            message="Connection failed with device B"
        )
        log3 = models.LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            source="test_source",
            message="Configuration backup completed"
        )
        db_session.add_all([log1, log2, log3])
        db_session.commit()
        
        # Filter by "Connection" in message
        response = client.get("/logs/?message=Connection", headers=admin_headers)
        self.assert_pagination_response(response)
        
        # Verify only logs with "Connection" in message are returned
        data = response.json()
        filtered_logs = [log for log in data["items"] if "Connection" in log["message"]]
        assert len(filtered_logs) >= 2  # At least our test logs 