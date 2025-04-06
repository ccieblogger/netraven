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
    config_metadata: jsonb

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
├── setup/
│   ├── dev_runner.py
│   └── setup_postgres.sh
├── config/
│   └── environments/
│       └── dev.yaml
├── tests/
│   └── test_db_connection.py
├── setup/
│   └── dev_runner.py
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

### Developer Runner Script: `setup/dev_runner.py`
```python
import argparse
import os
from netraven.config.loader import load_config
from netraven.db.session import create_engine, SessionLocal
from netraven.db.base import Base

config = load_config(env="dev")
db_url = os.getenv("DATABASE_URL", config["database"]["url"])
engine = create_engine(db_url, echo=True)

def run_db_check():
    print(f"Checking DB connection at {db_url}...")
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

def run_create_schema():
    print("Creating database schema (for dev use only)...")
    try:
        Base.metadata.create_all(engine)
        print("✅ Schema created successfully.")
    except Exception as e:
        print(f"❌ Failed to create schema: {e}")

def run_drop_schema():
    print("WARNING: This will drop all tables in the database!")
    confirm = input("Are you sure you want to continue? Type 'yes' to proceed: ")
    if confirm.lower() == 'yes':
        try:
            Base.metadata.drop_all(engine)
            print("✅ All tables dropped successfully.")
        except Exception as e:
            print(f"❌ Failed to drop schema: {e}")
    else:
        print("Schema drop cancelled.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NetRaven Dev Runner - Manage DB for development.")
    parser.add_argument("--db-check", action="store_true", help="Check database connection")
    parser.add_argument("--create-schema", action="store_true", help="Create DB schema from models")
    parser.add_argument("--drop-schema", action="store_true", help="Drop all DB tables (DANGEROUS)")

    args = parser.parse_args()

    if args.db_check:
        run_db_check()
    elif args.create_schema:
        run_create_schema()
    elif args.drop_schema:
        run_drop_schema()
    else:
        print("No task specified. Use -h or --help for options.")
```

---

### Appendix: PostgreSQL 14 Installation and Management Script

To simplify the developer experience, use the following script to install PostgreSQL 14 and bootstrap the NetRaven database.

#### `setup/setup_postgres.sh`
```bash
#!/bin/bash

set -e

COMMAND=${1:-install}

DB_USER=${DB_USER:-netraven}
DB_PASSWORD=${DB_PASSWORD:-netraven}
DB_NAME=${DB_NAME:-netraven}

# Install PostgreSQL 14
sudo apt update
sudo apt install -y wget gnupg lsb-release

# Add PostgreSQL's official GPG key
wget -qO - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /usr/share/keyrings/postgresql.gpg

# Add PostgreSQL repo
echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

sudo apt update
sudo apt install -y postgresql-14 postgresql-client-14

# Enable and start service
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create user and database
sudo -u postgres psql <<EOF
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
      CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASSWORD';
   END IF;
END
\$\$;

CREATE DATABASE $DB_NAME OWNER $DB_USER;
EOF

echo "✅ PostgreSQL 14 installed and NetRaven database initialized."

elif [[ $COMMAND == "drop" ]]; then
  echo "⚠ Dropping all tables from database '$DB_NAME'..."
  sudo -u postgres psql -d $DB_NAME -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  echo "✅ Schema reset."

elif [[ $COMMAND == "check" ]]; then
  echo "🔍 Testing database connection..."
  PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1" || echo "❌ Failed to connect to database"

elif [[ $COMMAND == "refresh" ]]; then
  echo "♻ Removing PostgreSQL and reinstalling..."
  sudo systemctl stop postgresql || true
  sudo apt remove --purge -y postgresql* postgresql-client*
  sudo rm -rf /var/lib/postgresql /etc/postgresql
  sudo apt autoremove -y
  echo "🧹 PostgreSQL removed. Reinstalling..."
  exec "$0" install

else
  echo "Usage: $0 [install|drop|check|refresh]"
  exit 1
```

> 📝 The `DB_USER`, `DB_PASSWORD`, and `DB_NAME` values are automatically pulled from the configuration system (`config/environments/dev.yaml`) but can also be overridden using environment variables.

---
