# NetRaven Developer Onboarding: Database Interaction with Async SQLAlchemy

## 1. Introduction

Welcome to NetRaven development! This document provides a guide for developers on how to interact with the NetRaven PostgreSQL database using the SQLAlchemy ORM with asynchronous support (`asyncio`). Understanding these patterns is crucial for developing features across all NetRaven services.

We use:
*   **Database:** PostgreSQL
*   **ORM:** SQLAlchemy (v2.0 style)
*   **Driver:** `asyncpg` (for asynchronous operations)
*   **Connection:** `postgresql+asyncpg://netraven:netraven@localhost:5432/netraven`
*   **Models:** Defined in the `netraven_db/db/models/` directory.
*   **Session Management:** Provided via `netraven_db/db/session.py`.

All database operations should be performed asynchronously using `async`/`await`.

## 2. Prerequisites

Before you start interacting with the database, ensure your development environment is set up correctly:

1.  **WSL2 Environment:** Development is expected to occur within WSL2.
2.  **VS Code:** Configured with Remote - WSL extension for seamless development.
3.  **Python:** A recent version of Python 3 (e.g., 3.10+) installed within WSL2.
4.  **Virtual Environment:** A Python virtual environment created and activated (e.g., `python3 -m venv venv` and `source venv/bin/activate`).
5.  **PostgreSQL Server:** Running and accessible from WSL2 at `localhost:5432`. The database `netraven` must exist, along with the user `netraven` having the password `netraven` and necessary privileges. (The `setup/install_postgres_wsl2.sh` script can configure this).
6.  **Dependencies & Schema:** Project dependencies installed (`pip install -r requirements.txt`) and the database schema migrated to the latest version (`./setup/setup_db.sh` or `venv/bin/alembic upgrade head`).

## 3. Core Concepts

*   **SQLAlchemy ORM:** Allows you to interact with the database using Python objects (models) instead of writing raw SQL for most operations.
*   **Models:** Python classes defined in `netraven_db/db/models/` that map to database tables (e.g., `Device`, `Credential`, `JobLog`).
*   **AsyncSession:** The primary interface for database interactions. All operations using the session are asynchronous and must be `await`ed.
*   **Engine:** Manages database connections. We use an async engine configured in `netraven_db/db/session.py`.
*   **`get_db` Dependency:** A convenience async context manager in `netraven_db/db/session.py` that provides an `AsyncSession`, handles commits on success, and rollbacks on exceptions. This is the **recommended way** to get a session.

## 4. Getting a Database Session

The standard way to get a database session for your operations is using the `get_db` async context manager.

```python
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from netraven_db.db.session import get_db
from netraven_db.db.models import Device # Example model
# Need select for the example query below
from sqlalchemy import select

async def example_database_operation():
    print("Starting database operation...")
    try:
        # get_db() yields an AsyncSession
        async for db_session in get_db():
            # Use the session within this block
            print(f"Obtained session: {db_session}")
            # Example: Fetch a device (details below)
            stmt = select(Device).limit(1)
            result = await db_session.execute(stmt)
            device = result.scalars().first()
            if device:
                print(f"Found device: {device.hostname}")
            else:
                print("No devices found.")
            # The context manager handles commit/rollback automatically
            # If an exception occurs here, it will rollback.
            # If the block completes without error, it will commit.
        print("Session block finished.")

    except Exception as e:
        print(f"An error occurred outside the session block: {e}")

# --- How to run this example ---
# async def main():
#    await example_database_operation()
#
# if __name__ == "__main__":
#    asyncio.run(main())
```

**Note:** In a FastAPI application, `get_db` would typically be used as a dependency injector:

```python
# Example FastAPI route
# from fastapi import Depends, APIRouter
# from sqlalchemy.ext.asyncio import AsyncSession
# from netraven_db.db.session import get_db

# router = APIRouter()
# @router.get("/some_path")
# async def read_something(db: AsyncSession = Depends(get_db)):
#    # Use 'db' session here directly
#    pass
```

