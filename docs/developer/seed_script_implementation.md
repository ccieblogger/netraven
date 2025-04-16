# Development Database Seed Script Implementation Plan for NetRaven

## Background

For a productive development experience, it is essential that the NetRaven development environment comes pre-populated with realistic test data. This enables developers and UI/UX designers to view, test, and debug features such as device/job management, credential handling, logging, and configuration diff views without manual data entry.

This document outlines the steps to implement an automated seed script that populates the development database with a rich set of test data every time the dev environment is started or reset.

---

## Requirements

- **Seed script** must populate the database with:
  - Devices (with various types, IPs, and tags)
  - Tags
  - Credentials (valid and invalid)
  - Jobs (with various statuses)
  - Job logs and connection logs
  - Example device configurations (to test diffview)
- **Idempotency:** The script should be safe to run multiple times (no duplicate data).
- **Integration:** The script should run automatically in the dev environment after migrations, or be easily invoked via a utility script.
- **Environment Guard:** Only run in the development environment.
- **Documentation:** Clear instructions for running, re-seeding, and customizing the data.

---

## Implementation Steps

### 1. Create the Seed Script

- Place the script in `scripts/seed_dev_data.py` or a similar location.
- Use SQLAlchemy ORM models to insert data.
- Check for existing data to avoid duplication.
- Populate all relevant tables: `Device`, `Tag`, `Credential`, `Job`, `JobLog`, `ConnectionLog`, and configuration storage (e.g., Git repo or config blobs).

**Example Script Outline:**
```python
# scripts/seed_dev_data.py
from netraven.db.session import get_db
from netraven.db.models import Device, Tag, Credential, Job, JobLog, ConnectionLog
from datetime import datetime

def seed():
    db = next(get_db())
    if db.query(Device).count() > 0:
        print("Database already seeded.")
        return

    # Tags
    tag_core = Tag(name="core")
    tag_edge = Tag(name="edge")
    tag_test = Tag(name="test")
    db.add_all([tag_core, tag_edge, tag_test])
    db.commit()

    # Devices
    device1 = Device(hostname="core-sw1", ip_address="10.0.0.1", device_type="cisco_ios", tags=[tag_core])
    device2 = Device(hostname="edge-fw1", ip_address="10.0.1.1", device_type="paloalto_panos", tags=[tag_edge])
    device3 = Device(hostname="test-router", ip_address="10.0.2.1", device_type="juniper_junos", tags=[tag_test])
    db.add_all([device1, device2, device3])
    db.commit()

    # Credentials
    cred1 = Credential(device_id=device1.id, username="admin", password="correct", description="Valid admin")
    cred2 = Credential(device_id=device1.id, username="admin", password="wrong", description="Invalid admin")
    cred3 = Credential(device_id=device2.id, username="edge", password="edgepass", description="Edge valid")
    db.add_all([cred1, cred2, cred3])
    db.commit()

    # Jobs
    job1 = Job(name="Backup core-sw1", status="COMPLETED", devices=[device1], scheduled_time=datetime.utcnow())
    job2 = Job(name="Audit edge-fw1", status="FAILED", devices=[device2], scheduled_time=datetime.utcnow())
    db.add_all([job1, job2])
    db.commit()

    # Job Logs
    log1 = JobLog(job_id=job1.id, device_id=device1.id, message="Backup completed successfully.", level="INFO")
    log2 = JobLog(job_id=job2.id, device_id=device2.id, message="Authentication failed.", level="ERROR")
    db.add_all([log1, log2])
    db.commit()

    # Connection Logs
    conn_log1 = ConnectionLog(job_id=job1.id, device_id=device1.id, log="show running-config output...", timestamp=datetime.utcnow())
    db.add(conn_log1)
    db.commit()

    print("Development data seeded.")

if __name__ == "__main__":
    seed()
```

### 2. Add Example Configs for DiffView

- Store at least two versions of a device configuration for one device (e.g., `core-sw1`).
- If configs are stored in Git, use the GitPython library to commit two different config versions for the same device.
- If configs are stored as blobs, insert two config records with different timestamps.

**Example:**
```python
# Pseudocode for GitPython
from git import Repo
repo = Repo.init('/data/git-config-repo')
with open('/data/git-config-repo/core-sw1.conf', 'w') as f:
    f.write('hostname core-sw1\ninterface Gi0/1\n ip address 10.0.0.1 255.255.255.0\n')
repo.index.add(['core-sw1.conf'])
repo.index.commit('Initial config for core-sw1')
with open('/data/git-config-repo/core-sw1.conf', 'w') as f:
    f.write('hostname core-sw1\ninterface Gi0/1\n ip address 10.0.0.2 255.255.255.0\n')
repo.index.add(['core-sw1.conf'])
repo.index.commit('Changed IP for core-sw1')
```

### 3. Integrate with Dev Environment Startup

- Option 1: Add a step to your `manage_netraven.sh` script:
  ```bash
  ./setup/manage_netraven.sh seed-dev
  # This runs: python scripts/seed_dev_data.py
  ```
- Option 2: Add a `command` in your Docker Compose for dev:
  ```yaml
  command: >
    sh -c "alembic upgrade head && python scripts/seed_dev_data.py && uvicorn ..."
  ```
- Option 3: Document manual invocation for developers.

### 4. Testing & Validation

- Start the dev environment and verify:
  - Devices, tags, credentials, jobs, and logs appear in the UI.
  - Config diff view works (shows at least two versions for a device).
  - No duplicate data on repeated runs.
- Optionally, add a test to CI to ensure the seed script runs without error.

### 5. Rollback Instructions

- To clear test data, reset the dev database (e.g., `./setup/manage_netraven.sh reset-db dev`).
- To reseed, rerun the seed script after reset.
- No code rollback is needed if the script is idempotent.

---

## Example Data Elements

- **Devices:** core-sw1, edge-fw1, test-router
- **Tags:** core, edge, test
- **Credentials:** Valid and invalid for each device
- **Jobs:** Completed and failed jobs
- **Logs:** Job and connection logs for each job/device
- **Configs:** At least two versions for one device to test diffview

---

## Notes & Best Practices

- Keep test data generic and non-sensitive.
- Make the script safe to run multiple times.
- Only run in the dev environment (add a guard if needed).
- Document how to customize or extend the seed data.

---

## References
- [SQLAlchemy ORM documentation](https://docs.sqlalchemy.org/en/20/orm/)
- [GitPython documentation](https://gitpython.readthedocs.io/en/stable/)
- [Docker Compose documentation](https://docs.docker.com/compose/) 