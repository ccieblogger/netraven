#!/bin/bash
# Backup script for development database

# Set variables
BACKUP_DIR="./db_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/netraven_db_${TIMESTAMP}.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Get the database container name from docker-compose
DB_CONTAINER=$(docker-compose ps -q db)

# Backup the database
echo "Creating backup of database to $BACKUP_FILE..."
docker exec $DB_CONTAINER pg_dump -U postgres netraven > "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup created successfully: $BACKUP_FILE"
    echo "To restore, use: cat $BACKUP_FILE | docker exec -i \$(docker-compose ps -q db) psql -U postgres -d netraven"
else
    echo "Backup failed!"
    exit 1
fi 