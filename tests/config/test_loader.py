import pytest
import os
import yaml
from pathlib import Path
from unittest.mock import patch

# Function to test
from netraven.config.loader import load_config, get_env_overrides

@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Creates a temporary directory structure for config files."""
    env_dir = tmp_path / "environments"
    env_dir.mkdir()
    return env_dir

@pytest.fixture
def clean_netraven_env_vars():
    """Cleans up NETRAVEN_* environment variables after tests."""
    original_vars = {k: v for k, v in os.environ.items() if k.startswith("NETRAVEN_")}
    # Remove keys for the test
    for k in original_vars:
        del os.environ[k]
    yield
    # Restore original keys
    for k, v in original_vars.items():
        os.environ[k] = v
    # Remove any keys added during the test that weren't there originally
    current_keys = {k for k, v in os.environ.items() if k.startswith("NETRAVEN_")}
    added_keys = current_keys - set(original_vars.keys())
    for k in added_keys:
        del os.environ[k]

# --- Tests for get_env_overrides --- 
def test_get_env_overrides_simple(clean_netraven_env_vars):
    os.environ["NETRAVEN_DATABASE__URL"] = "env_db_url"
    overrides = get_env_overrides()
    assert overrides == {"database": {"url": "env_db_url"}}

def test_get_env_overrides_nested(clean_netraven_env_vars):
    os.environ["NETRAVEN_WORKER__REDACTION__PATTERNS"] = "env_pattern"
    os.environ["NETRAVEN_WORKER__TIMEOUT"] = "30"
    overrides = get_env_overrides()
    assert overrides == {
        "worker": {
            "timeout": "30",
            "redaction": {"patterns": "env_pattern"}
        }
    }

def test_get_env_overrides_no_prefix():
    # Assuming no NETRAVEN_ vars are set by default test runner environment
    overrides = get_env_overrides()
    assert overrides == {}

# --- Tests for load_config --- 
def test_load_config_only_default(temp_config_dir, clean_netraven_env_vars):
    default_yaml = temp_config_dir / "default.yaml"
    default_yaml.write_text(yaml.dump({"logging": {"level": "INFO"}}))
    config = load_config(env="dev", config_dir=temp_config_dir)
    assert config == {"logging": {"level": "INFO"}}

def test_load_config_dev_over_default(temp_config_dir, clean_netraven_env_vars):
    default_yaml = temp_config_dir / "default.yaml"
    dev_yaml = temp_config_dir / "dev.yaml"
    default_yaml.write_text(yaml.dump({"logging": {"level": "INFO"}, "database": {"url": "default_url"}}))
    dev_yaml.write_text(yaml.dump({"logging": {"level": "DEBUG"}, "worker": {"threads": 5}}))
    config = load_config(env="dev", config_dir=temp_config_dir)
    assert config == {
        "logging": {"level": "DEBUG"}, # Dev overrides default
        "database": {"url": "default_url"}, # From default
        "worker": {"threads": 5} # From dev
    }

def test_load_config_env_var_override(temp_config_dir, clean_netraven_env_vars):
    dev_yaml = temp_config_dir / "dev.yaml"
    dev_yaml.write_text(yaml.dump({"database": {"url": "yaml_url"}}))
    os.environ["NETRAVEN_DATABASE__URL"] = "env_override_url"
    os.environ["NETRAVEN_NEW_KEY"] = "env_value"
    config = load_config(env="dev", config_dir=temp_config_dir)
    assert config["database"]["url"] == "env_override_url"
    assert config["new_key"] == "env_value"

def test_load_config_nonexistent_env_loads_default(temp_config_dir, clean_netraven_env_vars):
    default_yaml = temp_config_dir / "default.yaml"
    default_yaml.write_text(yaml.dump({"setting": "default_value"}))
    # No prod.yaml exists
    config = load_config(env="prod", config_dir=temp_config_dir)
    assert config == {"setting": "default_value"} # Should load default

def test_load_config_no_files(temp_config_dir, clean_netraven_env_vars):
    # No files created in temp_config_dir
    config = load_config(env="dev", config_dir=temp_config_dir)
    assert config == {}

def test_load_config_only_env_vars(temp_config_dir, clean_netraven_env_vars):
    # No files created
    os.environ["NETRAVEN_WORKER__TIMEOUT"] = "45"
    config = load_config(env="dev", config_dir=temp_config_dir)
    assert config == {"worker": {"timeout": "45"}}

@patch.dict(os.environ, {"NETRAVEN_ENV": "staging"}, clear=True)
def test_load_config_uses_netraven_env(temp_config_dir, clean_netraven_env_vars):
    staging_yaml = temp_config_dir / "staging.yaml"
    staging_yaml.write_text(yaml.dump({"mode": "staging"}))
    default_yaml = temp_config_dir / "default.yaml"
    default_yaml.write_text(yaml.dump({"mode": "default"}))
    
    config = load_config(config_dir=temp_config_dir) # env=None, should use NETRAVEN_ENV
    assert config == {"mode": "staging"}

@patch.dict(os.environ, {}, clear=True) # Ensure NETRAVEN_ENV is not set
def test_load_config_defaults_to_dev_env(temp_config_dir, clean_netraven_env_vars):
    dev_yaml = temp_config_dir / "dev.yaml"
    dev_yaml.write_text(yaml.dump({"mode": "dev"}))
    default_yaml = temp_config_dir / "default.yaml"
    default_yaml.write_text(yaml.dump({"mode": "default"}))
    
    config = load_config(config_dir=temp_config_dir) # env=None, NETRAVEN_ENV not set
    assert config == {"mode": "dev"}

# Example test for malformed YAML - adapt if needed
# def test_load_config_malformed_yaml(temp_config_dir, clean_netraven_env_vars):
#     bad_yaml = temp_config_dir / "dev.yaml"
#     bad_yaml.write_text("logging: level: DEBUG\n key: :invalid:")
#     with pytest.raises(yaml.YAMLError):
#           # Error might occur during loading, check loader logs/behavior
#           # Depending on implementation, it might log error and return partial/empty
#           load_config(env="dev", config_dir=temp_config_dir)
#           pass 