## 5. Querying Data (SELECT)

Use SQLAlchemy's `select()` construct to build queries.

```python
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload # For eager loading relationships
from sqlalchemy.ext.asyncio import AsyncSession
from netraven_db.db.session import get_db
from netraven_db.db.models import Device, Tag, Credential # Import necessary models

async def query_examples():
    async for db in get_db(): # Use the recommended session provider

        # --- Simple Select All ---
        print("\n--- Fetching all devices (limit 5) ---")
        stmt_all = select(Device).limit(5)
        result_all = await db.execute(stmt_all)
        all_devices = result_all.scalars().all()
        for device in all_devices:
            print(f"Device ID: {device.id}, Hostname: {device.hostname}")

        # --- Filtering (WHERE clause) ---
        print("\n--- Fetching device by hostname ---")
        target_hostname = "router1.example.com" # Replace with an actual hostname if needed
        stmt_filter = select(Device).where(Device.hostname == target_hostname)
        result_filter = await db.execute(stmt_filter)
        # .first() returns one or None
        device_by_hostname = result_filter.scalars().first()
        if device_by_hostname:
            print(f"Found by hostname: {device_by_hostname.hostname} (IP: {device_by_hostname.ip_address})")
        else:
            print(f"Device with hostname '{target_hostname}' not found.")

        # --- Accessing Relationships (Lazy Loading - default) ---
        if device_by_hostname:
            print(f"\n--- Tags for {device_by_hostname.hostname} (Lazy Loaded) ---")
            # Accessing device.tags triggers *another* query if not eager loaded
            try:
                # Note: This requires the session `db` to still be active
                # In async, need run_sync for lazy loads unless session configured differently
                tags = await db.run_sync(lambda session: list(device_by_hostname.tags))
                if tags:
                    for tag in tags:
                        print(f"- Tag: {tag.name}")
                else:
                    print("No tags associated (Lazy Load).")
            except Exception as e:
                 print(f"Error accessing lazy-loaded tags (ensure session is active): {e}")


        # --- Accessing Relationships (Eager Loading - recommended for performance) ---
        # Use options(selectinload(...)) to load related objects in the initial query
        print(f"\n--- Fetching device by hostname with Tags (Eager Loaded) ---")
        stmt_eager = select(Device).\
            where(Device.hostname == target_hostname).\
            options(selectinload(Device.tags)) # Eager load tags
        result_eager = await db.execute(stmt_eager)
        device_with_tags = result_eager.scalars().first()
        if device_with_tags:
            print(f"Found: {device_with_tags.hostname}")
            if device_with_tags.tags:
                for tag in device_with_tags.tags:
                    # Accessing .tags here does NOT trigger a new query
                    print(f"- Tag: {tag.name} (Type: {tag.type})")
            else:
                print("No tags associated (Eager Load).")
        else:
             print(f"Device with hostname '{target_hostname}' not found.")

        # --- Querying via relationships (e.g., find credentials for a device's tags) ---
        if device_with_tags:
             print(f"\n--- Finding Credentials via Tags for {device_with_tags.hostname} ---")
             device_tag_ids = [tag.id for tag in device_with_tags.tags]
             if device_tag_ids:
                # Find credentials associated with any of the device's tags
                stmt_creds = select(Credential).\
                    join(Credential.tags).\
                    where(Tag.id.in_(device_tag_ids)).\
                    distinct() # Avoid duplicate credentials if they share tags
                result_creds = await db.execute(stmt_creds)
                credentials = result_creds.scalars().all()
                if credentials:
                    for cred in credentials:
                        print(f"- Credential ID: {cred.id}, User: {cred.username}, Priority: {cred.priority}")
                else:
                    print("No credentials found matching device tags.")
             else:
                 print("Device has no tags to search credentials with.")


# --- Run Example ---
# async def main():
#     await query_examples()
# if __name__ == "__main__":
#     asyncio.run(main())
```

## 6. Inserting Data (INSERT)

