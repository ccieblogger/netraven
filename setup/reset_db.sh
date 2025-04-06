#!/bin/bash
# reset_db.sh
# Resets the NetRaven database by dropping all tables defined in the models.
# WARNING: THIS IS DESTRUCTIVE AND WILL DELETE ALL DATA IN THESE TABLES.
# Assumes it's run from the project root directory.

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Pipes fail if any command fails, not just the last one.
set -o pipefail

echo "*** WARNING: Database Table Drop ***"
echo "This script will attempt to DROP ALL TABLES defined in the SQLAlchemy models,"
echo "DELETING ALL ASSOCIATED DATA."
echo "Make sure the PostgreSQL server is running and accessible."
echo ""

# Define Virtual Environment Path
VENV_PATH="venv"

# Check if Virtual Environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at '$VENV_PATH'."
    echo "Please run the setup script (e.g., ./setup/setup_db.sh) first."
    exit 1
fi

# Check if dev_runner.py exists
if [ ! -f "dev_runner.py" ]; then
    echo "Error: dev_runner.py not found in the project root."
    exit 1
fi

# Define executable paths
PYTHON_EXEC="$VENV_PATH/bin/python"
# ALEMBIC_EXEC="$VENV_PATH/bin/alembic" # No longer needed for this script

# Confirmation Prompt (from dev_runner.py will also ask)
# It's good practice to have a script-level confirmation too.
read -p "Are you absolutely sure you want to drop all tables and delete all data? (yes/no): " confirmation
if [[ "$confirmation" != "yes" ]]; then
    echo "Table drop cancelled."
    exit 0
fi

echo "Proceeding with table drop via dev_runner.py..."

# Call dev_runner.py to drop the schema
# The dev_runner script itself has another confirmation prompt.
"$PYTHON_EXEC" dev_runner.py --drop-schema

# After dropping tables, Alembic history might be inconsistent.
# It's often good practice to stamp the DB as being at 'base' after a drop,
# though running setup_db.sh later will handle upgrading from base anyway.
# echo "Stamping Alembic history to 'base'..."
# "$ALEMBIC_EXEC" stamp base

echo "--- NetRaven Database Table Drop Attempt Complete ---"
echo "If confirmed in the prompt above, tables should have been dropped."
echo ""
echo "You can recreate the schema by running:"
echo "  ./setup/setup_db.sh"
echo ""

exit 0 