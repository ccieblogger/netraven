import pytest
import pytest_asyncio
from sqlalchemy.future import select
from sqlalchemy import delete, text # Removed inspect
import uuid

# Models are needed, SessionLocal is replaced by fixture
from netraven_db.db.models import ConnectionLog, Device, Job

# Using function scope for prerequisites to ensure clean data for each test
@pytest_asyncio.fixture(scope="function")
# No longer needs db_session directly, just creates objects
async def prerequisite_data():
    """Creates prerequisite Device and Job ORM objects."""
    print("DEBUG: Creating prerequisite ORM objects...")
    device = Device(hostname=f"test-device-prereq-{uuid.uuid4()}", ip_address="1.1.1.1")
    job = Job(status=f"pending-prereq-{uuid.uuid4()}")
    
    # Just return the objects, don't commit here
    yield device, job
    print("DEBUG: prerequisite_data fixture teardown (no DB action here).")

@pytest.mark.asyncio
async def test_connection_log_insert(db_session, prerequisite_data):
    """Test inserting a ConnectionLog record."""
    # Get the ORM objects from the fixture
    device, job = prerequisite_data 
    test_log_content = "Sample connection log content for testing."

    # Add prerequisite objects and commit to get their IDs
    print("DEBUG: Adding/committing prerequisite objects...")
    db_session.add_all([device, job])
    await db_session.commit()
    await db_session.refresh(device)
    await db_session.refresh(job)
    print(f"DEBUG: Prerequisites committed. device.id: {device.id}, job.id: {job.id}")

    # Now create ConnectionLog using the generated IDs
    print("DEBUG: Creating ConnectionLog object...")
    new_log = ConnectionLog(
        job_id=job.id,
        device_id=device.id,
        log=test_log_content
    )
    
    # Add and commit the new log
    db_session.add(new_log)
    print("DEBUG: Committing new_log...")
    await db_session.commit()
    print("DEBUG: Commit finished.")
    
    # Refresh to get log's ID and defaults (like timestamp)
    await db_session.refresh(new_log)
    print(f"DEBUG: Refreshed new_log. id: {new_log.id}")

    # Verify the insertion
    assert new_log.id is not None
    assert new_log.job_id == job.id
    assert new_log.device_id == device.id
    assert new_log.log == test_log_content
    assert new_log.timestamp is not None

    # Optional: Query back to double-check
    result = await db_session.execute(
        select(ConnectionLog).where(ConnectionLog.id == new_log.id)
    )
    retrieved_log = result.scalar_one_or_none()
    assert retrieved_log is not None
    assert retrieved_log.log == test_log_content

    # Cleanup of new_log handled by prerequisite_data teardown via FK cascade (or explicit delete there) 