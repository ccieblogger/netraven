from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from netraven.config.loader import load_config

# Import routers
from .routers import devices, jobs, users, logs, auth_router, tags, credentials, backups  # Import the new backups router

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

# Include routers
app.include_router(auth_router.router)
app.include_router(users.router)
app.include_router(tags.router)
app.include_router(credentials.router)
app.include_router(devices.router)
app.include_router(jobs.router)
app.include_router(logs.router)
app.include_router(backups.router)  # Include the backups router
