# NetRaven `device_comm` Developer Bootstrapping + Scaffolding Package

This single file includes everything a developer or AI agent needs to understand, build, and run the `device_comm` (Device Gateway) service for the NetRaven system.

---

## Developer Bootstrapping Appendix: `device_comm` Service

### Context
This service (also referred to as the Device Gateway) is the interface between the NetRaven system and customer network devices. It abstracts device communication protocols (e.g., SSH, Telnet, REST), provides a secure internal REST API for services like the Scheduler to request config collection, and performs protocol-level work like connection reuse, error handling, and normalization.

### Core Responsibilities
- Expose a RESTful API for service-to-service communication
- Execute connection and command tasks on behalf of the Scheduler
- Authenticate with provided credentials (not stored internally)
- Normalize interactions across device types and protocols
- Report detailed logs to the Job Logging service
- Efficiently manage device connection pools
- Handle retries, errors, and timeouts consistently

### Project Info
```yaml
service_name: device_comm
logging:
  level: DEBUG
  format: json
connection:
  max_pool_size: 10
  connection_timeout: 15
  retry_attempts: 3
  retry_backoff: 2
security:
  api_key: your-internal-api-key
  jwt_issuer: https://auth.netraven.local
  redaction_patterns:
    - 'password'
    - 'secret'
```

---

### Dev Runner (dev_runner.py)
```python
import asyncio
from device_comm.service import run_device_collection

if __name__ == "__main__":
    asyncio.run(run_device_collection())
```

---

### API Entrypoints and Execution
```python
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/execute-command")
async def execute_command(req: CommandRequest):
    return await run_command_on_device(req)
```

---

### Internal Workflow
```
Scheduler → POST /execute-command
→ Device Comm validates and tests credentials
→ Establishes connection (SSH, Telnet, etc.)
→ Executes command(s)
→ Redacts sensitive output
→ Logs results via Job Log Service
→ Updates device status in DB
→ Responds to Scheduler with result
```

---

### API Schemas
```python
from pydantic import BaseModel
from typing import Optional

class CredentialPayload(BaseModel):
    username: str
    password: str
    method: str  # 'ssh', 'telnet', etc.

class CommandRequest(BaseModel):
    device_id: int
    ip: str
    command: str
    credential: CredentialPayload

class CommandResponse(BaseModel):
    result: str
    success: bool
    error: Optional[str] = None
```

---

### Credential Handling
- Credentials are **not stored** inside the `device_comm` service.
- Credentials must be passed as part of the request.
- Credential failures must:
  - Be logged with context (without leaking secrets)
  - Return structured errors to the Scheduler
  - Be reported for retry prioritization by the caller

---

### Job Logging Interface
```python
{
  "job_id": 123,
  "device_id": 456,
  "event": "command_output",
  "output": "<REDACTED_OUTPUT>",
  "success": true,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

### Monitoring
- `/health` → returns service status
- `/status` → returns internal summary (connection/session stats)

---

### Suggested Dev Stack
```
- Python 3.11+
- asyncpg + SQLAlchemy (async)
- FastAPI (preferred)
- Netmiko / NAPALM / Paramiko
- Pydantic
- JWT + API key middleware
- structlog or JSON logging
- Prometheus client
- pytest + unittest.mock
```

---

### Database Integration

The `device_comm` service communicates with the PostgreSQL database to:
- Log job events and command results
- Update device metadata
- Store retrieved configuration data
- Save raw session logs from Netmiko into a structured table

#### Add: db.py
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://netraven:netraven@localhost:5432/netraven")

engine = create_async_engine(DB_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
```

#### Add: connection_logs table definition (models.py)
```python
from sqlalchemy import Column, Integer, Text, DateTime, func
from device_comm.db import Base

class ConnectionLog(Base):
    __tablename__ = 'connection_logs'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer)
    device_id = Column(Integer)
    log = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
```

#### Update: log_utils.py
```python
from device_comm.db import get_session
from device_comm.models import ConnectionLog

async def save_connection_log(job_id, device_id, raw_log: str):
    redacted = redact_secrets(raw_log)
    async for session in get_session():
        entry = ConnectionLog(job_id=job_id, device_id=device_id, log=redacted)
        session.add(entry)
        await session.commit()

# Basic redaction
def redact_secrets(log: str):
    redacted_lines = []
    for line in log.splitlines():
        if any(secret in line.lower() for secret in ["password", "secret"]):
            redacted_lines.append("[REDACTED LINE]")
        else:
            redacted_lines.append(line)
    return "
".join(redacted_lines)
```

#### Update: service.py (example DB insert + session log save)
```python
from device_comm.db import get_session
from sqlalchemy import text
from device_comm.log_utils import save_connection_log

async def run_command_on_device(request):
    command_output = f"Simulated output of '{request.command}' on {request.ip}"
    netmiko_log = f"Login to {request.ip} successful
> {request.command}
{command_output}"

    # Save output to connection log table
    await save_connection_log(job_id=1, device_id=request.device_id, raw_log=netmiko_log)

    # Also log summary to job_logs
    async for session in get_session():
        await session.execute(
            text("INSERT INTO job_logs (job_id, device_id, message, success) VALUES (:job, :device, :msg, :ok)"),
            {
                "job": 1,
                "device": request.device_id,
                "msg": f"Command executed: {request.command}",
                "ok": True
            }
        )
        await session.commit()

    return {
        "result": command_output,
        "success": True,
        "error": None
    }
```

