#!/bin/bash
#
# PostgreSQL Backup Script for NetRaven
#
# This script creates a backup of the PostgreSQL database and stores it
# in the backup volume mounted to the PostgreSQL container.
#

# Configuration
BACKUP_DIR="/backups"
DB_NAME="${POSTGRES_DB:-netraven}"
DB_USER="${POSTGRES_USER:-netraven}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:-netraven}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Ensure backup directory exists
mkdir -p ${BACKUP_DIR}

echo "Creating backup of ${DB_NAME} database to ${BACKUP_FILE}..."

# Set PGPASSWORD environment variable for authentication
export PGPASSWORD="${DB_PASSWORD}"

# Create backup
pg_dump -h ${DB_HOST} -U ${DB_USER} ${DB_NAME} | gzip > ${BACKUP_FILE}

# Unset PGPASSWORD for security
unset PGPASSWORD

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup completed successfully"
    echo "Backup file: ${BACKUP_FILE}"
    
    # List existing backups
    echo "Available backups:"
    ls -lh ${BACKUP_DIR}
    
    # Calculate total backup size
    TOTAL_SIZE=$(du -sh ${BACKUP_DIR} | cut -f1)
    echo "Total backup size: ${TOTAL_SIZE}"
    
    # Cleanup old backups (keep last 7 days)
    find ${BACKUP_DIR} -name "${DB_NAME}_*.sql.gz" -type f -mtime +7 -delete
    echo "Cleaned up backups older than 7 days"
    
    exit 0
else
    echo "Backup failed"
    exit 1
fi 