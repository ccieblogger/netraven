#!/bin/bash

set -e

COMMAND=${1:-install}

# Default values, consider sourcing from config or env
DB_USER=${DB_USER:-netraven}
DB_PASSWORD=${DB_PASSWORD:-netraven}
DB_NAME=${DB_NAME:-netraven}

if [[ $COMMAND == "install" ]]; then
  echo "🚀 Installing PostgreSQL 14 and setting up NetRaven database..."

  # Check if running in WSL and adjust apt source if necessary
  if grep -q Microsoft /proc/version; then
    echo "WSL detected. Ensuring correct apt sources for PostgreSQL..."
    # Add PostgreSQL's official GPG key
    sudo apt-get update && sudo apt-get install -y gnupg
    wget -qO - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg
    # Add PostgreSQL repo
    echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list > /dev/null
  fi

  sudo apt-get update
  # Install PostgreSQL server and client
  sudo apt-get install -y postgresql-14 postgresql-client-14

  # Ensure the service is running (start if not, enable for boot)
  sudo systemctl start postgresql
  sudo systemctl enable postgresql

  echo "Creating database user '$DB_USER' and database '$DB_NAME'..."
  # Use sudo -u postgres to execute commands as the postgres user
  sudo -u postgres psql <<EOF
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
      CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASSWORD';
      ALTER ROLE $DB_USER CREATEDB; -- Optional: Allow user to create DBs if needed
      RAISE NOTICE 'Role "$DB_USER" created.';
   ELSE
      RAISE NOTICE 'Role "$DB_USER" already exists. Ensuring password.';
      ALTER ROLE $DB_USER WITH PASSWORD '$DB_PASSWORD';
   END IF;
END
\$\$;

-- Check if DB exists, create if not, ensuring correct owner
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- If DB existed, ensure owner is correct (optional, might fail if user doesn't own it)
-- ALTER DATABASE $DB_NAME OWNER TO $DB_USER;

GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

EOF

  echo "✅ PostgreSQL 14 installed and NetRaven database '$DB_NAME' initialized for user '$DB_USER'."

elif [[ $COMMAND == "drop" ]]; then
  echo "🗑️ Dropping public schema from database '$DB_NAME'..."
  # Ensure the user running this has privileges, or run as postgres user
  # PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  sudo -u postgres psql -d $DB_NAME -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  echo "✅ Public schema reset in '$DB_NAME'."

elif [[ $COMMAND == "check" ]]; then
  echo "🔍 Testing database connection to '$DB_NAME' as user '$DB_USER'..."
  export PGPASSWORD=$DB_PASSWORD
  if psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null; then
    echo "✅ Connection successful."
  else
    echo "❌ Failed to connect to database '$DB_NAME' as '$DB_USER'."
    echo "   Hints: Check if PostgreSQL service is running (`systemctl status postgresql`)."
    echo "          Verify hostname, database name, user, and password."
    echo "          Check PostgreSQL logs (/var/log/postgresql/...)."
    exit 1
  fi
  unset PGPASSWORD

elif [[ $COMMAND == "refresh" ]]; then
  echo "♻️ Removing PostgreSQL and reinstalling..."
  sudo systemctl stop postgresql || true
  sudo apt-get remove --purge -y postgresql* postgresql-client*
  sudo rm -rf /var/lib/postgresql /etc/postgresql /var/log/postgresql
  sudo apt-get autoremove -y
  sudo apt-get autoclean
  sudo rm -f /etc/apt/sources.list.d/pgdg.list /usr/share/keyrings/postgresql-keyring.gpg
  echo "🧹 PostgreSQL removed. Reinstalling..."
  # Re-run the script with the install command
  exec "$0" install

else
  echo "Usage: $0 [install|drop|check|refresh]"
  echo "  install : Installs PostgreSQL 14, creates user/db."
  echo "  drop    : Drops and recreates the public schema in the database."
  echo "  check   : Tests the connection to the database."
  echo "  refresh : Purges PostgreSQL and runs install again (DANGEROUS)."
  exit 1