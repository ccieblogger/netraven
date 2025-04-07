#!/bin/bash

# Simple script to install and start Redis server for NetRaven development
# Based on scheduler_sot.md Appendix

set -e

echo "🚀 Installing Redis server..."

sudo apt-get update
sudo apt-get install -y redis-server

echo "Ensuring Redis service is enabled and started..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Optional: Check Redis status
echo "Checking Redis status:"
sudo systemctl status redis-server --no-pager || echo "Warning: Could not get Redis status, but installation attempted."

# Optional: Test connection
echo "Testing Redis connection with PING..."
if redis-cli ping; then
    echo "✅ Redis installed and running."
else
    echo "❌ Redis installed but PING command failed. Check Redis status and logs."
    exit 1
fi
