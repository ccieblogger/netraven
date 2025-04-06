import pytest
import os
from unittest.mock import patch

# Function to test
from netraven.config.loader import load_config, CONFIG_DIR, DEFAULT_ENV

# Ensure the test config file exists for the test to run
# This assumes dev.yaml is correctly populated based on previous steps
TEST_CONFIG_FILE = os.path.join(CONFIG_DIR, f"{DEFAULT_ENV}.yaml")

@pytest.fixture(autouse=True)
def ensure_test_config_exists():
    """Checks if the config file exists before running tests in this module."""
    if not os.path.exists(TEST_CONFIG_FILE):
        pytest.skip(f"Test config file not found: {TEST_CONFIG_FILE}")

@pytest.fixture
def clean_env_vars():
    """Temporarily remove relevant env vars and restore them after test."""
    original_app_env = os.environ.pop('APP_ENV', None)
    original_db_url = os.environ.pop('DATABASE_URL', None)
    yield
    if original_app_env is not None:
        os.environ['APP_ENV'] = original_app_env
    if original_db_url is not None:
        os.environ['DATABASE_URL'] = original_db_url

def test_load_config_default_env(clean_env_vars):
    """Test loading configuration with default environment (dev)."""
    config = load_config() # No env specified, no APP_ENV set
    assert isinstance(config, dict)
    # Check for sections added in previous step
    assert "database" in config
    assert "url" in config["database"]
    assert "logging" in config
    assert "worker" in config
    assert "thread_pool_size" in config["worker"]
    assert "git_repo_path" in config["worker"]
    assert "retry_attempts" in config["worker"]
    assert "redaction" in config["worker"]
    assert "patterns" in config["worker"]["redaction"]
    assert isinstance(config["worker"]["redaction"]["patterns"], list)

@patch.dict(os.environ, {"APP_ENV": "nonexistent"})
def test_load_config_nonexistent_env(clean_env_vars):
    """Test loading configuration with an environment that has no file."""
    with pytest.raises(FileNotFoundError):
        load_config()

@patch.dict(os.environ, {"DATABASE_URL": "env_override_db_url"})
def test_load_config_db_url_override(clean_env_vars):
    """Test overriding database.url via DATABASE_URL environment variable."""
    config = load_config() # Load default env (dev)
    assert config["database"]["url"] == "env_override_db_url"

# Potential test for malformed YAML (requires creating a temporary bad file)
# def test_load_config_malformed_yaml(tmp_path):
#     bad_yaml_content = "database: url: \n bad_indent"
#     env_name = "malformed"
#     config_dir = tmp_path / CONFIG_DIR
#     config_dir.mkdir(parents=True)
#     bad_file = config_dir / f"{env_name}.yaml"
#     bad_file.write_text(bad_yaml_content)
#     
#     # Temporarily patch CONFIG_DIR to use tmp_path
#     with patch('netraven.config.loader.CONFIG_DIR', str(tmp_path / CONFIG_DIR)):
#         with pytest.raises(yaml.YAMLError):
#             load_config(env=env_name)
