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

*This section will be populated with common database troubleshooting steps.*

## Docker Issues

*This section will be populated with common Docker deployment troubleshooting steps.* 