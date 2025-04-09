import pytest
from unittest.mock import MagicMock, patch, call, ANY
from datetime import datetime, timedelta, timezone

from netraven.scheduler.job_registration import sync_jobs_from_db, generate_rq_job_id
from netraven.db.models import Job # Import the actual model

# --- Mock Data --- 

@pytest.fixture
def mock_db_session():
    """Fixture for a mocked DB session."""
    return MagicMock()

@pytest.fixture
def mock_scheduler():
    """Fixture for a mocked RQ Scheduler instance."""
    scheduler = MagicMock()
    scheduler.get_jobs.return_value = [] # Default to no existing jobs
    return scheduler

@pytest.fixture
def sample_jobs():
    """Fixture providing sample Job model instances."""
    job1 = Job(id=1, name="Interval Job", is_enabled=True, schedule_type='interval', interval_seconds=3600)
    job2 = Job(id=2, name="Cron Job", is_enabled=True, schedule_type='cron', cron_string="0 * * * *")
    job3 = Job(id=3, name="Onetime Job", is_enabled=True, schedule_type='onetime', scheduled_for=datetime.now(timezone.utc) + timedelta(hours=1))
    job4 = Job(id=4, name="Disabled Job", is_enabled=False, schedule_type='interval', interval_seconds=60)
    job5 = Job(id=5, name="Onetime Past", is_enabled=True, schedule_type='onetime', scheduled_for=datetime.now(timezone.utc) - timedelta(hours=1))
    job6 = Job(id=6, name="Invalid Type", is_enabled=True, schedule_type='unknown')
    job7 = Job(id=7, name="Existing Job", is_enabled=True, schedule_type='interval', interval_seconds=120)
    return [job1, job2, job3, job4, job5, job6, job7]

# --- Test Cases --- 

@patch('netraven.scheduler.job_registration.get_db')
def test_sync_jobs_schedules_correct_types(mock_get_db, mock_db_session, mock_scheduler, sample_jobs):
    """Verify jobs with valid schedule types are scheduled correctly."""
    # Arrange
    mock_get_db.return_value = iter([mock_db_session])
    # Return only the schedulable jobs (1, 2, 3)
    mock_db_session.query.return_value.filter.return_value.all.return_value = [sample_jobs[0], sample_jobs[1], sample_jobs[2]]
    
    # Act
    sync_jobs_from_db(mock_scheduler)

    # Assert
    # Check interval job was scheduled
    mock_scheduler.schedule.assert_called_once_with(
        scheduled_time=ANY, # Check time is roughly now
        func=ANY, # Check correct function is targeted (run_worker_job)
        args=[sample_jobs[0].id],
        interval=sample_jobs[0].interval_seconds,
        repeat=None,
        job_id=generate_rq_job_id(sample_jobs[0].id),
        description=ANY,
        meta=ANY
    )
    # Check cron job was scheduled
    mock_scheduler.cron.assert_called_once_with(
        sample_jobs[1].cron_string,
        func=ANY,
        args=[sample_jobs[1].id],
        repeat=None,
        job_id=generate_rq_job_id(sample_jobs[1].id),
        description=ANY,
        meta=ANY
    )
    # Check onetime job was scheduled
    mock_scheduler.enqueue_at.assert_called_once_with(
        sample_jobs[2].scheduled_for,
        ANY,  # Function should be ANY, not specifically named
        args=[sample_jobs[2].id],
        job_id=generate_rq_job_id(sample_jobs[2].id),
        description=ANY,
        meta=ANY
    )
    # Verify the target function is correct (patching it might be better)
    assert mock_scheduler.schedule.call_args.kwargs['func'].__name__ == 'run_job'
    assert mock_scheduler.cron.call_args.kwargs['func'].__name__ == 'run_job'
    assert mock_scheduler.enqueue_at.call_args.args[1].__name__ == 'run_job'

@patch('netraven.scheduler.job_registration.get_db')
def test_sync_jobs_skips_disabled_invalid_past(mock_get_db, mock_db_session, mock_scheduler, sample_jobs):
    """Verify disabled, invalid type, and past one-time jobs are skipped."""
    # Arrange
    mock_get_db.return_value = iter([mock_db_session])
    # Return only the jobs that should be skipped (4, 5, 6)
    mock_db_session.query.return_value.filter.return_value.all.return_value = [sample_jobs[3], sample_jobs[4], sample_jobs[5]]

    # Act
    sync_jobs_from_db(mock_scheduler)

    # Assert
    mock_scheduler.schedule.assert_not_called()
    mock_scheduler.cron.assert_not_called()
    mock_scheduler.enqueue_at.assert_not_called()

@patch('netraven.scheduler.job_registration.get_db')
def test_sync_jobs_skips_existing(mock_get_db, mock_db_session, mock_scheduler, sample_jobs):
    """Verify jobs already present in the RQ scheduler are skipped."""
    # Arrange
    job_to_test = sample_jobs[6] # Job 7 (Existing Job)
    rq_job_id = generate_rq_job_id(job_to_test.id)
    
    mock_get_db.return_value = iter([mock_db_session])
    mock_db_session.query.return_value.filter.return_value.all.return_value = [job_to_test]
    
    # Mock scheduler to report the job ID as existing
    mock_existing_rq_job = MagicMock(id=rq_job_id)
    mock_scheduler.get_jobs.return_value = [mock_existing_rq_job]

    # Act
    sync_jobs_from_db(mock_scheduler)

    # Assert
    mock_scheduler.schedule.assert_not_called()
    mock_scheduler.cron.assert_not_called()
    mock_scheduler.enqueue_at.assert_not_called()
    mock_scheduler.get_jobs.assert_called_once() # Verify it checked existing jobs 