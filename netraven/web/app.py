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

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(devices.router)
app.include_router(credentials.router)
app.include_router(tags.router)
app.include_router(keys.router)
app.include_router(admin_settings.router) 