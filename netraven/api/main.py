from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from netraven.config.loader import load_config
import time
from sqlalchemy import text
from netraven.db.session import engine
from redis import Redis
from rq import Worker
from rq_scheduler import Scheduler
from datetime import datetime, timezone

# Import routers
from .routers import devices, jobs, users, auth_router, tags, credentials, backups, logs  # Import the new logs router

# Load configuration
config = load_config()
api_config = config.get('api', {})

app = FastAPI(
    title="NetRaven API",
    description="NetRaven Network Configuration Management System API",
    version="1.0.0",
    docs_url="/docs",  # Remove /api prefix
    redoc_url="/redoc",  # Remove /api prefix
    openapi_url="/openapi.json"  # Remove /api prefix
)

# Configure CORS - expand to include containerized frontend URLs
allow_origins = [
    # Local development
    "http://localhost:5173",
    "http://localhost:5174", 
    "http://localhost:5175", 
    "http://localhost:5176", 
    "http://127.0.0.1:5173", 
    "http://127.0.0.1:5174",
    # Container hostnames and names
    "http://frontend:5173",
    "http://frontend:80",
    "http://netraven-frontend-dev:5173",
    "http://netraven-frontend-prod:80",
    # Production access
    "http://localhost:80",
    "http://localhost"
]

# Add any additional origins from config
if 'cors_origins' in api_config and isinstance(api_config['cors_origins'], list):
    allow_origins.extend(api_config['cors_origins'])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", status_code=200)  # Remove /api prefix
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# --- System Status Health Check ---
_system_status_cache = {"result": None, "timestamp": 0}
CACHE_TTL = 30  # seconds

def check_postgres():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "healthy"
    except Exception:
        return "unhealthy"

def check_redis(redis_url):
    try:
        redis_conn = Redis.from_url(redis_url)
        redis_conn.ping()
        return "healthy"
    except Exception:
        return "unhealthy"

def check_worker(redis_url):
    try:
        redis_conn = Redis.from_url(redis_url)
        workers = Worker.all(connection=redis_conn)
        return "healthy" if workers else "unhealthy"
    except Exception:
        return "unhealthy"

def check_scheduler(redis_url):
    try:
        redis_conn = Redis.from_url(redis_url)
        scheduler = Scheduler(connection=redis_conn)
        jobs = scheduler.get_jobs()
        return "healthy" if jobs else "unhealthy"
    except Exception:
        return "unhealthy"

@app.get("/system/status", status_code=200)
def system_status(request: Request):
    refresh = request.query_params.get("refresh", "false").lower() == "true"
    now = time.time()
    if not refresh and _system_status_cache["result"] and now - _system_status_cache["timestamp"] < CACHE_TTL:
        return _system_status_cache["result"]

    config = load_config()
    redis_url = config.get('scheduler', {}).get('redis_url', 'redis://localhost:6379/0')

    status = {
        "api": "healthy",  # If this endpoint responds, API is healthy
        "postgres": check_postgres(),
        "redis": check_redis(redis_url),
        "worker": check_worker(redis_url),
        "scheduler": check_scheduler(redis_url),
        "system_time": datetime.now(timezone.utc).isoformat()
    }
    _system_status_cache["result"] = status
    _system_status_cache["timestamp"] = now
    return status

# Include routers
app.include_router(auth_router.router)
app.include_router(users.router)
app.include_router(tags.router)
app.include_router(credentials.router)
app.include_router(devices.router)
app.include_router(jobs.router)
app.include_router(backups.router)  # Include the backups router
app.include_router(logs.router)
