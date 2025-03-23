# Import FastAPI
from fastapi import FastAPI

# Import routers
from netraven.web.routers import (
    auth,
    users,
    devices,
    credentials,
    tags,
    keys,
    admin_settings
)

# Create FastAPI app
app = FastAPI(title="NetRaven API", version="1.0.0")

# Include routers
app.include_router(auth.router, prefix="/api/auth")
app.include_router(users.router)
app.include_router(devices.router)
app.include_router(credentials.router)
app.include_router(tags.router)
app.include_router(keys.router)
app.include_router(admin_settings.router)
