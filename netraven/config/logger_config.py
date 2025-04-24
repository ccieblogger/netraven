import os

def get_logger_config():
    """
    Returns logger-specific configuration. Extend this to load from YAML if needed.
    """
    return {
        "level": os.getenv("NETRAVEN_LOG_LEVEL", "INFO"),
        "destinations": [d.strip() for d in os.getenv("NETRAVEN_LOG_DESTINATIONS", "stdout").split(",")],
        # Add more logger-specific config as needed
    } 