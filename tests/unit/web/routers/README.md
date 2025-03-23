# Router Unit Tests

This directory contains unit tests for the API routers in the NetRaven application.

## Purpose

These tests verify the behavior of individual router endpoints, focusing on:

- Request validation
- Response formatting
- Permission checking
- Error handling

## Test Structure

Router tests should be organized by router module, with one test file per router:

- `test_auth.py` - Tests for the auth router
- `test_devices.py` - Tests for the devices router
- `test_backups.py` - Tests for the backups router
- etc.

## Test Guidelines

1. Mock all database interactions
2. Mock service calls where appropriate
3. Focus on router-specific functionality (not business logic)
4. Test all endpoints in the router
5. Test both success and error cases
6. Test permission boundaries 