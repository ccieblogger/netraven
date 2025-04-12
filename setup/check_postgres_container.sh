#!/bin/bash

# NetRaven PostgreSQL Container Test Script
# This script tests the connection to the containerized PostgreSQL database

set -e  # Exit on any errors

# Directory paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}   PostgreSQL Container Connection Test   ${NC}"
echo -e "${GREEN}==========================================${NC}"

# Database connection parameters
DB_HOST="postgres"
DB_USER="netraven"
DB_PASSWORD="netraven"
DB_NAME="netraven"
DB_PORT="5432"

# Check if the PostgreSQL container is running
echo -e "\n${YELLOW}Checking if PostgreSQL container is running...${NC}"
if docker ps | grep -q netraven-postgres; then
    echo -e "${GREEN}✓ PostgreSQL container is running.${NC}"
else
    echo -e "${RED}✗ PostgreSQL container is not running.${NC}"
    echo -e "${YELLOW}Starting PostgreSQL container...${NC}"
    
    # Try to start the container
    if docker-compose up -d postgres; then
        echo -e "${GREEN}✓ PostgreSQL container started successfully.${NC}"
        
        # Wait for container to be ready
        echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
        sleep 5
    else
        echo -e "${RED}✗ Failed to start PostgreSQL container. Check docker-compose configuration.${NC}"
        exit 1
    fi
fi

# Check if container is healthy
echo -e "\n${YELLOW}Checking PostgreSQL container health...${NC}"
if docker exec netraven-postgres pg_isready -U $DB_USER > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL server is accepting connections.${NC}"
else
    echo -e "${RED}✗ PostgreSQL server is not accepting connections.${NC}"
    echo -e "${YELLOW}Container may still be initializing. Try again in a moment.${NC}"
    exit 1
fi

# Test database connection and existence of database
echo -e "\n${YELLOW}Testing connection to database '$DB_NAME'...${NC}"
if docker exec netraven-postgres psql -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Successfully connected to database '$DB_NAME'.${NC}"
else
    echo -e "${RED}✗ Failed to connect to database '$DB_NAME'.${NC}"
    
    # Check if database exists
    echo -e "${YELLOW}Checking if database '$DB_NAME' exists...${NC}"
    if docker exec netraven-postgres psql -U $DB_USER -c "SELECT datname FROM pg_database WHERE datname='$DB_NAME'" | grep -q $DB_NAME; then
        echo -e "${GREEN}✓ Database '$DB_NAME' exists, but connection failed.${NC}"
        echo -e "${RED}  Check connection parameters or database permissions.${NC}"
    else
        echo -e "${RED}✗ Database '$DB_NAME' does not exist.${NC}"
        echo -e "${YELLOW}  Creating database '$DB_NAME'...${NC}"
        
        if docker exec netraven-postgres psql -U $DB_USER -c "CREATE DATABASE $DB_NAME" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Database '$DB_NAME' created successfully.${NC}"
        else
            echo -e "${RED}✗ Failed to create database '$DB_NAME'.${NC}"
            exit 1
        fi
    fi
fi

# Test schema existence by checking for a table
echo -e "\n${YELLOW}Checking database schema...${NC}"
if docker exec netraven-postgres psql -U $DB_USER -d $DB_NAME -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')" | grep -q t; then
    echo -e "${GREEN}✓ Schema appears to be set up (users table exists).${NC}"
else
    echo -e "${YELLOW}⚠ Schema may not be initialized (users table not found).${NC}"
    echo -e "${YELLOW}  Run database migrations or schema creation with:${NC}"
    echo -e "${YELLOW}  poetry run python \"$ROOT_DIR/setup/dev_runner.py\" --create-schema${NC}"
fi

# Test a query to verify database functionality
echo -e "\n${YELLOW}Testing query execution...${NC}"
if docker exec netraven-postgres psql -U $DB_USER -d $DB_NAME -c "SELECT current_database(), current_user, version()" | grep -q $DB_NAME; then
    echo -e "${GREEN}✓ Query execution successful.${NC}"
else
    echo -e "${RED}✗ Query execution failed.${NC}"
    exit 1
fi

# Print summary
echo -e "\n${GREEN}==========================================${NC}"
echo -e "${GREEN}   PostgreSQL Container Test Complete      ${NC}"
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}✓ Container is running${NC}"
echo -e "${GREEN}✓ Server is accepting connections${NC}"
echo -e "${GREEN}✓ Database '$DB_NAME' exists${NC}"
echo -e "${GREEN}✓ Query execution works${NC}"
echo -e "${GREEN}==========================================${NC}"

exit 0 