import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime, timedelta

from netraven.api.main import app
from netraven.db import models
from tests.api.base import BaseAPITest

class TestJobLogsAPI(BaseAPITest):
    """Test suite for the Job Log API endpoints."""

    @pytest.fixture
    def test_device(self, db_session: Session):
        device = models.Device(
            hostname="test-device-1",
            ip_address="10.0.0.1",
            device_type="cisco_ios"
        )
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        return device

    @pytest.fixture
    def test_job(self, db_session: Session):
        job = models.Job(
            name="test-job-1",
            job_type="backup",
            schedule_type="onetime",
            is_enabled=True,
            status="pending"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        return job

    @pytest.fixture
    def test_job2(self, db_session: Session):
        job = models.Job(
            name="test-job-2",
            job_type="reachability",
            schedule_type="onetime",
            is_enabled=True,
            status="pending"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        return job

    @pytest.fixture
    def test_device2(self, db_session: Session):
        device = models.Device(
            hostname="test-device-2",
            ip_address="10.0.0.2",
            device_type="arista_eos"
        )
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        return device

    @pytest.fixture
    def create_job_logs(self, db_session: Session, test_job, test_device, test_job2, test_device2):
        def _create():
            logs = []
            # Logs for job 1, device 1
            for i in range(2):
                log = models.JobLog(
                    job_id=test_job.id,
                    device_id=test_device.id,
                    message=f"Backup log {i}",
                    level="INFO",
                    timestamp=datetime.now() - timedelta(minutes=i)
                )
                db_session.add(log)
                logs.append(log)
            # Logs for job 2, device 2
            for i in range(2):
                log = models.JobLog(
                    job_id=test_job2.id,
                    device_id=test_device2.id,
                    message=f"Reachability log {i}",
                    level="ERROR" if i == 1 else "INFO",
                    timestamp=datetime.now() - timedelta(minutes=10+i)
                )
                db_session.add(log)
                logs.append(log)
            db_session.commit()
            for log in logs:
                db_session.refresh(log)
            return logs
        return _create

    def test_job_logs_filter_by_job_name(self, client: TestClient, admin_headers: Dict, create_job_logs):
        create_job_logs()
        response = client.get("/job-logs/?job_name=test-job-1", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(item["job_name"] == "test-job-1" for item in data["items"])

    def test_job_logs_filter_by_device_names(self, client: TestClient, admin_headers: Dict, create_job_logs):
        create_job_logs()
        response = client.get("/job-logs/?device_names=test-device-2", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(item["device_name"] == "test-device-2" for item in data["items"])

    def test_job_logs_filter_by_job_type(self, client: TestClient, admin_headers: Dict, create_job_logs):
        create_job_logs()
        response = client.get("/job-logs/?job_type=backup", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(item["job_type"] == "backup" for item in data["items"])

    def test_job_logs_keyword_search(self, client: TestClient, admin_headers: Dict, create_job_logs):
        create_job_logs()
        response = client.get("/job-logs/?search=Reachability", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert all("Reachability" in item["message"] or "Reachability" in (item["job_name"] or "") for item in data["items"])

    def test_job_logs_response_enrichment(self, client: TestClient, admin_headers: Dict, create_job_logs):
        create_job_logs()
        response = client.get("/job-logs/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert "job_name" in item
            assert "device_name" in item
            assert "job_type" in item

    def test_job_logs_job_names_endpoint(self, client: TestClient, admin_headers: Dict, create_job_logs):
        create_job_logs()
        response = client.get("/job-logs/job-names", headers=admin_headers)
        assert response.status_code == 200
        names = response.json()
        assert "test-job-1" in names
        assert "test-job-2" in names 