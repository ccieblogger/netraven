import os
import yaml

CONFIG_PATH = os.environ.get(
    "NETRAVEN_CONFIG_PATH",
    "/app/netraven/config/environments/dev.yaml"
)

def get_logger_config():
    """
    Safely loads the logger-specific configuration from YAML and merges with environment variables.
    Only loads the 'logging' section to avoid circular import/logging issues.
    """
    config = {}
    # Try to load YAML config
    try:
        with open(CONFIG_PATH, "r") as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config and "logging" in yaml_config:
                config = yaml_config["logging"]
    except Exception as e:
        # Optionally log this with the main logger if available
        config = {}
    # Merge with environment variables if present
    env_level = os.getenv("NETRAVEN_LOG_LEVEL")
    if env_level:
        config["level"] = env_level
    env_dest = os.getenv("NETRAVEN_LOG_DESTINATIONS")
    if env_dest:
        config["destinations"] = [d.strip() for d in env_dest.split(",")]
    # Fallback defaults
    if "level" not in config:
        config["level"] = "INFO"
    if "destinations" not in config:
        config["destinations"] = ["stdout"]
    return config 