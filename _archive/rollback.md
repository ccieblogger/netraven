# Implementation Plan: Remove UI Browser Testing Components

## Overview
This plan outlines the steps to remove browser-based UI testing from the NetRaven project while preserving all other testing capabilities. The focus is on surgical removal of Playwright-related components only.

## 1. Identify and Remove Test Dependencies

### A. Update test-requirements.txt
- Remove the following lines:
  ```
  pytest-playwright>=0.4.0
  playwright>=1.40.0
  ```
- Leave all other test dependencies intact

## 2. Clean Up Dockerfiles

### A. Modify Dockerfile.api
- Remove Playwright browser installation section:
  ```
  # Install packages needed for Playwright
  apt-get update && \
  apt-get install -y --no-install-recommends \
      wget \
      gnupg \
      ca-certificates \
      fonts-noto-color-emoji \
      libnss3 \
      libnspr4 \
      libatk1.0-0 \
      libatk-bridge2.0-0 \
      libcups2 \
      libdrm2 \
      libxkbcommon0 \
      libxcomposite1 \
      libxdamage1 \
      libxfixes3 \
      libxrandr2 \
      libgbm1 \
      libasound2 \
      libpango-1.0-0 \
      libcairo2 && \
  # Create specific directory for Playwright browsers
  mkdir -p /app/.playwright-browsers && \
  chmod -R 777 /app/.playwright-browsers && \
  # Install Playwright browsers with explicit path
  PLAYWRIGHT_BROWSERS_PATH=/app/.playwright-browsers python -m playwright install --with-deps chromium && \
  # Make sure browser is properly installed
  echo "Verifying browser installation..." && \
  ls -la /app/.playwright-browsers
  ```

- Remove Playwright environment variable:
  ```
  # Add Playwright browser path
  ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright-browsers
  ```

## 3. Remove UI Test Code

### A. Clean up test directory structure
- Remove browser-specific test fixtures in `tests/ui/conftest.py`:
  - Remove the `playwright_browser` fixture
  - Remove the `page` fixture 
  - Remove the `authenticated_page` fixture
  - Leave other non-browser UI testing code intact

### B. Remove UI test flow files that depend on browser testing
- Remove or modify browser-dependent tests in:
  - `tests/ui/test_flows/test_login.py`
  - Any other files that explicitly use Playwright browser functionality

### C. Update main conftest.py
- Remove Playwright-specific fixtures in `tests/conftest.py`:
  - Remove the `playwright_browser` fixture
  - Remove the `page` fixture
  - Remove the `authenticated_page` fixture
  - Leave all database, token, and API testing fixtures intact

## 4. Update Documentation

### A. Modify UI testing section in documentation
- Update any references to browser-based testing in docs/testing.md
- Keep all other testing documentation intact

## 5. Clean Up CI/CD Configuration (if applicable)

### A. Update CI workflow files
- Remove Playwright installation steps from `.github/workflows/test.yml`
- Remove browser-specific CI job configurations

## 6. Rebuild Test Environment

### A. Rebuild with updated configuration
- Run the following commands to rebuild without browser testing components:
  ```bash
  docker-compose down
  ./scripts/build_test_env.sh
  ```

## 7. Verification Steps

### A. Verify other tests still function
- Run unit tests: `docker exec netraven-api-1 python -m pytest tests/unit`
- Run integration tests: `docker exec netraven-api-1 python -m pytest tests/integration`
- Ensure no Playwright-related errors appear

## 8. Rollback Plan

In case of issues, we can restore the browser testing capability by:
1. Restoring the test-requirements.txt entries
2. Restoring the Dockerfile.api Playwright installation section
3. Rebuilding the test environment 