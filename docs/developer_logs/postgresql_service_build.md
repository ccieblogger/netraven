# PostgreSQL Service Build - Development Log

**Date:** $(date +'%Y-%m-%d %H:%M:%S')

**Developer:** Gemini

**Goal:** Build the PostgreSQL service component for NetRaven as defined in `docs/source_of_truth/postgresql_sot.md`.

## Log Entries

*   **$(date +'%Y-%m-%d %H:%M:%S')**: Initiated build process.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Attempted `alembic init` but realized dependencies were missing and Poetry was not configured.
    *   **Insight:** The project setup deviates from the `architecture_sot.md` which specifies Poetry. No `pyproject.toml` or `requirements.txt` found.
    *   **Decision:** Proceed with setting up Poetry as per SOT.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Attempted `poetry init` but `poetry` command was not found.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Installed Poetry using `sudo apt install python3-poetry` after user confirmation.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Initialized Poetry project (`poetry init --no-interaction`), creating `pyproject.toml`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Added dependencies (`sqlalchemy[mypy]`, `alembic`, `psycopg2-binary`) using `poetry add ...`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created base directory structure (`netraven/db/`, `netraven/db/models/`, `config/environments/`).
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `netraven/db/base.py` with declarative base.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `netraven/db/session.py` with engine and session setup.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `config/environments/dev.yaml` with database URL.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Initialized Alembic (`alembic init alembic`).
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Configured `alembic.ini` with the correct `sqlalchemy.url`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Configured `alembic/env.py` to use metadata from `netraven.db.base.Base`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Started Phase 2: Define Database Models.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `netraven/db/models/tag.py` with `Tag` model and association tables.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `netraven/db/models/device.py` with `Device` model.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `netraven/db/models/device_config.py` with `DeviceConfiguration` model.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `netraven/db/models/credential.py` with `Credential` model (noted encryption TODO).
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `netraven/db/models/job.py` with `Job` model.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `netraven/db/models/job_log.py` with `JobLog` model and `LogLevel` enum.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `netraven/db/models/system_setting.py` with `SystemSetting` model.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `netraven/db/models/connection_log.py` with `ConnectionLog` model.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Imported all models into `netraven/db/models/__init__.py`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Started Phase 3: Database Migrations.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Generated initial migration (902c6a45cbf5). **Failed:** Migration script was empty.
    *   **Troubleshooting:** Realized models were not imported *before* `Base.metadata` was accessed in `alembic/env.py`.
    *   **Fix:** Added `import netraven.db.models` to `alembic/env.py` before `target_metadata = Base.metadata`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Regenerated migration. **Failed:** `sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved...` in `DeviceConfiguration` model.
    *   **Troubleshooting:** Identified column name conflict.
    *   **Fix:** Renamed `metadata` column to `config_metadata` in `netraven/db/models/device_config.py`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Regenerated migration (a3992da91329). **Success:** Script correctly contained table/index creation.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Applied migration `a3992da91329` using `alembic upgrade head`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Started Phase 4: Development Utilities and Testing.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `setup/dev_runner.py` script for DB helper commands.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `setup/setup_postgres.sh` script for PostgreSQL installation/management.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Made `setup/setup_postgres.sh` executable.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Attempted to add `pytest` as dev dependency (`--group dev`). **Failed:** Installed Poetry version (1.1.12) doesn't support groups.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Added `pytest` as a regular dependency using `poetry add pytest`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Created `tests/test_db_connection.py` with basic connection tests.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Attempted to run `pytest`. **Failed:** `ModuleNotFoundError: No module named 'netraven'`.
    *   **Troubleshooting:** Pytest couldn't find the source module because the package wasn't installed.
    *   **Fix:** Installed the project in editable mode using `pip install -e .`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Ran `pytest -v`. **Success:** Both connection tests passed.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Started Phase 5: Documentation and Refinement.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Added docstrings to all SQLAlchemy models in `netraven/db/models/`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Added docstring to `get_db` function in `netraven/db/session.py`.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Performed code review against project principles. Code adheres to guidelines.
*   **$(date +'%Y-%m-%d %H:%M:%S')**: Finalizing development log. 