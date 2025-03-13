# NetRaven Troubleshooting Guide

This guide provides solutions to common issues you might encounter when working with NetRaven, as well as instructions for verifying that different components are working correctly.

## Table of Contents

- [Authentication Issues](#authentication-issues)
  - [Creating an Admin User](#creating-an-admin-user)
  - [Testing Authentication](#testing-authentication)
  - [Using Authentication Tokens](#using-authentication-tokens)
- [API Issues](#api-issues)
- [Database Issues](#database-issues)
- [Docker Issues](#docker-issues)

## Authentication Issues

### Creating an Admin User

If you're having trouble logging in or need to reset admin credentials, you can use the built-in script to create or update the admin user:

```bash
# Create a new admin user with default credentials
python3 scripts/create_admin_user.py

# Update an existing admin user (use --force flag)
python3 scripts/create_admin_user.py --force

# Specify custom credentials
python3 scripts/create_admin_user.py --username myadmin --password mysecretpw --email admin@example.com --force
```

By default, this creates an admin user with these credentials:
- Username: `admin`
- Password: `adminpassword`
- Email: `admin@example.com`

### Testing Authentication

To verify that authentication is working correctly, you can use curl to test the login endpoint:

```bash
# Attempt to login with admin credentials
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=adminpassword" \
  http://localhost:8000/api/auth/token
```

A successful response should look like:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

If you get `{"detail":"Incorrect username or password"}`, check that:
1. You've created an admin user using the script above
2. The database file exists and is properly configured
3. You're using the correct credentials

### Using Authentication Tokens

Once you have a token, you can use it to access protected endpoints:

```bash
# Store the token in a variable
TOKEN=$(curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=adminpassword" \
  http://localhost:8000/api/auth/token | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//') 

# Use the token to get user information
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/users/me

# Use the token to access devices
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/devices

# Use the token to access backups
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/backups
```

If you get `{"detail":"Could not validate credentials"}`, the token might be:
1. Expired (tokens have a default expiration of 24 hours)
2. Invalid or malformed
3. Missing the "Bearer" prefix

## API Issues

*This section will be populated with common API troubleshooting steps.*

## Database Issues

### PostgreSQL Connection Issues

If you're having trouble connecting to the PostgreSQL database:

```bash
# Check if the PostgreSQL container is running
docker ps | grep postgres

# Check PostgreSQL logs for errors
docker logs netraven-postgres-1

# Test the PostgreSQL connection directly
docker exec -it netraven-postgres-1 psql -U netraven -d netraven -c "SELECT 1"
```

If the connection fails, check:
1. The PostgreSQL container is running (`docker compose ps`)
2. The PostgreSQL credentials in the `config.yml` file match those in `docker-compose.yml`
3. The `DATABASE_URL` environment variable in the API service configuration
4. Network connectivity between containers (they should be on the same Docker network)

### Data Persistence Issues

To verify data is being properly persisted:

```bash
# List all devices directly from the database
docker exec -it netraven-postgres-1 psql -U netraven -d netraven -c "SELECT hostname, ip_address, device_type FROM netraven.devices"

# Compare with API response
curl -s -X GET http://localhost:8000/api/devices -H "Authorization: Bearer $TOKEN" | jq
```

If the API shows different data than the database:
1. The API might be using demo/mock data instead of the real database
2. The API might be using a different database than expected
3. Caching issues might be present (restart the API container)

### Demo Mode vs Real Database

NetRaven may use demo mode for testing, which doesn't persist changes to the database. To verify you're using the real database:

```bash
# Add a device via the API
curl -s -X POST http://localhost:8000/api/devices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hostname": "test-device", "device_type": "cisco_ios", "ip_address": "192.168.1.100", "description": "Test Device", "port": 22, "username": "admin", "password": "test123"}' | jq

# Check if it appears in the database
docker exec -it netraven-postgres-1 psql -U netraven -d netraven -c "SELECT hostname, ip_address FROM netraven.devices WHERE hostname='test-device'"

# Update the device via the API
DEVICE_ID=$(curl -s -X GET http://localhost:8000/api/devices -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.hostname=="test-device") | .id')
curl -s -X PUT http://localhost:8000/api/devices/$DEVICE_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hostname": "test-device-updated", "device_type": "cisco_ios", "ip_address": "192.168.1.100", "description": "Updated Test Device", "port": 22}' | jq

# Check if the update appears in the database
docker exec -it netraven-postgres-1 psql -U netraven -d netraven -c "SELECT hostname, description FROM netraven.devices WHERE ip_address='192.168.1.100'"
```

If changes via the API don't appear in the database, check:
1. The router implementation in `netraven/web/routers/devices.py` for hardcoded demo data
2. The database connection configuration in `netraven/web/database.py`
3. That you're restarting the API container after making code changes

### Database Schema and Migration Issues

To check the database schema:

```bash
# List all tables in the database
docker exec -it netraven-postgres-1 psql -U netraven -d netraven -c "\dt netraven.*"

# Examine a specific table's schema
docker exec -it netraven-postgres-1 psql -U netraven -d netraven -c "\d netraven.devices"
```

If tables are missing:
1. Verify the initialization SQL script is being executed
2. Check the logs for database initialization errors
3. Restart the application and check logs for database model registration issues

### PostgreSQL Configuration Issues

To verify PostgreSQL extensions and configuration:

```bash
# Check installed extensions
docker exec -it netraven-postgres-1 psql -U netraven -d netraven -c "\dx"

# Check database schemas
docker exec -it netraven-postgres-1 psql -U netraven -d netraven -c "\dn"

# Check PostgreSQL version
docker exec -it netraven-postgres-1 psql -U netraven -d netraven -c "SELECT version()"
```

Make sure the required extensions (uuid-ossp, pgcrypto) are installed.

### Reset Database (if needed)

To reset the database and start fresh:

```bash
# Stop all containers
docker compose down

# Remove the PostgreSQL volume
docker volume rm netraven_postgres_data

# Start the containers again
docker compose up -d
```

This will fully reset the database, so use with caution!

## Docker Issues

*This section will be populated with common Docker deployment troubleshooting steps.* 