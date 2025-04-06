## NetRaven Device Communication Service: State of Technology (SOT)

### Executive Summary

This document defines the structure, responsibilities, and implementation plan for the `device_comm` service in NetRaven. The `device_comm` service is responsible for securely connecting to network devices, executing commands, capturing configurations, and forwarding results to the database and job logging system. It uses synchronous device communication tools within a threaded execution model, optimized for simplicity and observability.

### Core Responsibilities
- Execute device interactions on behalf of scheduled jobs
- Support vendor-specific CLI command execution using Netmiko
- Redact sensitive information from device output
- Write job and connection logs to the database
- Handle connection retries and error categorization
- Use threading to support limited concurrency (e.g., 5–10 devices per job)
- Retrieve and securely store backup configurations from network devices, ensuring version control and facilitating disaster recovery.

### Technology Stack
```yaml
git_integration: GitPython
language: Python 3.11+
device_library: Netmiko
execution_model: ThreadPoolExecutor (concurrent.futures)
api_framework: none (this service is invoked as a worker or CLI)
database_layer: SQLAlchemy (sync)
logging: structlog + JSON
unit_testing: pytest + unittest.mock
```

### Directory Structure
```
/netraven/
├── worker/
│   ├── __init__.py
│   ├── runner.py            # Job orchestration entrypoint
│   ├── dispatcher.py        # Parallel execution controller
│   ├── executor.py          # Device command executor logic
│   ├── redactor.py          # Output redaction utilities
│   ├── log_utils.py         # DB and file-based logging helpers
|   |── git_writer.py        # Commits the device configuration to a local Git repository
│   └── backends/
│       ├── __init__.py
│       └── netmiko_driver.py  # Netmiko CLI backend
```

### Configuration
- Located in: `/config/environments/dev.yaml`
```yaml
worker:
  thread_pool_size: 5
  connection_timeout: 15
  retry_attempts: 2
  retry_backoff: 2
  redaction:
    patterns:
      - "password"
      - "secret"
```

### Sample Job Flow
```
API → Scheduler → device_comm.runner.run_job(job_id)
→ Load devices and credentials from DB
→ Start thread pool with N devices
→ For each device:
   - Connect via Netmiko
   - Execute command(s)
   - Redact output
   - Log to job and connection log tables
→ Aggregate result status
→ Return to scheduler for status update
```

### Device Executor Logic (`executor.py`)
```python
from netraven.worker.backends.netmiko_driver import run_command
from netraven.worker.redactor import redact
from netraven.worker.log_utils import save_job_log, save_connection_log

def handle_device(device):
    result = {"device_id": device.id, "success": False, "error": None}
    try:
        raw_output = run_command(device)
        redacted = redact(raw_output)
        save_connection_log(device.id, job_id, redacted)
        save_job_log(device.id, job_id, "Command executed", success=True)
        result["success"] = True
        result["result"] = redacted
    except Exception as e:
        save_job_log(device.id, job_id, f"Error: {e}", success=False)
        result["error"] = str(e)
    return result
```

### Redaction Utility (`redactor.py`)
```python
def redact(output):
    lines = []
    for line in output.splitlines():
        if any(keyword in line.lower() for keyword in ["password", "secret"]):
            lines.append("[REDACTED LINE]")
        else:
            lines.append(line)
    return "\n".join(lines)
```

### Netmiko Driver (`netmiko_driver.py`)
```python
from netmiko import ConnectHandler

def run_command(device):
    connection = ConnectHandler(
        device_type=device.device_type,
        host=device.ip_address,
        username=device.username,
        password=device.password,
    )
    output = connection.send_command("show running-config")
    connection.disconnect()
    return output
```

### Logging Interface (`log_utils.py`)
```python
from netraven.db.session import get_db
from netraven.db.models import JobLog, ConnectionLog

def save_connection_log(device_id, job_id, log):
    db = next(get_db())
    entry = ConnectionLog(device_id=device_id, job_id=job_id, log=log)
    db.add(entry)
    db.commit()

def save_job_log(device_id, job_id, message, success):
    db = next(get_db())
    entry = JobLog(device_id=device_id, job_id=job_id, message=message, level="INFO" if success else "ERROR")
    db.add(entry)
    db.commit()
```

### Git Commit Logic (git_writer.py)
```python
import os
from git import Repo, GitCommandError

def commit_configuration_to_git(device_id, config_data, job_id, repo_path='/data/git-repo'):
    """
    Commits the device configuration to a local Git repository.

    Args:
        device_id (str): Unique identifier for the device (e.g., hostname or IP).
        config_data (str): The configuration data retrieved from the device.
        job_id (str): Identifier for the job that retrieved this configuration.
        repo_path (str): Path to the local Git repository.

    Returns:
        str: Commit hash if successful, None otherwise.
    """
    try:
        # Ensure the repository exists
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
            repo = Repo.init(repo_path)
        else:
            repo = Repo(repo_path)

        # Define the path for the configuration file
        config_file_path = os.path.join(repo_path, f"{device_id}_config.txt")

        # Write the configuration data to the file
        with open(config_file_path, 'w') as config_file:
            config_file.write(config_data)

        # Stage the file
        repo.index.add([config_file_path])

        # Create a commit message with metadata
        commit_message = f"Config backup for device {device_id} | Job ID: {job_id}"

        # Commit the changes
        commit = repo.index.commit(commit_message)

        return commit.hexsha

    except GitCommandError as git_err:
        print(f"Git error occurred: {git_err}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
```

### Dev Runner
`setup/dev_runner.py`
```python
import argparse
from netraven.worker.runner import run_job

parser = argparse.ArgumentParser()
parser.add_argument("job_id", type=int, help="Job ID to execute")
args = parser.parse_args()

run_job(args.job_id)
```

### Testing Examples
```python
from netraven.worker.executor import handle_device

def test_handle_device_success():
    device = DummyDevice(success_output="ok", raise_on=None)
    result = handle_device(device)
    assert result["success"] is True

def test_handle_device_failure():
    device = DummyDevice(success_output=None, raise_on=Exception("timeout"))
    result = handle_device(device)
    assert result["success"] is False
    assert "timeout" in result["error"]
```

### Packaging and Dependency Management

NetRaven is developed as a Python monorepo managed using [Poetry](https://python-poetry.org/). All services, including `device_comm`, are part of a unified workspace with shared dependencies and isolated service modules. This ensures maintainability, reproducibility, and ease of packaging and deployment.

#### Root-level `pyproject.toml`
```toml
[tool.poetry]
name = "netraven"
version = "0.1.0"
description = "NetRaven network configuration management system"
authors = ["Your Name <you@example.com>"]
packages = [
  { include = "netraven" }
]

[tool.poetry.dependencies]
python = "^3.11"
netmiko = "^4.0.0"
structlog = "^23.1.0"
sqlalchemy = "^2.0"
psycopg2 = "^2.9"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
```

#### Usage
```bash
# Install Poetry
pip install poetry

# Install all dependencies
poetry install

# Enter the environment
poetry shell
```

> 📁 `pyproject.toml` and `poetry.lock` live in the root `/` directory.
> 📁 Each service, like `/netraven/worker/`, is developed under the main namespace and imports as `netraven.worker.*`.

Run setup:
```bash
pip install poetry
poetry install
poetry shell
```

#### Alternative: `requirements.txt`
```
netmiko>=4.0
structlog
sqlalchemy>=2.0
psycopg2
```

Install manually:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Include either file in the `/setup/` directory, or root depending on packaging preference.

---
