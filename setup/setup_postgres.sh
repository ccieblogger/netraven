#!/bin/bash

set -e

COMMAND=${1:-install}

DB_USER=${DB_USER:-netraven}
DB_PASSWORD=${DB_PASSWORD:-netraven}
DB_NAME=${DB_NAME:-netraven}

# Install PostgreSQL 14
sudo apt update
sudo apt install -y wget gnupg lsb-release

# Add PostgreSQL's official GPG key
wget -qO - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /usr/share/keyrings/postgresql.gpg

# Add PostgreSQL repo
echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

sudo apt update
sudo apt install -y postgresql-14 postgresql-client-14

# Enable and start service
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create user and database
sudo -u postgres psql <<EOF
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
      CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASSWORD';
   END IF;
END
\$\$;

CREATE DATABASE $DB_NAME OWNER $DB_USER;
EOF

echo "✅ PostgreSQL 14 installed and NetRaven database initialized."

elif [[ $COMMAND == "drop" ]]; then
  echo "⚠ Dropping all tables from database '$DB_NAME'..."
  sudo -u postgres psql -d $DB_NAME -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  echo "✅ Schema reset."

elif [[ $COMMAND == "check" ]]; then
  echo "🔍 Testing database connection..."
  PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1" || echo "❌ Failed to connect to database"

elif [[ $COMMAND == "refresh" ]]; then
  echo "♻ Removing PostgreSQL and reinstalling..."
  sudo systemctl stop postgresql || true
  sudo apt remove --purge -y postgresql* postgresql-client*
  sudo rm -rf /var/lib/postgresql /etc/postgresql
  sudo apt autoremove -y
  echo "🧹 PostgreSQL removed. Reinstalling..."
  exec "$0" install

else
  echo "Usage: $0 [install|drop|check|refresh]"
  exit 1