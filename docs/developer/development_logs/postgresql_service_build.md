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