---

#### Add: security.py
```python
from fastapi import Header, HTTPException, Depends
from device_comm.config import settings

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")
```

---

### File + Code Scaffolding
```text
project_root/
├── device_comm/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── controller.py
│   ├── service.py
│   ├── models.py
│   ├── connection_pool.py
│   ├── log_utils.py
│   └── backends/
│       ├── __init__.py
│       ├── ssh.py
│       └── telnet.py
├── dev_runner.py
└── tests/
    └── test_device_comm.py
```

#### dev_runner.py
```python
import asyncio
import argparse
import uvicorn
from device_comm.service import run_device_collection, run_command_on_device
from device_comm.models import CommandRequest, CredentialPayload

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["api", "standalone"], default="standalone")
args = parser.parse_args()

if args.mode == "api":
    uvicorn.run("device_comm.main:app", host="127.0.0.1", port=8001, reload=True)

elif args.mode == "standalone":
    async def sample_run():
        test_request = CommandRequest(
            device_id=1,
            ip="192.168.1.1",
            command="show version",
            credential=CredentialPayload(
                username="admin",
                password="adminpass",
                method="ssh"
            )
        )
        result = await run_command_on_device(test_request)
        print("Execution Result:", result)

    asyncio.run(sample_run())
```

#### main.py
```python
from fastapi import FastAPI
from device_comm.controller import router

app = FastAPI()
app.include_router(router)
```

#### controller.py
```python
from fastapi import APIRouter, Depends
from device_comm.models import CommandRequest, CommandResponse
from device_comm.service import run_command_on_device
from device_comm.security import verify_api_key

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/execute-command", response_model=CommandResponse, dependencies=[Depends(verify_api_key)])
async def execute_command(req: CommandRequest):
    return await run_command_on_device(req)

@router.get("/status")
def status():
    # Simplified static return for now
    return {
        "active_connections": 0,
        "successful_commands": 0,
        "queued_jobs": 0
    }
from fastapi import APIRouter
from device_comm.models import CommandRequest, CommandResponse
from device_comm.service import run_command_on_device

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/execute-command", response_model=CommandResponse)
async def execute_command(req: CommandRequest):
    return await run_command_on_device(req)
```

### 🌐 REST API Endpoint for Accessing Connection Logs

```python
@router.get("/connection-log/{job_id}")
async def get_connection_log(job_id: int, db=Depends(get_session), api=Depends(verify_api_key)):
    result = await db.execute(
        select(ConnectionLog)
        .where(ConnectionLog.job_id == job_id)
        .order_by(ConnectionLog.timestamp.desc())
        .limit(1)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return {
        "device_id": log.device_id,
        "job_id": log.job_id,
        "timestamp": log.timestamp,
        "log": log.log
    }
```


#### service.py
```python
async def run_device_collection():
    # Stubbed: logic for batch device collection
    pass

async def run_command_on_device(request):
    # Stubbed: logic to connect to device and execute a command
    return {
        "result": "<output>",
        "success": True,
        "error": None
    }

#### models.py
```python
from pydantic import BaseModel
from typing import Optional

class CredentialPayload(BaseModel):
    username: str
    password: str
    method: str

class CommandRequest(BaseModel):
    device_id: int
    ip: str
    command: str
    credential: CredentialPayload

class CommandResponse(BaseModel):
    result: str
    success: bool
    error: Optional[str] = None
```

#### config.py
```python
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    api_key: str = os.getenv("API_KEY", "dev-key")
    log_level: str = os.getenv("LOG_LEVEL", "DEBUG")
    class Config:
        env_file = ".env"

settings = Settings()
```

#### backends/ssh.py
```python
async def send_ssh_command(ip, command, credentials):
    # Placeholder for Netmiko/Paramiko interaction
    return "fake SSH output"
```

#### connection_pool.py
```python
# Placeholder: implement pooling or simple connection handling
```

#### log_utils.py
```python
# Placeholder: implement standardized logging interface
```

#### test_device_comm.py
```python
from fastapi.testclient import TestClient
from device_comm.main import app
from device_comm.models import CommandRequest, CredentialPayload
import pytest

client = TestClient(app)

@pytest.fixture
def dummy_credential():
    return CredentialPayload(
        username="admin",
        password="password",
        method="ssh"
    )

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_execute_command_success(dummy_credential):
    request_data = CommandRequest(
        device_id=123,
        ip="192.168.1.1",
        command="show version",
        credential=dummy_credential
    )
    response = client.post("/execute-command", json=request_data.dict())
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "result" in body
    assert body["error"] is None
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
