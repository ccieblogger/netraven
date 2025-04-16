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
    def test_job_data(self):
        """Test job data for creation."""
        return {
            "name": "test-job-api-1",
            "command": "show version",
            "device_filter_type": "tag",
            "device_filter_value": "test-tag",
            "schedule_type": "onetime",
            "is_enabled": True,
            "tags": []
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
        assert data["command"] == test_job_data["command"]
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
                command="show version",
                device_filter_type="tag",
                device_filter_value="test",
                schedule_type="onetime",
                is_enabled=True,
                status="pending"
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
                command="show version",
                device_filter_type="tag",
                device_filter_value="test",
                schedule_type="onetime",
                is_enabled=True,
                status="pending"
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
                command="show version",
                device_filter_type="tag",
                device_filter_value="test",
                schedule_type="cron",
                is_enabled=True,
                status="success"
            ),
            models.Job(
                name="filter-interval-failed", 
                command="show version",
                device_filter_type="tag",
                device_filter_value="test",
                schedule_type="interval",
                is_enabled=True,
                status="failed"
            ),
            models.Job(
                name="filter-cron-pending", 
                command="show version",
                device_filter_type="tag",
                device_filter_value="test",
                schedule_type="cron",
                is_enabled=False,
                status="pending"
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
            command="show version",
            device_filter_type="tag",
            device_filter_value="test",
            schedule_type="onetime",
            is_enabled=True,
            status="pending"
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
            command="show version",
            device_filter_type="tag",
            device_filter_value="test",
            schedule_type="onetime",
            is_enabled=True,
            status="pending"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        update_data = {
            "name": "updated-name",
            "command": "show interfaces",
            "is_enabled": False
        }
        
        response = client.put(f"/jobs/{job.id}", json=update_data, headers=admin_headers)
        self.assert_successful_response(response)
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["command"] == update_data["command"]
        assert data["is_enabled"] == update_data["is_enabled"]
        # Original fields should be preserved
        assert data["schedule_type"] == job.schedule_type

    def test_update_job_with_conflict(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test updating a job with a conflicting name."""
        # Create two jobs
        job1 = models.Job(
            name="update-conflict-1",
            command="show version",
            device_filter_type="tag",
            device_filter_value="test",
            schedule_type="onetime",
            is_enabled=True,
            status="pending"
        )
        job2 = models.Job(
            name="update-conflict-2",
            command="show version",
            device_filter_type="tag",
            device_filter_value="test",
            schedule_type="onetime",
            is_enabled=True,
            status="pending"
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
            command="show version",
            device_filter_type="tag",
            device_filter_value="test",
            schedule_type="onetime",
            is_enabled=True,
            status="pending"
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
            command="show version",
            device_filter_type="tag",
            device_filter_value="test",
            schedule_type="onetime",
            is_enabled=True,
            status="pending"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        response = client.post(f"/jobs/run/{job.id}", headers=admin_headers)
        self.assert_successful_response(response, 202)
        
        data = response.json()
        assert data["status"] == "queued"
        assert data["job_id"] == job.id
        assert data["queue_job_id"] == "mock-queue-job-id"
        
        # Verify the job was enqueued with correct ID
        mock_queue.enqueue.assert_called_once()

    @patch('netraven.api.routers.jobs.rq_queue')
    def test_run_disabled_job(self, mock_queue, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test triggering a disabled job."""
        job = models.Job(
            name="disabled-job",
            command="show version",
            device_filter_type="tag",
            device_filter_value="test",
            schedule_type="onetime",
            is_enabled=False,  # Disabled
            status="pending"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        response = client.post(f"/jobs/run/{job.id}", headers=admin_headers)
        self.assert_error_response(response, 400, "disabled")
        
        # Verify no job was enqueued
        mock_queue.enqueue.assert_not_called() 