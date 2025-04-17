import os
from datetime import datetime
from netraven.db.session import get_db
from netraven.db.models.device import Device
from netraven.db.models.tag import Tag
from netraven.db.models.credential import Credential
from netraven.db.models.job import Job
from netraven.db.models.job_log import JobLog, LogLevel
from netraven.db.models.connection_log import ConnectionLog
from netraven.db.models.device_config import DeviceConfiguration
from netraven.config.loader import load_config
from git import Repo

# Environment guard: Only run in dev
if os.environ.get("NETRAVEN_ENV", "dev") != "dev":
    print("Seed script only runs in development environment.")
    exit(1)

def seed():
    db = next(get_db())
    # Idempotency: Only seed if no devices exist
    if db.query(Device).count() > 0:
        print("Database already seeded.")
        return

    # --- Tags ---
    tag_core = Tag(name="core")
    tag_edge = Tag(name="edge")
    tag_test = Tag(name="test")
    db.add_all([tag_core, tag_edge, tag_test])
    db.commit()

    # --- Devices ---
    device1 = Device(hostname="core-sw1", ip_address="10.0.0.1", device_type="cisco_ios", tags=[tag_core])
    device2 = Device(hostname="edge-fw1", ip_address="10.0.1.1", device_type="paloalto_panos", tags=[tag_edge])
    device3 = Device(hostname="test-router", ip_address="10.0.2.1", device_type="juniper_junos", tags=[tag_test])
    db.add_all([device1, device2, device3])
    db.commit()

    # --- Credentials ---
    cred1 = Credential.create_with_encrypted_password(username="admin", password="correct", description="Valid admin", tags=[tag_core])
    cred2 = Credential.create_with_encrypted_password(username="admin", password="wrong", description="Invalid admin", tags=[tag_core])
    cred3 = Credential.create_with_encrypted_password(username="edge", password="edgepass", description="Edge valid", tags=[tag_edge])
    cred4 = Credential.create_with_encrypted_password(username="testuser", password="testpass", description="Test credential", tags=[tag_test])
    db.add_all([cred1, cred2, cred3, cred4])
    db.commit()

    # --- Jobs ---
    job1 = Job(name="Backup core-sw1", status="COMPLETED", scheduled_for=datetime.utcnow(), tags=[tag_core])
    job2 = Job(name="Audit edge-fw1", status="FAILED", scheduled_for=datetime.utcnow(), tags=[tag_edge])
    db.add_all([job1, job2])
    db.commit()

    # --- Job Logs ---
    log1 = JobLog(job_id=job1.id, device_id=device1.id, message="Backup completed successfully.", level=LogLevel.INFO)
    log2 = JobLog(job_id=job2.id, device_id=device2.id, message="Authentication failed.", level=LogLevel.ERROR)
    db.add_all([log1, log2])
    db.commit()

    # --- Connection Logs ---
    conn_log1 = ConnectionLog(job_id=job1.id, device_id=device1.id, log="show running-config output...", timestamp=datetime.utcnow())
    db.add(conn_log1)
    db.commit()

    # --- Device Configurations & Git Versioning (Phase 2) ---
    config = load_config()
    repo_path = config.get('git', {}).get('repo_path', '/data/git-config-repo')
    if not os.path.exists(repo_path):
        os.makedirs(repo_path, exist_ok=True)
    try:
        repo = Repo(repo_path)
    except Exception:
        repo = Repo.init(repo_path)

    # Two versions for core-sw1
    config_v1 = 'hostname core-sw1\ninterface Gi0/1\n ip address 10.0.0.1 255.255.255.0\n'
    config_v2 = 'hostname core-sw1\ninterface Gi0/1\n ip address 10.0.0.2 255.255.255.0\n'
    config_file = os.path.join(repo_path, f'{device1.id}_config.txt')

    # Version 1
    with open(config_file, 'w') as f:
        f.write(config_v1)
    repo.index.add([config_file])
    commit1 = repo.index.commit('Initial config for core-sw1')
    dev_conf1 = DeviceConfiguration(
        device_id=device1.id,
        config_data=config_v1,
        retrieved_at=datetime.utcnow(),
        config_metadata={"commit": commit1.hexsha, "version": 1}
    )
    db.add(dev_conf1)
    db.commit()

    # Version 2
    with open(config_file, 'w') as f:
        f.write(config_v2)
    repo.index.add([config_file])
    commit2 = repo.index.commit('Changed IP for core-sw1')
    dev_conf2 = DeviceConfiguration(
        device_id=device1.id,
        config_data=config_v2,
        retrieved_at=datetime.utcnow(),
        config_metadata={"commit": commit2.hexsha, "version": 2}
    )
    db.add(dev_conf2)
    db.commit()

    print("Development data seeded, including device config versions for diffview.")

if __name__ == "__main__":
    seed() 