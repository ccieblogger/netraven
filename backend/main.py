from fastapi import FastAPI
from backend.api.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8080,
        ssl_certfile="cert.pem",  # Path to your SSL certificate
        ssl_keyfile="key.pem",    # Path to your SSL private key
    )
