import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from netraven.db.models import Device, DeviceConfiguration
from netraven.db.base import Base
from netraven.scheduler.job_definitions import prune_old_device_configs
from datetime import datetime, timedelta

@pytest.fixture(scope="function")
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()

def add_device_with_configs(session, device_id, num_configs, days_ago_start=0):
    device = Device(id=device_id, hostname=f"dev{device_id}", ip_address=f"10.0.0.{device_id}", device_type="cisco_ios")
    session.add(device)
    session.commit()
    for i in range(num_configs):
        config = DeviceConfiguration(
            device_id=device_id,
            config_data=f"config {i}",
            data_hash=f"hash{i}",
            retrieved_at=datetime.utcnow() - timedelta(days=days_ago_start + i),
            config_metadata={}
        )
        session.add(config)
    session.commit()
    return device

def test_prune_old_device_configs_retains_latest(in_memory_db, monkeypatch):
    session = in_memory_db
    device = add_device_with_configs(session, 1, 15)
    # Patch get_db to yield our test session
    monkeypatch.setattr("netraven.scheduler.job_definitions.get_db", lambda: iter([session]))
    prune_old_device_configs(retain_count=10)
    configs = session.query(DeviceConfiguration).filter_by(device_id=device.id).order_by(DeviceConfiguration.retrieved_at.desc()).all()
    assert len(configs) == 10
    # The configs retained should be the 10 most recent
    expected = [f"config {i}" for i in range(0, 10)]
    actual = [c.config_data for c in configs]
    assert actual == expected

def test_prune_old_device_configs_handles_multiple_devices(in_memory_db, monkeypatch):
    session = in_memory_db
    add_device_with_configs(session, 1, 12)
    add_device_with_configs(session, 2, 8)
    monkeypatch.setattr("netraven.scheduler.job_definitions.get_db", lambda: iter([session]))
    prune_old_device_configs(retain_count=10)
    configs1 = session.query(DeviceConfiguration).filter_by(device_id=1).all()
    configs2 = session.query(DeviceConfiguration).filter_by(device_id=2).all()
    assert len(configs1) == 10
    assert len(configs2) == 8
