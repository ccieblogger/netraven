# NetRaven Test Directory Map

This document provides a map of the testing structure across the NetRaven project to help developers locate and understand the various test components.

## Overview

The NetRaven project has two main locations for test-related files:

1. `/tests` - The main pytest test suite
2. `/scripts/tests` - Standalone test scripts for development and debugging

## Main Test Suite Structure

```
/tests/
├── conftest.py               # Shared test fixtures and configuration
├── __init__.py               # Package initialization
├── README.md                 # Test suite documentation
│
├── unit/                     # Unit tests for individual components
│   ├── core/                 # Core functionality unit tests
│   ├── routers/              # API router unit tests
│   ├── web/                  # Web components unit tests
│   └── README.md             # Unit test documentation
│
├── integration/              # Integration tests
│   ├── test_api_*.py         # API integration tests
│   ├── test_*_integration.py # Component integration tests
│   └── README.md             # Integration test documentation
│
├── ci/                       # CI-related test configurations
│
├── core/                     # Tests for core system functionality
│
├── mock/                     # Mock objects and data for testing
│
└── utils/                    # Test utilities and helpers
```

## Test Scripts Structure

```
/scripts/tests/
├── README.md                 # Documentation for test scripts
│
├── test_gateway*.py          # Gateway-related test scripts
├── test_device*.py           # Device-related test scripts
├── test_netmiko*.py          # NetMiko-related test scripts
├── test_log*.py              # Logging-related test scripts
└── test_*.py                 # Other standalone test scripts
```

## Other Test-Related Locations

```
/test-artifacts/              # Generated files during testing
```

## Running Tests

### Main Test Suite

The main test suite is organized for running with pytest:

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_specific_feature.py
```

### Test Scripts

Test scripts can be run directly with Python:

```bash
# Run a specific test script
python scripts/tests/test_specific_script.py
```

## Test Documentation

Additional documentation on testing:

- [Testing Guide](testing.md) - Comprehensive guide to testing practices
- [Integration Testing](integration_testing.md) - Guide to writing integration tests
- [Unit Testing](unit_testing.md) - Guide to writing unit tests

## Relationships Between Test Types

```
┌───────────────────┐     ┌─────────────────────┐     ┌───────────────────┐
│                   │     │                     │     │                   │
│    Unit Tests     │────►│ Integration Tests   │────►│  Test Scripts     │
│  (tests/unit/)    │     │ (tests/integration/)│     │ (scripts/tests/)  │
│                   │     │                     │     │                   │
└───────────────────┘     └─────────────────────┘     └───────────────────┘
       │                           │                          │
       │ Tests individual          │ Tests interactions       │ Provides ad-hoc
       │ components                │ between components       │ and debugging tests
       ▼                           ▼                          ▼
```

This map provides a high-level view of where to find different types of tests in the project and how they relate to each other. 