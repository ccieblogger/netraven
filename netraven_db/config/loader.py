import yaml
import os
from pathlib import Path

def load_config(env: str = "dev", config_dir: str = "config") -> dict:
    """Loads configuration files based on environment."""
    base_path = Path(config_dir)
    env_file = base_path / "environments" / f"{env}.yaml"

    config = {}

    # Load environment-specific config first
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_config = yaml.safe_load(f)
            if env_config:
                config.update(env_config)
    else:
        print(f"Warning: Environment config file not found at {env_file}")


    # TODO: Implement loading of base and component-specific configs later
    # Example: Load main config
    # main_config_file = base_path / "netraven.yaml"
    # if main_config_file.exists():
    #     with open(main_config_file, 'r') as f:
    #         main_config = yaml.safe_load(f)
    #         # Merge carefully, env takes precedence
    #         config = {**main_config, **config}


    # Override with environment variables (e.g., DB_URL)
    db_url_env = os.getenv("DB_URL")
    if db_url_env:
        if 'database' not in config:
            config['database'] = {}
        config['database']['url'] = db_url_env
        print(f"Overriding database URL from environment variable.")


    if not config.get("database", {}).get("url"):
         print(f"Warning: Database URL not found in config file {env_file} or DB_URL environment variable.")
         # Provide a default fallback or raise an error depending on requirements
         # For now, let's assume the file *should* exist or env var is set.

    return config

if __name__ == '__main__':
    # Example usage:
    dev_config = load_config(env="dev", config_dir="../../config") # Adjust path for direct execution
    print("Loaded Dev Config:")
    print(dev_config)

    # Example with env var override
    # Set DB_URL environment variable before running if you want to test this
    # export DB_URL="postgresql+asyncpg://user:pass@host:port/dbname_override"
    test_config = load_config(env="test", config_dir="../../config")
    print("\nLoaded Test Config (potentially overridden):")
    print(test_config) 