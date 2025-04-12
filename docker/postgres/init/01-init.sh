#!/bin/bash
set -e

# The PostgreSQL image automatically creates:
# - Database $POSTGRES_DB (netraven)
# - User $POSTGRES_USER (netraven) with password $POSTGRES_PASSWORD
# - Grants all privileges to the user for the database

# This script runs additional setup if needed
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  -- Add any additional database setup here if needed
  
  -- Ensure user has all necessary permissions
  ALTER USER $POSTGRES_USER WITH CREATEDB CREATEROLE;
  
  -- Create extensions if required
  CREATE EXTENSION IF NOT EXISTS "pg_trgm";
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOSQL

echo "PostgreSQL initialization complete" 