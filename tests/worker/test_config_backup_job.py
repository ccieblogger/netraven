import pytest
from sqlalchemy.orm import Session
from netraven.db.models.device import Device
from netraven.db.models.device_config import DeviceConfiguration
from netraven.worker.jobs import config_backup
from datetime import datetime

@pytest.fixture
def test_device(db_session: Session):
    device = Device(hostname="test-device", ip_address="10.0.0.1", device_type="cisco_ios")
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device

def test_config_backup_creates_db_record(db_session: Session, test_device):
    """
    Test that running the config backup job stores a configuration in the database.
    """
    # Patch the network call to return a known config
    from unittest.mock import patch
    test_config = "hostname test-device\ninterface eth0"
    with patch("netraven.worker.backends.netmiko_driver.run_command", return_value=test_config):
        with patch("netraven.worker.redactor.redact", side_effect=lambda c, _: c):
            result = config_backup.run(test_device, job_id=123, config={}, db=db_session)
    assert result["success"] is True
    # Confirm a DeviceConfiguration record exists
    configs = db_session.query(DeviceConfiguration).filter_by(device_id=test_device.id).all()
    assert len(configs) == 1
    assert configs[0].config_data == test_config
    assert configs[0].config_metadata["job_id"] == 123

def test_config_backup_deduplication(db_session: Session, test_device):
    """
    Test that running the backup job twice with the same config only stores one record (deduplication).
    """
    from unittest.mock import patch
    test_config = "hostname test-device\ninterface eth0"
    with patch("netraven.worker.backends.netmiko_driver.run_command", return_value=test_config):
        with patch("netraven.worker.redactor.redact", side_effect=lambda c, _: c):
            # First run: should store config
            result1 = config_backup.run(test_device, job_id=1, config={}, db=db_session)
            # Second run: should deduplicate (not store again)
            result2 = config_backup.run(test_device, job_id=2, config={}, db=db_session)
    assert result1["success"] is True
    assert result2["success"] is True
    configs = db_session.query(DeviceConfiguration).filter_by(device_id=test_device.id).all()
    assert len(configs) == 1  # Only one record due to deduplication

def test_config_backup_stores_metadata(db_session: Session, test_device):
    """
    Test that the backup job stores correct metadata (job_id, timestamp).
    """
    from unittest.mock import patch
    test_config = "hostname test-device\ninterface eth0"
    with patch("netraven.worker.backends.netmiko_driver.run_command", return_value=test_config):
        with patch("netraven.worker.redactor.redact", side_effect=lambda c, _: c):
            result = config_backup.run(test_device, job_id=555, config={}, db=db_session)
    assert result["success"] is True
    config_record = db_session.query(DeviceConfiguration).filter_by(device_id=test_device.id).first()
    assert config_record is not None
    assert config_record.config_metadata["job_id"] == 555
    assert config_record.retrieved_at is not None

def test_config_backup_handles_network_error(db_session: Session, test_device):
    """
    Test that the backup job handles network errors gracefully and does not store a config.
    """
    from unittest.mock import patch
    from netmiko.exceptions import NetmikoTimeoutException
    with patch("netraven.worker.backends.netmiko_driver.run_command", side_effect=NetmikoTimeoutException("timeout")):
        result = config_backup.run(test_device, job_id=999, config={}, db=db_session)
    assert result["success"] is False
    configs = db_session.query(DeviceConfiguration).filter_by(device_id=test_device.id).all()
    assert len(configs) == 0

def test_config_backup_stores_multiple_versions(db_session: Session, test_device):
    """
    Test that running the backup job with different configs stores multiple versions.
    """
    from unittest.mock import patch
    config1 = "hostname test-device\ninterface eth0"
    config2 = "hostname test-device\ninterface eth1"
    with patch("netraven.worker.backends.netmiko_driver.run_command", side_effect=[config1, config2]):
        with patch("netraven.worker.redactor.redact", side_effect=lambda c, _: c):
            result1 = config_backup.run(test_device, job_id=1, config={}, db=db_session)
            result2 = config_backup.run(test_device, job_id=2, config={}, db=db_session)
    assert result1["success"] is True
    assert result2["success"] is True
    configs = db_session.query(DeviceConfiguration).filter_by(device_id=test_device.id).all()
    assert len(configs) == 2
    assert {c.config_metadata["job_id"] for c in configs} == {1, 2}
