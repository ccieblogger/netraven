

## Developer Bootstrapping Appendix (LLM-Ready)

This section is intended to provide a precise set of technical details and structured data to be consumed by AI agents (e.g., Cursor AI, Gemini 2.5, GPT) for bootstrapping the NetRaven database environment.

### Project Info
```yaml
project_name: netraven
orm: sqlalchemy.async_orm
database:
  type: postgresql
  driver: asyncpg
  connection_url: postgresql+asyncpg://postgres:netraven@localhost:5432/netraven
  migration_tool: alembic
```

### Initial Models

Below is an expanded model list, incorporating schema detail from the PostgreSQL Intended State document:
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
    type: string  # e.g., role, location, vendor
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

### Alembic Setup
```bash
# Initialize Alembic
alembic init alembic

# Update alembic.ini with correct sqlalchemy.url
sqlalchemy.url = postgresql+asyncpg://postgres:netraven@localhost:5432/netraven

# Modify alembic/env.py to import models from netraven.db.models
# Set target_metadata = Base.metadata

# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### File and Directory Structure (Database Focus)
```plaintext
/netraven-db/
├── alembic.ini
├── netraven/
│   ├── __init__.py
│   ├── db/
│   │   ├── base.py            # declarative base
│   │   ├── session.py         # async db engine and session
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── device.py
│   │       ├── credential.py
│   │       ├── tag.py
│   │       ├── joblog.py
│   │       |── system_setting.py
|   |       └── connection_log.py
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── <timestamp>_initial_schema.py
├── config/
│   └── environments/
│       └── dev.yaml           # DB config + env overrides
├── tests/
│   ├── __init__.py
│   └── test_db_connection.py
└── dev_runner.py              # Run services locally for debugging
```

### Sample dev.yaml
```yaml
database:
  url: postgresql+asyncpg://postgres:netraven@localhost:5432/netraven
logging:
  level: DEBUG
```

### Sample DB Session Helper (session.py)
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from netraven.config.loader import load_config

config = load_config(env="dev")
db_url = config["database"]["url"]

engine = create_async_engine(db_url, echo=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
```

### Sample Pytest Test File (test_db_connection.py)
```python
import pytest
import asyncio
from sqlalchemy.exc import OperationalError
from netraven.db.session import SessionLocal

@pytest.mark.asyncio
async def test_database_connection():
    try:
        async with SessionLocal() as session:
            await session.execute("SELECT 1")
    except OperationalError as e:
        pytest.fail(f"Database connection failed: {e}")
```

### Sample Dev Runner Script (dev_runner.py)
```python
import argparse
import asyncio
from netraven.config.loader import load_config
from netraven.db.session import engine
from netraven.db.models import device  # Example import

async def run_db_check():
    async with engine.begin() as conn:
        await conn.execute("SELECT 1")
        print("✅ Database connection successful")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NetRaven Dev Runner")
    parser.add_argument("--db-check", action="store_true", help="Check database connection")
    args = parser.parse_args()

    if args.db_check:
        asyncio.run(run_db_check())
```

### 📂 New Model File
In the `netraven_db/db/models/` directory, create:

`connection_log.py`
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

Also update `models/__init__.py` to include:
```python
from .connection_log import ConnectionLog
```

### 🔎 Access Example (Optional for LLM)
```sql
SELECT log, timestamp
FROM connection_logs
WHERE device_id = 123
ORDER BY timestamp DESC
LIMIT 1;
```

### 🧪 Test Case (Optional for `test_db_connection.py`)
```python
from netraven.db.models.connection_log import ConnectionLog

@pytest.mark.asyncio
async def test_connection_log_insert():
    async with SessionLocal() as session:
        log = ConnectionLog(job_id=1, device_id=101, log="Sample connection log")
        session.add(log)
        await session.commit()

---


