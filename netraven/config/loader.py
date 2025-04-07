import os
import yaml
import structlog
from pathlib import Path
from typing import Dict, Any

log = structlog.get_logger()

# Define the base directory for configuration files relative to this loader file
# Assumes loader.py is in netraven/config/
CONFIG_DIR = Path(__file__).parent.resolve()
ENV_DIR = CONFIG_DIR / "environments"

# --- Helper function to recursively merge dictionaries --- 
def merge_dicts(source: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge source dict into destination dict.
    
    Values from source overwrite values in destination.
    If a value is a dict in both, it recurses.
    """
    for key, value in source.items():
        if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
            merge_dicts(value, destination[key])
        else:
            destination[key] = value
    return destination

# --- Helper function to get nested keys from environment variables --- 
def get_env_overrides(prefix: str = "NETRAVEN_") -> Dict[str, Any]:
    """Creates a nested dictionary from environment variables with a specific prefix.
    
    Example: NETRAVEN_DATABASE__URL becomes {"database": {"url": ...}}
    """
    overrides = {}
    prefix_len = len(prefix)
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix and split by double underscore for nesting
            parts = key[prefix_len:].lower().split('__')
            d = overrides
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = value
    return overrides

# --- Main configuration loading function --- 
def load_config(env: str = None, config_dir: Path = ENV_DIR) -> Dict[str, Any]:
    """Loads configuration from YAML files and merges environment variables.
    
    1. Determines the environment (defaulting to 'dev').
    2. Loads the base config file (e.g., 'default.yaml').
    3. Loads the environment-specific config file (e.g., 'dev.yaml') and merges it.
    4. Loads environment variables starting with 'NETRAVEN_' and merges them.
    
    Args:
        env: The environment name (e.g., 'dev', 'prod'). Reads NETRAVEN_ENV if None.
        config_dir: The directory containing environment YAML files.
        
    Returns:
        A dictionary containing the merged configuration.
    """
    if env is None:
        env = os.getenv("NETRAVEN_ENV", "dev").lower()
        log.debug(f"Environment not specified, using NETRAVEN_ENV or default: {env}")
    else:
        env = env.lower()

    base_config_path = config_dir / "default.yaml"
    env_config_path = config_dir / f"{env}.yaml"
    
    config: Dict[str, Any] = {}

    # 1. Load base configuration (if exists)
    if base_config_path.exists():
        try:
            with open(base_config_path, 'r') as f:
                base_config = yaml.safe_load(f)
                if base_config:
                    config = merge_dicts(base_config, config)
                log.debug(f"Loaded base configuration from {base_config_path}")
        except Exception as e:
            log.error(f"Failed to load base config {base_config_path}", error=str(e))

    # 2. Load environment-specific configuration and merge
    if env_config_path.exists():
        try:
            with open(env_config_path, 'r') as f:
                env_config = yaml.safe_load(f)
                if env_config:
                    config = merge_dicts(env_config, config)
                log.debug(f"Loaded environment configuration from {env_config_path}")
        except Exception as e:
            log.error(f"Failed to load environment config {env_config_path}", error=str(e))
    else:
        log.warning(f"Environment config file not found: {env_config_path}")

    # 3. Load environment variable overrides and merge
    env_overrides = get_env_overrides()
    if env_overrides:
        config = merge_dicts(env_overrides, config)
        log.debug("Applied environment variable overrides", overrides=env_overrides)

    if not config:
        log.warning("Configuration result is empty. Check config files and environment.")

    return config

# Example Usage (can be run directly for testing)
if __name__ == "__main__":
    # Example: Set an env var override for testing
    os.environ["NETRAVEN_LOGGING__LEVEL"] = "DEBUG_FROM_ENV"
    os.environ["NETRAVEN_NEW_SETTING"] = "hello_from_env"
    
    loaded_config = load_config()
    print("Loaded Configuration:")
    import json
    print(json.dumps(loaded_config, indent=2))
