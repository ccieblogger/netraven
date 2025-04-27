import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from netraven.api.main import app
from datetime import datetime, timedelta
from tests.api.base import BaseAPITest

class TestSchedulerAPI(BaseAPITest):
    @patch("netraven.api.routers.scheduler.Scheduler")
    @patch("netraven.api.routers.scheduler.get_redis_conn")
    def test_scheduler_jobs_success(self, mock_redis, mock_scheduler, admin_headers, client):
        # Mock scheduler.get_jobs()
        mock_job = MagicMock()
        mock_job.meta = {"db_job_id": 1, "schedule_type": "interval", "interval_seconds": 60}
        mock_job.description = "Test Job"
        mock_job.args = [1]
        mock_job.next_run = datetime.utcnow() + timedelta(minutes=5)
        mock_job.repeat = None
        mock_job.enqueued_at = datetime.utcnow()
        mock_scheduler.return_value.get_jobs.return_value = [mock_job]
        mock_redis.return_value = MagicMock()

        response = client.get("/scheduler/jobs", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["id"] == 1
        assert data[0]["name"] == "Test Job"
        assert data[0]["interval_seconds"] == 60
        assert data[0]["schedule_type"] == "interval"

    @patch("netraven.api.routers.scheduler.Queue")
    @patch("netraven.api.routers.scheduler.get_redis_conn")
    def test_queue_status_success(self, mock_redis, mock_queue, admin_headers, client):
        # Mock queue.jobs
        mock_job = MagicMock()
        mock_job.id = "rq-job-1"
        mock_job.enqueued_at = datetime.utcnow() - timedelta(minutes=1)
        mock_job.func_name = "run_job"
        mock_job.args = [1]
        mock_job.meta = {"db_job_id": 1}
        mock_queue.return_value.jobs = [mock_job]
        mock_redis.return_value = MagicMock()

        response = client.get("/scheduler/queue/status", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "jobs" in data[0]
        assert data[0]["jobs"][0]["job_id"] == "rq-job-1"
        assert data[0]["jobs"][0]["func_name"] == "run_job"

    @patch("netraven.api.routers.scheduler.Scheduler", side_effect=Exception("Redis error"))
    @patch("netraven.api.routers.scheduler.get_redis_conn")
    def test_scheduler_jobs_error(self, mock_redis, mock_scheduler, admin_headers, client):
        mock_redis.return_value = MagicMock()
        response = client.get("/scheduler/jobs", headers=admin_headers)
        assert response.status_code == 503
        assert "Failed to fetch scheduled jobs" in response.text

    @patch("netraven.api.routers.scheduler.Queue", side_effect=Exception("Redis error"))
    @patch("netraven.api.routers.scheduler.get_redis_conn")
    def test_queue_status_error(self, mock_redis, mock_queue, admin_headers, client):
        mock_redis.return_value = MagicMock()
        response = client.get("/scheduler/queue/status", headers=admin_headers)
        assert response.status_code == 503
        assert "Failed to fetch queue status" in response.text

    def test_scheduler_jobs_auth_required(self):
        unauth_client = TestClient(app)
        response = unauth_client.get("/scheduler/jobs")
        assert response.status_code in (401, 403)

    def test_queue_status_auth_required(self):
        unauth_client = TestClient(app)
        response = unauth_client.get("/scheduler/queue/status")
        assert response.status_code in (401, 403) 