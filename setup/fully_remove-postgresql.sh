#!/bin/bash

# Stop the PostgreSQL service
echo "Stopping PostgreSQL service..."
sudo systemctl stop postgresql

# Purge PostgreSQL packages
echo "Removing PostgreSQL packages..."
sudo apt-get --purge remove -y postgresql*

# Remove PostgreSQL directories
echo "Deleting PostgreSQL directories..."
sudo rm -rf /var/lib/postgresql/
sudo rm -rf /var/log/postgresql/
sudo rm -rf /etc/postgresql/

# Remove the PostgreSQL user
echo "Removing PostgreSQL user..."
sudo deluser --remove-home postgres

# Verify uninstallation
echo "Verifying PostgreSQL uninstallation..."
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL has been successfully uninstalled!"
else
    echo "PostgreSQL is still installed. Please check manually."
fi

exit 0