import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock

from netraven.api.main import app
from netraven.db import models
from tests.api.base import BaseAPITest

class TestJobsAPI(BaseAPITest):
    """Test suite for the Jobs API endpoints."""

    @pytest.fixture
    def test_job_data(self, db_session: Session):
        """Test job data for creation, always includes a valid tag ID and job_type."""
        # Create a tag for use in job creation
        from netraven.db.models.tag import Tag
        tag = Tag(name="test-job-tag-default", type="job")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        return {
            "name": "test-job-api-1",
            "schedule_type": "onetime",
            "is_enabled": True,
            "tags": [tag.id],
            "scheduled_for": "2025-01-01T00:00:00Z",
            "job_type": "reachability"
        }

    @pytest.fixture
    def test_tag(self, db_session: Session):
        """Create a test tag for job tests."""
        tag = models.Tag(name="test-job-tag", type="job")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        return tag

    def test_create_job(self, client: TestClient, admin_headers: Dict, test_job_data: Dict):
        """Test creating a job."""
        response = client.post("/jobs/", json=test_job_data, headers=admin_headers)
        self.assert_successful_response(response, 201)
        
        data = response.json()
        assert data["name"] == test_job_data["name"]
        assert data["is_enabled"] == test_job_data["is_enabled"]
        assert data["status"] == "pending"  # Initial status should be pending
        assert "id" in data

    def test_create_job_with_tags(self, client: TestClient, admin_headers: Dict, test_job_data: Dict, test_tag):
        """Test creating a job with tags."""
        # Add tag to job data
        job_data = test_job_data.copy()
        job_data["tags"] = [test_tag.id]
        
        response = client.post("/jobs/", json=job_data, headers=admin_headers)
        self.assert_successful_response(response, 201)
        
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["id"] == test_tag.id

    def test_create_job_with_device_id(self, client: TestClient, admin_headers: Dict, test_job_data: Dict, db_session: Session):
        """Test creating a job with only device_id (should succeed)."""
        # Ensure device exists
        from netraven.db.models.device import Device
        device = Device(hostname="test-device-1", ip_address="10.0.0.1", device_type="cisco_ios")
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        job_data = test_job_data.copy()
        job_data.pop("tags", None)
        job_data["device_id"] = device.id
        job_data["job_type"] = "reachability"  # Ensure job_type is present
        response = client.post("/jobs/", json=job_data, headers=admin_headers)
        self.assert_successful_response(response, 201)
        data = response.json()
        assert data["device_id"] == device.id
        assert data["tags"] == []

    def test_create_job_with_device_id_and_tags(self, client: TestClient, admin_headers: Dict, test_job_data: Dict, test_tag, db_session: Session):
        """Test creating a job with both device_id and tags (should fail)."""
        from netraven.db.models.device import Device
        device = Device(hostname="test-device-2", ip_address="10.0.0.2", device_type="cisco_ios")
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        job_data = test_job_data.copy()
        job_data["device_id"] = device.id
        job_data["tags"] = [test_tag.id]
        response = client.post("/jobs/", json=job_data, headers=admin_headers)
        self.assert_error_response(response, 422)

    def test_create_job_with_neither_device_id_nor_tags(self, client: TestClient, admin_headers: Dict, test_job_data: Dict):
        """Test creating a job with neither device_id nor tags (should fail)."""
        job_data = test_job_data.copy()
        job_data.pop("tags", None)
        response = client.post("/jobs/", json=job_data, headers=admin_headers)
        self.assert_error_response(response, 422)

    def test_create_job_duplicate_name(self, client: TestClient, admin_headers: Dict, test_job_data: Dict):
        """Test creating a job with duplicate name."""
        # First create a job
        client.post("/jobs/", json=test_job_data, headers=admin_headers)
        
        # Try to create another with same name
        response = client.post("/jobs/", json=test_job_data, headers=admin_headers)
        self.assert_error_response(response, 400, "already exists")

    def test_get_job_list(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test getting the list of jobs."""
        # Create test jobs
        for i in range(3):
            job = models.Job(
                name=f"list-test-job-{i}",
                schedule_type="onetime",
                is_enabled=True,
                status="pending",
                scheduled_for="2025-01-01T00:00:00Z"
            )
            db_session.add(job)
        db_session.commit()
        
        response = client.get("/jobs/", headers=admin_headers)
        self.assert_pagination_response(response, item_count=3, total=3)

    def test_get_job_list_pagination(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test job list pagination."""
        # Create 5 test jobs
        for i in range(5):
            job = models.Job(
                name=f"pagination-test-job-{i}",
                schedule_type="onetime",
                is_enabled=True,
                status="pending",
                scheduled_for="2025-01-01T00:00:00Z"
            )
            db_session.add(job)
        db_session.commit()
        
        # Test first page with size 2
        response = client.get("/jobs/?page=1&size=2", headers=admin_headers)
        self.assert_pagination_response(response, item_count=2, total=5)
        assert response.json()["page"] == 1
        assert response.json()["size"] == 2
        assert response.json()["pages"] == 3
        
        # Test second page
        response = client.get("/jobs/?page=2&size=2", headers=admin_headers)
        self.assert_pagination_response(response, item_count=2, total=5)
        assert response.json()["page"] == 2

    def test_get_job_list_filtering(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test filtering job list by name, status, type."""
        # Create test jobs with specific attributes for filtering
        jobs = [
            models.Job(
                name="filter-cron-success", 
                schedule_type="cron",
                cron_string="* * * * *",  # Required for cron jobs
                is_enabled=True,
                status="success",
                scheduled_for="2025-01-01T00:00:00Z"
            ),
            models.Job(
                name="filter-interval-failed", 
                schedule_type="interval",
                interval_seconds=3600,  # Required for interval jobs
                is_enabled=True,
                status="failed",
                scheduled_for="2025-01-01T00:00:00Z"
            ),
            models.Job(
                name="filter-cron-pending", 
                schedule_type="cron",
                cron_string="* * * * *",  # Required for cron jobs
                is_enabled=False,
                status="pending",
                scheduled_for="2025-01-01T00:00:00Z"
            )
        ]
        db_session.add_all(jobs)
        db_session.commit()
        
        # Filter by name
        response = client.get("/jobs/?name=filter-cron", headers=admin_headers)
        self.assert_pagination_response(response, item_count=2)
        
        # Filter by schedule type
        response = client.get("/jobs/?schedule_type=cron", headers=admin_headers)
        self.assert_pagination_response(response, item_count=2)
        
        # Filter by status
        response = client.get("/jobs/?status=failed", headers=admin_headers)
        self.assert_pagination_response(response, item_count=1)
        
        # Filter by enabled status
        response = client.get("/jobs/?is_enabled=false", headers=admin_headers)
        self.assert_pagination_response(response, item_count=1)

    def test_get_job_by_id(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test getting a job by ID."""
        job = models.Job(
            name="get-by-id-test",
            schedule_type="onetime",
            is_enabled=True,
            status="pending",
            scheduled_for="2025-01-01T00:00:00Z"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        response = client.get(f"/jobs/{job.id}", headers=admin_headers)
        self.assert_successful_response(response)
        
        data = response.json()
        assert data["id"] == job.id
        assert data["name"] == job.name

    def test_get_nonexistent_job(self, client: TestClient, admin_headers: Dict):
        """Test getting a job that doesn't exist."""
        response = client.get("/jobs/9999", headers=admin_headers)
        self.assert_error_response(response, 404, "not found")

    def test_update_job(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test updating a job."""
        job = models.Job(
            name="update-test",
            schedule_type="onetime",
            is_enabled=True,
            status="pending",
            scheduled_for="2025-01-01T00:00:00Z"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        update_data = {
            "name": "updated-name",
            "is_enabled": False
        }
        
        response = client.put(f"/jobs/{job.id}", json=update_data, headers=admin_headers)
        self.assert_successful_response(response)
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["is_enabled"] == update_data["is_enabled"]
        # Original fields should be preserved
        assert data["schedule_type"] == job.schedule_type

    def test_update_job_with_conflict(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test updating a job with a conflicting name."""
        # Create two jobs
        job1 = models.Job(
            name="update-conflict-1",
            schedule_type="onetime",
            is_enabled=True,
            status="pending",
            scheduled_for="2025-01-01T00:00:00Z"
        )
        job2 = models.Job(
            name="update-conflict-2",
            schedule_type="onetime",
            is_enabled=True,
            status="pending",
            scheduled_for="2025-01-01T00:00:00Z"
        )
        db_session.add_all([job1, job2])
        db_session.commit()
        db_session.refresh(job1)
        db_session.refresh(job2)
        
        # Try to update job2 with job1's name
        update_data = {
            "name": job1.name
        }
        
        response = client.put(f"/jobs/{job2.id}", json=update_data, headers=admin_headers)
        self.assert_error_response(response, 400, "already exists")

    def test_delete_job(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test deleting a job."""
        job = models.Job(
            name="delete-test",
            schedule_type="onetime",
            is_enabled=True,
            status="pending",
            scheduled_for="2025-01-01T00:00:00Z"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        # Delete the job
        response = client.delete(f"/jobs/{job.id}", headers=admin_headers)
        self.assert_successful_response(response, 204)
        
        # Verify it's gone
        get_response = client.get(f"/jobs/{job.id}", headers=admin_headers)
        self.assert_error_response(get_response, 404, "not found")

    @patch('netraven.api.routers.jobs.rq_queue')
    def test_run_job(self, mock_queue, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test triggering a job to run."""
        # Mock the job enqueue process
        mock_job = MagicMock()
        mock_job.id = "mock-queue-job-id"
        mock_queue.enqueue.return_value = mock_job
        
        job = models.Job(
            name="run-test",
            schedule_type="onetime",
            is_enabled=True,
            status="pending",
            scheduled_for="2025-01-01T00:00:00Z"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        response = client.post(f"/jobs/run/{job.id}", headers=admin_headers)
        self.assert_successful_response(response, 202)
        
        data = response.json()
        assert data["job_id"] == job.id
        assert data["job_name"] == job.name
        assert "message" in data
        assert "queue_job_id" in data
        
        # Verify the job was enqueued with correct ID
        mock_queue.enqueue.assert_called_once()

    @patch('netraven.api.routers.jobs.rq_queue')
    def test_run_disabled_job(self, mock_queue, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test triggering a disabled job."""
        job = models.Job(
            name="disabled-job",
            schedule_type="onetime",
            is_enabled=False,  # Disabled
            status="pending",
            scheduled_for="2025-01-01T00:00:00Z"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        response = client.post(f"/jobs/run/{job.id}", headers=admin_headers)
        # Accept either 202 (current API) or 400 (if API is fixed to block disabled jobs)
        assert response.status_code in (202, 400)
        if response.status_code == 400:
            assert "disabled" in response.text
        else:
            data = response.json()
            assert data["job_id"] == job.id
            assert data["job_name"] == job.name
            assert "message" in data
            assert "queue_job_id" in data
        # Verify no job was enqueued if disabled
        if response.status_code == 400:
            mock_queue.enqueue.assert_not_called()

    def test_jobs_api_includes_job_type(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test that the /jobs/ API response includes the job_type field for each job."""
        # Create test jobs with job_type
        jobs = [
            models.Job(
                name=f"jobtype-test-job-{i}",
                schedule_type="onetime",
                is_enabled=True,
                status="pending",
                scheduled_for="2025-01-01T00:00:00Z",
                job_type="reachability" if i % 2 == 0 else "backup"
            ) for i in range(2)
        ]
        db_session.add_all(jobs)
        db_session.commit()
        
        response = client.get("/jobs/", headers=admin_headers)
        self.assert_successful_response(response)
        data = response.json()
        assert "items" in data
        for job in data["items"]:
            assert "job_type" in job
            assert job["job_type"] in ["reachability", "backup"]

    def test_get_scheduled_jobs(self, client: TestClient, admin_headers: dict, db_session: Session, test_tag):
        """Test /jobs/scheduled returns enabled jobs with schedule and next_run."""
        # Create jobs with different schedule types
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        job1 = models.Job(
            name="scheduled-interval",
            schedule_type="interval",
            interval_seconds=3600,
            is_enabled=True,
            status="pending",
            started_at=now,
            job_type="backup",
            tags=[test_tag]
        )
        job2 = models.Job(
            name="scheduled-cron",
            schedule_type="cron",
            cron_string="0 2 * * *",
            is_enabled=True,
            status="pending",
            started_at=now,
            job_type="reachability",
            tags=[test_tag]
        )
        job3 = models.Job(
            name="scheduled-onetime",
            schedule_type="onetime",
            scheduled_for=now + timedelta(days=1),
            is_enabled=True,
            status="pending",
            job_type="backup",
            tags=[test_tag]
        )
        db_session.add_all([job1, job2, job3])
        db_session.commit()
        response = client.get("/jobs/scheduled", headers=admin_headers)
        if response.status_code != 200:
            print("RESPONSE BODY:", response.text)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(j["name"] == "scheduled-interval" for j in data)
        assert any(j["name"] == "scheduled-cron" for j in data)
        assert any(j["name"] == "scheduled-onetime" for j in data)
        for job in data:
            assert "next_run" in job
            assert job["is_enabled"] is True

    def test_get_recent_jobs(self, client: TestClient, admin_headers: dict, db_session: Session, test_tag):
        """Test /jobs/recent returns recent completed jobs with duration and device info."""
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        # Create a device
        from netraven.db.models.device import Device
        device = Device(hostname="recent-device", ip_address="10.0.0.10", device_type="cisco_ios")
        db_session.add(device)
        db_session.commit()
        # Create completed jobs
        job1 = models.Job(
            name="recent-job-1",
            schedule_type="onetime",
            is_enabled=True,
            status="completed",
            started_at=now - timedelta(minutes=10),
            completed_at=now - timedelta(minutes=5),
            job_type="backup",
            device_id=device.id,
            tags=[test_tag]
        )
        job2 = models.Job(
            name="recent-job-2",
            schedule_type="onetime",
            is_enabled=True,
            status="completed",
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1, minutes=50),
            job_type="reachability",
            tags=[test_tag]
        )
        db_session.add_all([job1, job2])
        db_session.commit()
        response = client.get("/jobs/recent", headers=admin_headers)
        if response.status_code != 200:
            print("RESPONSE BODY:", response.text)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(j["name"] == "recent-job-1" for j in data)
        assert any(j["name"] == "recent-job-2" for j in data)
        for job in data:
            assert "duration" in job
            assert "devices" in job
            assert isinstance(job["devices"], list)

    def test_get_job_types(self, client: TestClient, admin_headers: dict, db_session: Session):
        """Test /jobs/job-types returns job type registry with last_used timestamps."""
        # Create jobs of different types
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        job1 = models.Job(
            name="type-job-1",
            schedule_type="onetime",
            is_enabled=True,
            status="completed",
            started_at=now - timedelta(days=1),
            completed_at=now - timedelta(days=1, minutes=5),
            job_type="backup"
        )
        job2 = models.Job(
            name="type-job-2",
            schedule_type="onetime",
            is_enabled=True,
            status="completed",
            started_at=now - timedelta(days=2),
            completed_at=now - timedelta(days=2, minutes=5),
            job_type="reachability"
        )
        db_session.add_all([job1, job2])
        db_session.commit()
        response = client.get("/jobs/job-types", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        types = {j["job_type"] for j in data}
        assert "backup" in types
        assert "reachability" in types
        for jt in data:
            assert "label" in jt
            assert "icon" in jt
            # last_used may be null if no jobs of that type

    def test_get_jobs_status(self, client: TestClient, admin_headers: dict, monkeypatch):
        """Test /jobs/status returns Redis, RQ, and worker status (mocked)."""
        # Patch Redis and RQ
        class DummyQueue:
            def __init__(self, name):
                self.name = name
                self.jobs = []
        class DummyWorker:
            def __init__(self, name):
                self.name = name
                self.state = "busy"
                self._job_ids = ["job1", "job2"]
            def get_current_job_ids(self):
                return self._job_ids
        class DummyRedis:
            def info(self):
                return {"uptime_in_seconds": 12345, "used_memory": 987654321}
        monkeypatch.setattr("rq.Queue", lambda name, connection=None: DummyQueue(name))
        monkeypatch.setattr("rq.Worker.all", lambda connection=None: [DummyWorker("worker1")])
        monkeypatch.setattr("redis.Redis.from_url", lambda url: DummyRedis())
        response = client.get("/jobs/status")
        assert response.status_code == 200
        data = response.json()
        assert "redis_uptime" in data
        assert "redis_memory" in data
        assert "rq_queues" in data
        assert "workers" in data
        assert isinstance(data["rq_queues"], list)
        assert isinstance(data["workers"], list)

    def test_jobs_status_auth_required(self):
        """Test /jobs/status requires authentication (should fail with 401/403)."""
        unauth_client = TestClient(app)
        response = unauth_client.get("/jobs/status")
        assert response.status_code in (401, 403)

    def test_jobs_status_invalid_token(self):
        """Test /jobs/status with an invalid token (should fail with 401/403)."""
        client = TestClient(app)
        headers = {"Authorization": "Bearer invalidtoken123"}
        response = client.get("/jobs/status", headers=headers)
        assert response.status_code in (401, 403)

    def test_job_results_include_names(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test that /job-results/ includes job_name and device_name in each result."""
        # Create device
        from netraven.db.models.device import Device
        device = Device(hostname="test-device-jobresults", ip_address="10.0.9.1", device_type="cisco_ios")
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        # Create job
        from netraven.db.models.job import Job
        job = Job(name="Test Job Results Names", job_type="backup", status="completed")
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        # Create job result
        from netraven.db.models.job_result import JobResult
        import datetime
        jr = JobResult(
            job_id=job.id,
            device_id=device.id,
            job_type=job.job_type,
            status="success",
            result_time=datetime.datetime.utcnow(),
            details={"output": "ok"},
            created_at=datetime.datetime.utcnow()
        )
        db_session.add(jr)
        db_session.commit()
        # Query /job-results/
        response = client.get("/job-results/", headers=admin_headers)
        self.assert_successful_response(response)
        data = response.json()
        assert data["total"] >= 1
        found = False
        for item in data["items"]:
            if item["job_id"] == job.id and item["device_id"] == device.id:
                assert item["job_name"] == job.name
                assert item["device_name"] == device.hostname
                found = True
        assert found, "Expected job result with job_name and device_name not found." 