1.  Create an instance of your model class.
2.  Add the instance to the session using `db.add()`.
3.  The `get_db` context manager handles the commit.

```python
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from netraven_db.db.session import get_db
from netraven_db.db.models import JobLog, Job # Assuming Job model exists

async def insert_example():
    async for db in get_db():
        print("\n--- Inserting a new Job Log ---")
        # Assume job_id 1 exists for this example
        new_log_entry = JobLog(
            job_id=1, # Make sure this job ID exists in your DB
            level="INFO",
            message="Configuration retrieval started."
            # timestamp defaults to now
        )
        db.add(new_log_entry)
        # No explicit commit needed here, get_db handles it.
        # If successful, the log is added. If an error occurs before
        # the 'async for' block exits, it will be rolled back.

        # Note: The new_log_entry object might not have its ID populated
        # until the commit happens *after* the block.
        # To get the ID immediately, you might need `await db.flush()`
        # await db.flush()
        # print(f"New Log Entry ID (after flush): {new_log_entry.id}")

    print("Insertion attempt complete (committed if no errors).")

# --- Run Example ---
# async def main():
#     await insert_example()
# if __name__ == "__main__":
#     asyncio.run(main())

```

## 7. Updating Data (UPDATE)

1.  Query the object(s) you want to update.
2.  Modify the attributes of the model instance(s).
3.  SQLAlchemy tracks changes on objects attached to the session. `get_db` handles the commit.

```python
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from netraven_db.db.session import get_db
from netraven_db.db.models import SystemSetting

async def update_example():
    setting_key_to_update = "backup_retention_days"
    new_value = {"days": 90}

    async for db in get_db():
        print(f"\n--- Updating System Setting '{setting_key_to_update}' ---")
        stmt = select(SystemSetting).where(SystemSetting.key == setting_key_to_update)
        result = await db.execute(stmt)
        setting = result.scalars().first()

        if setting:
            print(f"Found setting. Old value: {setting.value}")
            setting.value = new_value # Update the attribute
            # Optional: add to session explicitly if unsure if tracked
            # db.add(setting)
            print(f"Setting '{setting_key_to_update}' value updated (pending commit).")
        else:
            # Option: Create if not exists (Upsert pattern)
            print(f"Setting '{setting_key_to_update}' not found. Creating it.")
            new_setting = SystemSetting(
                key=setting_key_to_update,
                value=new_value,
                description="Number of days to retain backups."
            )
            db.add(new_setting)

    print("Update/Insert attempt complete (committed if no errors).")


# --- Run Example ---
# async def main():
#     await update_example()
# if __name__ == "__main__":
#     asyncio.run(main())
```

## 8. Deleting Data (DELETE)

1.  Query the object you want to delete.
2.  Use `await db.delete(object_instance)`.
3.  `get_db` handles the commit.

```python
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from netraven_db.db.session import get_db
from netraven_db.db.models import JobLog

async def delete_example():
    log_id_to_delete = 1 # Replace with an actual ID you want to delete

    async for db in get_db():
        print(f"\n--- Deleting Job Log ID: {log_id_to_delete} ---")

        # Fetch the object first
        log_entry = await db.get(JobLog, log_id_to_delete) # db.get is efficient for PK lookups

        if log_entry:
            await db.delete(log_entry)
            print(f"Job Log ID {log_id_to_delete} marked for deletion (pending commit).")
        else:
            print(f"Job Log ID {log_id_to_delete} not found.")

    print("Deletion attempt complete (committed if no errors).")


# --- Run Example ---
# async def main():
#     await delete_example()
# if __name__ == "__main__":
#     asyncio.run(main())
```

## 9. Example Service Function Stubs

Here's how these patterns might look in functions within different NetRaven services:

