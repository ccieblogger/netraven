import pytest
from datetime import datetime
from netraven.db.models.job_run import JobRun
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from netraven.api.main import app
from sqlalchemy import text

@pytest.fixture
def db_session():
    from netraven.db import SessionLocal
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def client():
    return TestClient(app)

def test_job_run_persistence(db_session):
    session: Session = db_session
    job_run = JobRun(
        job_name="test_job",
        user_id=1,
        timestamp=datetime.utcnow(),
        status="success",
        parameters={"param1": "value1"},
        output="Test output"
    )
    session.add(job_run)
    session.commit()
    retrieved = session.query(JobRun).filter_by(job_name="test_job").first()
    assert retrieved is not None
    assert retrieved.job_name == "test_job"
    assert retrieved.status == "success"
    assert retrieved.parameters["param1"] == "value1"
    assert retrieved.output == "Test output"

def test_job_history_endpoint(client, db_session):
    session: Session = db_session
    # Ensure user with id=2 exists for FK
    session.execute(text("INSERT INTO users (id, username, email, hashed_password, is_active, role, created_at, updated_at) VALUES (2, 'historyuser', 'historyuser@example.com', 'fakehash', true, 'user', NOW(), NOW()) ON CONFLICT (id) DO NOTHING;"))
    jr = JobRun(
        job_name="history_job",
        user_id=2,
        timestamp=datetime.utcnow(),
        status="success",
        parameters={"foo": "bar"},
        output="history output"
    )
    session.add(jr)
    session.commit()
    # Authenticate as admin using /auth/token
    login_resp = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Simulate API call to /jobs/history/history_job with auth
    response = client.get("/jobs/history/history_job", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(run["job_name"] == "history_job" for run in data)
