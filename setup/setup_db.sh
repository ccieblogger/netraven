#!/bin/bash
# setup_db.sh
# Sets up the NetRaven database environment after PostgreSQL installation.
# Assumes it's run from the project root directory.

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Pipes fail if any command fails, not just the last one.
set -o pipefail

echo "--- Starting NetRaven Database Setup ---"

# Define Virtual Environment Path
VENV_PATH="venv"

# 1. Create/Verify Virtual Environment
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating Python virtual environment at '$VENV_PATH'..."
    python3 -m venv "$VENV_PATH"
    echo "Virtual environment created."
else
    echo "Virtual environment already exists at '$VENV_PATH'."
fi

# Activate Environment (for pip/alembic commands below)
# Using direct paths to executables for script robustness
PYTHON_EXEC="$VENV_PATH/bin/python"
PIP_EXEC="$VENV_PATH/bin/pip"
ALEMBIC_EXEC="$VENV_PATH/bin/alembic"

echo "Using Python from: $PYTHON_EXEC"

# 2. Install Dependencies
echo "Installing/updating Python dependencies from requirements.txt..."
"$PIP_EXEC" install -r requirements.txt
echo "Dependencies installed."

# 3. Apply Database Migrations
echo "Applying database migrations using Alembic..."
# This command brings the database schema to the latest version found in alembic/versions
"$ALEMBIC_EXEC" upgrade head
echo "Database migrations applied successfully."

echo "--- NetRaven Database Setup Complete ---"
echo ""
echo "You can now verify the setup by running:"
echo "  $PYTHON_EXEC dev_runner.py --db-check"
echo "  $VENV_PATH/bin/pytest"
echo ""

exit 0 