"""
Configuration utilities for NetRaven.

This module provides functions for loading and working with configuration files
in the NetRaven application.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Union

# Default configuration values
DEFAULT_CONFIG = {
    "backup": {
        "storage": {
            "type": "local",
            "local": {
                "directory": "data/backups"
            },
            "s3": {
                "bucket": "",
                "prefix": "backups/"
            }
        },
        "format": "{host}_config.txt",
        "git": {
            "enabled": False,
            "author_name": "NetRaven",
            "author_email": "netraven@example.com"
        }
    },
    "logging": {
        "level": "INFO",
        "directory": "logs",
        "filename": "netraven.log",
        "console": {
            "enabled": True,
            "level": "INFO"
        },
        "file": {
            "enabled": True,
            "level": "DEBUG",
            "max_size_mb": 10,
            "backup_count": 5
        },
        "json": {
            "enabled": False,
            "filename": "netraven.json.log"
        },
        "sensitive_data": {
            "redact_enabled": True
        }
    },
    "web": {
        "host": "127.0.0.1",
        "port": 8080,
        "debug": False,
        "allowed_origins": ["http://localhost:3000", "http://localhost:8080"],
        "database": {
            "type": "sqlite",
            "sqlite": {
                "path": "data/netraven.db"
            },
            "postgres": {
                "host": "localhost",
                "port": 5432,
                "database": "netraven",
                "user": "netraven",
                "password": "netraven"
            },
            "mysql": {
                "host": "localhost",
                "port": 3306,
                "database": "netraven",
                "user": "netraven",
                "password": "netraven"
            }
        },
        "authentication": {
            "token_expiration": 86400,  # 24 hours in seconds
            "jwt_algorithm": "HS256",
            "require_https": False,
            "cookie_secure": False,
            "password_min_length": 8
        }
    }
}


def get_default_config_path() -> str:
    """
    Get the default path for the configuration file.
    
    The function checks several common locations for the config file:
    1. NETRAVEN_CONFIG environment variable
    2. ./config.yml in the current directory
    3. ~/.config/netraven/config.yml in the user's home directory
    4. /etc/netraven/config.yml for system-wide configuration
    
    Returns:
        Path to the default configuration file, or fallback to ./config.yml
    """
    # Check environment variable
    env_config = os.environ.get("NETRAVEN_CONFIG")
    if env_config and os.path.exists(env_config):
        return env_config
    
    # Check current directory
    current_dir_config = os.path.join(os.getcwd(), "config.yml")
    if os.path.exists(current_dir_config):
        return current_dir_config
    
    # Check user's config directory
    user_config_dir = os.path.expanduser("~/.config/netraven")
    user_config = os.path.join(user_config_dir, "config.yml")
    if os.path.exists(user_config):
        return user_config
    
    # Check system-wide config
    system_config = "/etc/netraven/config.yml"
    if os.path.exists(system_config):
        return system_config
    
    # Return default path even if it doesn't exist
    return current_dir_config


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two configuration dictionaries.
    
    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary
        
    Returns:
        Merged configuration dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def load_config(config_path: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Tuple of (merged_config, storage_config)
    """
    if not config_path:
        config_path = get_default_config_path()
    
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables
    storage_type = os.environ.get("NETRAVEN_STORAGE_TYPE")
    if storage_type:
        config["backup"]["storage"]["type"] = storage_type
    
    # S3 storage settings from environment
    s3_bucket = os.environ.get("NETRAVEN_S3_BUCKET")
    if s3_bucket:
        config["backup"]["storage"]["s3"]["bucket"] = s3_bucket
    
    s3_prefix = os.environ.get("NETRAVEN_S3_PREFIX")
    if s3_prefix:
        config["backup"]["storage"]["s3"]["prefix"] = s3_prefix
    
    # Local storage from environment
    local_dir = os.environ.get("NETRAVEN_LOCAL_DIR")
    if local_dir:
        config["backup"]["storage"]["local"]["directory"] = local_dir
    
    # Web settings from environment
    web_host = os.environ.get("NETRAVEN_WEB_HOST")
    if web_host:
        config["web"]["host"] = web_host
    
    web_port = os.environ.get("NETRAVEN_WEB_PORT")
    if web_port:
        config["web"]["port"] = int(web_port)
    
    # Web database settings
    web_db_type = os.environ.get("NETRAVEN_WEB_DATABASE_TYPE")
    if web_db_type:
        config["web"]["database"]["type"] = web_db_type
    
    # Load configuration from file if it exists
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                config = merge_configs(config, file_config)
    
    # Extract storage config for convenience
    storage_config = config["backup"]["storage"]
    
    return config, storage_config


def get_storage_path(config: Dict[str, Any], filename: str) -> str:
    """
    Get the full path for a backup file.
    
    Args:
        config: Configuration dictionary
        filename: Name of the backup file
        
    Returns:
        Full path to the backup file
    """
    storage_config = config["backup"]["storage"]
    storage_type = storage_config["type"]
    
    if storage_type == "local":
        directory = storage_config["local"]["directory"]
        # If directory is relative, make it relative to config directory
        if not os.path.isabs(directory):
            config_path = get_default_config_path()
            config_dir = os.path.dirname(os.path.abspath(config_path))
            directory = os.path.join(config_dir, directory)
        
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)
        
        return os.path.join(directory, filename)
    elif storage_type == "s3":
        bucket = storage_config["s3"]["bucket"]
        prefix = storage_config["s3"]["prefix"]
        return f"s3://{bucket}/{prefix}{filename}"
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


def get_backup_filename_format(config: Dict[str, Any]) -> str:
    """
    Get the backup filename format string.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Backup filename format string
    """
    return config["backup"]["format"]


def get_config() -> Dict[str, Any]:
    """
    Get the configuration dictionary.
    
    This is a convenience function that loads the configuration and returns
    just the config dictionary without the storage_config.
    
    Returns:
        Configuration dictionary
    """
    config, _ = load_config()
    return config 