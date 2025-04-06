import yaml
import os
import logging
from typing import Dict, Any

log = logging.getLogger(__name__)

# Default environment if not specified
DEFAULT_ENV = "dev"
CONFIG_DIR = "config/environments"

def load_config(env: str = None) -> Dict[str, Any]:
    """Loads configuration from YAML file based on environment.

    Args:
        env (str, optional): The environment name (e.g., 'dev', 'test', 'prod').
                             Defaults to os.getenv('APP_ENV') or DEFAULT_ENV.

    Returns:
        A dictionary containing the loaded configuration.

    Raises:
        FileNotFoundError: If the configuration file for the specified env doesn't exist.
        yaml.YAMLError: If the YAML file is malformed.
        Exception: For other unexpected errors during loading.
    """
    if env is None:
        env = os.getenv("APP_ENV", DEFAULT_ENV)
    
    config_file_path = os.path.join(CONFIG_DIR, f"{env}.yaml")
    log.info(f"Attempting to load configuration from: {config_file_path}")

    config: Dict[str, Any] = {}

    try:
        if not os.path.exists(config_file_path):
            raise FileNotFoundError(f"Configuration file not found: {config_file_path}")

        with open(config_file_path, 'r') as stream:
            config = yaml.safe_load(stream)
            if config is None: # Handle empty YAML file case
                config = {}
        
        log.info(f"Successfully loaded configuration for environment '{env}'.")
        
        # --- Environment Variable Overrides --- 
        # Example: Override database URL
        db_url_override = os.getenv("DATABASE_URL")
        if db_url_override:
            if "database" not in config:
                config["database"] = {}
            config["database"]["url"] = db_url_override
            log.info("Overrode database URL with DATABASE_URL environment variable.")
            
        # TODO: Add overrides for other critical settings if needed (e.g., secrets)

        return config

    except FileNotFoundError as fnf_err:
        log.error(fnf_err)
        raise # Re-raise to indicate critical failure
    except yaml.YAMLError as yaml_err:
        log.error(f"Error parsing YAML file {config_file_path}: {yaml_err}")
        raise # Re-raise
    except Exception as e:
        log.error(f"Unexpected error loading configuration: {e}")
        raise # Re-raise

# Example usage (for potential direct testing)
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     try:
#         dev_config = load_config("dev")
#         print("Dev Config:", dev_config)
#         # test_config = load_config("test") # This would fail if test.yaml doesn't exist
#         # print("Test Config:", test_config)
#         
#         # Test override
#         os.environ["DATABASE_URL"] = "overridden_url_for_testing"
#         dev_config_override = load_config("dev")
#         print("Dev Config with Override:", dev_config_override)
#         del os.environ["DATABASE_URL"] # Clean up env var
#         
#     except Exception as e:
#         print(f"Failed to load config: {e}")
