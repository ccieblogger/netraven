## NetRaven API Service: State of Technology (SOT)

### Executive Summary

This document outlines the architecture, technology stack, and implementation details of the NetRaven API service. It provides all interaction endpoints for internal services, external integrations, and the frontend UI. This service is responsible for user authentication, job control, device management, and exposing structured API documentation. It is built using FastAPI and integrates with PostgreSQL, Redis (via RQ), and Git (for diff metadata).

### Core Responsibilities
- Authenticate users via JWT (OAuth2 Password Flow)
- Authorize access to protected routes based on roles (admin/user)
- Expose endpoints for managing:
  - Devices and device groups
  - Jobs and job runs
  - Users and role-based access
  - Logs and job histories
  - Config diffs via Git metadata
- Trigger RQ jobs for immediate execution
- Serve OpenAPI schema for UI and external tool integrations

### Technology Stack
```yaml
language: Python 3.11+
framework: FastAPI
authentication: JWT (OAuth2)
database_layer: SQLAlchemy (sync)
queue_trigger: RQ
api_docs: OpenAPI / Swagger (auto)
logging: structlog + JSON
```

### Directory Structure
```
/netraven/api/
├── __init__.py
├── main.py               # FastAPI app instance
├── dependencies.py       # DB/session/context loaders
├── auth.py               # Token creation, validation
├── routers/
│   ├── devices.py
│   ├── jobs.py
│   ├── users.py
│   └── logs.py
├── schemas/              # Pydantic request/response models
│   ├── device.py
│   ├── job.py
│   ├── user.py
│   ├── log.py
│   └── base.py
```

### Route Authentication
```python
# dependencies.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

SECRET = "change-me"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload  # Replace with DB lookup if needed
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Endpoint Examples
```python
# jobs.py
@router.post("/jobs/run/{job_id}")
def run_job_now(job_id: int, user = Depends(get_current_user)):
    q = Queue(connection=Redis())
    q.enqueue(run_device_job, job_id)
    return {"status": "queued", "job_id": job_id}

# devices.py
@router.get("/devices")
def list_devices(user = Depends(get_current_user)):
    return db.query(Device).filter(Device.owner == user['sub']).all()
```

### Wireframe: Job Trigger Flow (Low-Fidelity)
```
+---------------------------------------------------------------+
|                      API Trigger: /jobs/run/123              |
+---------------------------------------------------------------+
| Auth Header: Bearer <jwt>                                    |
|---------------------------------------------------------------|
| Payload: job_id = 123                                        |
|---------------------------------------------------------------|
| Redis <- enqueues job -> RQ Worker (device_comm)             |
+---------------------------------------------------------------+
```

### Testing Strategy
- ✅ Auth route unit test using FastAPI TestClient
- ✅ Permission test for unauthorized routes
- ✅ Queue test to verify job is sent to Redis
- ✅ Schema test using OpenAPI validation

---
