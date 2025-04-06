## NetRaven Database Service: State of Technology (SOT)

### Executive Summary

This document provides a detailed, implementation-ready reference for the NetRaven database layer. It defines the schema, tooling, file structure, and developer workflows required to build and maintain the PostgreSQL-based persistence layer for NetRaven. All database interactions are performed using synchronous SQLAlchemy ORM with psycopg2. The architecture is designed for local development, with structure and separation allowing future containerization.

### Technology Stack
```yaml
orm: sqlalchemy.orm
migration_tool: alembic
database:
  type: postgresql
  driver: psycopg2
  connection_url: postgresql+psycopg2://netraven:netraven@localhost:5432/netraven
```

### Database Schema Overview

```yaml
models:
  Device:
    id: integer, primary_key
    hostname: string
    ip_address: string
    device_type: string
    last_seen: datetime
    tags: many-to-many => Tag
    configurations: one-to-many => DeviceConfiguration

  DeviceConfiguration:
    id: integer, primary_key
    device_id: foreign_key => Device
    config_data: text
    retrieved_at: datetime
    metadata: jsonb

  Credential:
    id: integer, primary_key
    username: string
    password: string (encrypted)
    priority: integer
    last_used: datetime
    success_rate: float
    tags: many-to-many => Tag

  Tag:
    id: integer, primary_key
    name: string
    type: string
    devices: many-to-many => Device
    credentials: many-to-many => Credential

  Job:
    id: integer, primary_key
    device_id: foreign_key => Device
    status: string
    scheduled_for: datetime
    started_at: datetime
    completed_at: datetime

  JobLog:
    id: integer, primary_key
    job_id: foreign_key => Job
    message: string
    level: string
    timestamp: datetime

  SystemSetting:
    id: integer, primary_key
    key: string
    value: json
    description: string

  ConnectionLog:
    id: integer, primary_key
    job_id: foreign_key => Job
    device_id: foreign_key => Device
    log: text
    timestamp: datetime
```

### Directory Structure
```
/netraven/
├── db/
│   ├── base.py              # declarative base
│   ├── session.py           # sync db engine and session
│   └── models/
│       ├── __init__.py
│       ├── device.py
│       ├── device_config.py
│       ├── credential.py
│       ├── tag.py
│       ├── job.py
│       ├── job_log.py
│       ├── system_setting.py
│       └── connection_log.py
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── config/
│   └── environments/
│       └── dev.yaml
├── tests/
│   └── test_db_connection.py
└── dev_runner.py
```

### Alembic Setup Workflow
```bash
alembic init alembic
# Update alembic.ini:
sqlalchemy.url = postgresql+psycopg2://netraven:netraven@localhost:5432/netraven

# In alembic/env.py:
# from netraven.db.base import Base
# target_metadata = Base.metadata

alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### Sample `session.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from netraven.config.loader import load_config

config = load_config(env="dev")
db_url = config["database"]["url"]

engine = create_engine(db_url, echo=True)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Sample `dev.yaml`
```yaml
database:
  url: postgresql+psycopg2://netraven:netraven@localhost:5432/netraven
logging:
  level: DEBUG
```

### Sample Test: `test_db_connection.py`
```python
import pytest
from sqlalchemy.exc import OperationalError
from netraven.db.session import get_db

def test_db_connect():
    try:
        db = next(get_db())
        db.execute("SELECT 1")
    except OperationalError as e:
        pytest.fail(f"Database connection failed: {e}")
```

### Sample `connection_log.py`
```python
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from netraven.db.base import Base

class ConnectionLog(Base):
    __tablename__ = 'connection_logs'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    log = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
```

### Developer Runner Script: `dev_runner.py`
```python
from netraven.db.session import engine

if __name__ == "__main__":
    with engine.connect() as conn:
        conn.execute("SELECT 1")
        print("✅ Database connection successful")
```

---

> ✅ This document serves as a source of truth for setting up and maintaining the NetRaven PostgreSQL database layer, with a sync-first design and full developer tooling support.

