# NetRaven Container Communication Fix - Implementation Plan

## Issue Analysis

After a thorough review of the NetRaven codebase and containerization setup, I've identified the following key issues with the communication between containerized services:

1. **Frontend-to-API Communication Issues**:
   - The frontend service is hard-coded to connect to `http://localhost:8000` in `frontend/src/services/api.js`
   - In containerized environments, services should communicate using container service names, not localhost
   - Each service has its own network namespace in Docker, so "localhost" refers to the container itself, not other containers

2. **Environment Configuration Inconsistencies**:
   - Inconsistent environment variable usage between development and production setups
   - CORS configuration includes container service names but frontend still uses hardcoded localhost

3. **Network Configuration and Service Discovery**:
   - No proper service discovery mechanism for dynamically connecting services
   - Docker networking not properly leveraged for inter-container communication

4. **API Gateway Configuration**:
   - Frontend Nginx configuration doesn't include proxy settings for API requests

## Implementation Plan

### Phase 1: Fix Frontend-to-API Communication

1. **Update API Base URL Configuration**:
   - Modify `frontend/src/services/api.js` to use environment variables for API URL
   - Ensure the API URL is properly passed to containers through build args and runtime environment variables

2. **Update Environment Variable Configuration**:
   - Ensure `.env` files contain proper API URLs for different environments
   - Update Vue environment handling to properly pass these variables to the frontend

### Phase 2: Update Docker Configuration

1. **Improve Docker Compose Network Configuration**:
   - Ensure proper network definition for service communication
   - Add explicit network definitions if needed

2. **Update Docker Build Process**:
   - Modify Docker build args to include proper API URLs
   - Ensure environment variables are properly passed to containers at build time

### Phase 3: Configure API Gateway and CORS

1. **Update Nginx Configuration**:
   - Add API proxy configuration to the frontend Nginx setup
   - Enable proxy path for frontend to communicate with API

2. **Refine CORS Configuration**:
   - Ensure CORS settings in the API allow connections from all relevant frontend origins
   - Test CORS configuration for both development and production environments

### Phase 4: Testing and Verification

1. **Test Inter-Container Communication**:
   - Verify API calls from frontend to backend are successful
   - Test with both development and production configurations

2. **Performance and Reliability Testing**:
   - Test under load conditions
   - Verify connection stability

## Detailed Changes Required

### 1. Frontend API Service Updates

```javascript
// frontend/src/services/api.js - Update API_BASE_URL configuration
// From:
const API_BASE_URL = 'http://localhost:8000'; // Force to use localhost:8000

// To:
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

### 2. Frontend Environment Configuration

```
# frontend/.env.development
VITE_API_URL=http://api:8000

# frontend/.env.production
VITE_API_URL=http://api:8000
```

### 3. Docker Compose Updates

```yaml
# docker-compose.yml - Update environment variables for frontend
services:
  frontend:
    environment:
      - NODE_ENV=development
      - VITE_API_URL=http://api:8000

# docker-compose.prod.yml - Update environment variables for frontend  
services:
  frontend:
    environment:
      - NODE_ENV=production
      - VITE_API_URL=http://api:8000
```

### 4. Nginx Configuration for API Proxy

```nginx
# frontend/nginx.conf - Add API proxy configuration
location /api/ {
    proxy_pass http://api:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 5. API CORS Configuration Update

```python
# netraven/api/main.py - Update CORS configuration
allow_origins = [
    # Local development
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Container service names
    "http://frontend:5173",
    "http://frontend:80",
    "http://netraven-frontend-dev:5173",
    "http://netraven-frontend-prod:80",
    # Host machine access to containers
    "http://localhost:80",
    "http://localhost:5173"
] 