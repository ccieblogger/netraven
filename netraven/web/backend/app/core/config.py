"""
Configuration management for the NetRaven web backend.

This module provides settings for the web API and connections to the core
NetRaven functionality.
"""

from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any, Union
from pathlib import Path


class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NetRaven"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8080", "http://localhost:3000"]
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here-in-production-use-env-var"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./netraven.db"
    
    # Storage settings
    STORAGE_TYPE: str = "local"  # local, s3, azure
    STORAGE_PATH: Path = Path("./backups")
    GIT_ENABLED: bool = True
    GIT_REMOTE: Optional[str] = None
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    # Scheduling settings
    MAX_PARALLEL_JOBS: int = 5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Create storage configuration dictionary for core module
storage_config = {
    'backup': {
        'storage': {
            'type': settings.STORAGE_TYPE,
            'local': {
                'directory': str(settings.STORAGE_PATH)
            },
            's3': {
                # These would typically be set via environment variables
                'bucket': '',
                'prefix': 'netraven/',
                'region': '',
                'access_key': '',
                'secret_key': '',
            }
        }
    }
} 