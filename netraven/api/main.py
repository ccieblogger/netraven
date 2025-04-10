from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import routers
from .routers import devices, jobs, users, logs, auth_router, tags, credentials

# Check if we're in development mode (you can set this in your environment)
# Default to development mode if not specified
is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"

app = FastAPI(
    title="NetRaven API",
    description="API for managing NetRaven network configuration backups and jobs.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",  # Customize OpenAPI path if needed
    docs_url="/api/docs",              # Customize Swagger UI path
    redoc_url="/api/redoc"             # Customize ReDoc path
)

# Configure CORS - more flexible approach
origins = ["*"] if is_development else [
    "http://localhost:5173",  # Production/fixed origins would go here
    "https://netraven.example.com"  # Example production domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
