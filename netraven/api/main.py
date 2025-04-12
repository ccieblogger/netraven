from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from .routers import devices, jobs, users, logs, auth_router, tags, credentials, backups  # Import the new backups router

app = FastAPI(
    title="NetRaven API",
    description="API for managing NetRaven network configuration backups and jobs.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",  # Customize OpenAPI path if needed
    docs_url="/api/docs",              # Customize Swagger UI path
    redoc_url="/api/redoc"             # Customize ReDoc path
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}

# Include routers
app.include_router(auth_router.router)
app.include_router(users.router)
app.include_router(tags.router)
app.include_router(credentials.router)
app.include_router(devices.router)
app.include_router(jobs.router)
app.include_router(logs.router)
app.include_router(backups.router)  # Include the backups router
