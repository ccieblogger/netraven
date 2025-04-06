#!/bin/bash
set -e

# Fully remove old PostgreSQL installation if needed
sudo service postgresql stop || true
sudo apt purge postgresql-14 postgresql-contrib -y || true
sudo apt autoremove --purge -y || true
sudo rm -rf /var/lib/postgresql /etc/postgresql /etc/postgresql-common /var/log/postgresql || true

# Reinstall PostgreSQL
sudo apt update
sudo apt install postgresql-14 postgresql-contrib -y

# Start PostgreSQL
sudo service postgresql start

# Create NetRaven database and user
sudo -u postgres psql <<EOF
DROP DATABASE IF EXISTS netraven;
DROP ROLE IF EXISTS netraven;
CREATE ROLE netraven WITH LOGIN PASSWORD 'netraven';
CREATE DATABASE netraven OWNER netraven;
GRANT ALL PRIVILEGES ON DATABASE netraven TO netraven;
EOF

# Configure PostgreSQL to use password authentication
PG_HBA=$(find /etc/postgresql -name pg_hba.conf | head -n 1)
sudo sed -i "s/^local\s\+all\s\+all\s\+peer/local all all md5/" "$PG_HBA"
sudo sed -i "s/^local\s\+all\s\+postgres\s\+peer/local all postgres md5/" "$PG_HBA"

# Restart PostgreSQL to apply changes
sudo service postgresql restart

echo "✅ PostgreSQL setup complete."
echo "Connection URL: postgresql+asyncpg://netraven:netraven@localhost:5432/netraven"

echo "to test database: 'psql -U netraven -h localhost -d netraven -W' password = netraven"