```python
# --- Potentially in a device communication service ---
from sqlalchemy.orm import selectinload
from netraven_db.db.models import Device, DeviceConfiguration
from sqlalchemy import select # Make sure select is imported
from sqlalchemy.ext.asyncio import AsyncSession # Ensure AsyncSession is imported
import datetime # Ensure datetime is imported

async def get_device_with_config(hostname: str, db: AsyncSession) -> Device | None:
    """Fetches a device and its latest configuration."""
    stmt = select(Device).\
        where(Device.hostname == hostname).\
        options(
            # Correct way to load relationship on DeviceConfiguration
            selectinload(Device.configurations) # Load the collection first
            # If you need details from DeviceConfiguration itself, it loads automatically
            # or you could potentially chain a joinedload if needed, depends on exact use case
            # selectinload(Device.configurations).joinedload(DeviceConfiguration.metadata_) # Example chain
         )
    result = await db.execute(stmt)
    return result.scalars().first()

async def save_new_config(device_id: int, config_text: str, metadata: dict, db: AsyncSession):
    """Saves a newly retrieved configuration."""
    new_config = DeviceConfiguration(
        device_id=device_id,
        config_data=config_text,
        metadata_=metadata # Remember the underscore!
    )
    db.add(new_config)
    # Commit handled by caller's session management (e.g., get_db)

# --- Potentially in a scheduler service ---
from netraven_db.db.models import Job, JobLog
# import datetime # Already imported above

async def create_backup_job(device_id: int, scheduled_time: datetime.datetime | None, db: AsyncSession) -> Job:
    """Creates a new job entry in the database."""
    new_job = Job(
        device_id=device_id,
        status='pending',
        scheduled_for=scheduled_time
    )
    db.add(new_job)
    await db.flush() # To get the new job's ID if needed immediately
    return new_job

async def update_job_status(job_id: int, new_status: str, db: AsyncSession):
    """Updates the status of an existing job."""
    job = await db.get(Job, job_id)
    if job:
        job.status = new_status
        if new_status == 'running':
            job.started_at = datetime.datetime.utcnow()
        elif new_status in ['completed', 'failed']:
            job.completed_at = datetime.datetime.utcnow()
        # db.add(job) # Usually not needed for updates, but doesn't hurt
    else:
        print(f"Warning: Job ID {job_id} not found for status update.")
    # Commit handled by caller

# --- Potentially in credential/tag management ---
from netraven_db.db.models import Credential, Tag

async def find_credentials_by_tag_name(tag_name: str, db: AsyncSession) -> list[Credential]:
    """Finds credentials associated with a specific tag name."""
    stmt = select(Credential).\
        join(Credential.tags).\
        where(Tag.name == tag_name)
    result = await db.execute(stmt)
    return list(result.scalars().all())

```

## 10. Important Considerations

*   **Always `await`:** All database operations using the `AsyncSession` are asynchronous.
*   **Error Handling:** Wrap database operations in `try...except` blocks to catch potential `SQLAlchemyError` exceptions (e.g., connection errors, integrity errors). The `get_db` context manager helps by automatically rolling back transactions on exceptions within its block.
*   **Transactions:** `get_db` manages transactions per request or operation block. For complex operations spanning multiple steps that must succeed or fail together, ensure they happen within a single `async for db in get_db():` block.
*   **Raw SQL:** If you absolutely must use raw SQL, wrap it in `text()`: `await db.execute(text("SELECT version()"))`. Prefer the ORM methods where possible.
*   **Session Lifecycle:** Be mindful of the session's scope. Objects loaded in one session might become detached if used after the session is closed. Using the `get_db` pattern helps manage this correctly for typical use cases.
*   **Performance:** Use eager loading (`options(selectinload(...))` or `joinedload(...)`) for relationships you know you'll need, to avoid the N+1 query problem associated with lazy loading. Analyze complex queries.

## 11. Verification

You can verify your database connection and basic setup using:

1.  **Dev Runner:** `venv/bin/python dev_runner.py --db-check`
2.  **Pytest:** `venv/bin/pytest` (runs tests in the `tests/` directory)

This document provides the foundation for interacting with the NetRaven database. Refer to the SQLAlchemy 2.0 documentation for more advanced patterns and features. Happy coding! 