# NetRaven Unit Tests

This directory contains unit tests for the NetRaven application. Unit tests focus on testing individual components in isolation.

## Documentation

The testing documentation has been moved to the central documentation directory:

**[Testing Guide](../../docs/guides/developer/testing.md)**

Please refer to this guide for complete information on:
- Writing tests
- Running tests
- Test fixtures
- Mocking
- Best practices

## Quick Reference

For quick reference:

```bash
# Run all unit tests
pytest tests/unit/

# Run tests for a specific component
pytest tests/unit/core/
pytest tests/unit/routers/
pytest tests/unit/web/

# Run a specific test file
pytest tests/unit/core/test_auth.py

# Run tests with coverage report
pytest tests/unit/ --cov=netraven
``` 