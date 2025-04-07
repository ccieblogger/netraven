from fastapi import FastAPI

# Import routers
from .routers import devices, jobs, users, logs, auth_router

app = FastAPI(
    title="NetRaven API",
    description="API for managing NetRaven network configuration backups and jobs.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",  # Customize OpenAPI path if needed
    docs_url="/api/docs",              # Customize Swagger UI path
    redoc_url="/api/redoc"             # Customize ReDoc path
)

@app.get("/health", tags=["Health"])
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}

# Include routers
app.include_router(auth_router.router)
app.include_router(devices.router)
app.include_router(jobs.router)
app.include_router(users.router)
app.include_router(logs.router)
