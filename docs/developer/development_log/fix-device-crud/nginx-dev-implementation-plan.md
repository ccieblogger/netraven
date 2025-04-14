# Nginx Development Environment Integration Plan

## Overview

This document outlines the plan to introduce Nginx as a reverse proxy in the development environment to achieve parity with production and resolve API URL resolution issues encountered during the tag-based credential system implementation.

## Background

The NetRaven application currently uses:
- Vite dev server in development for frontend serving
- Direct API access in development
- Nginx in production as a unified proxy for both frontend and API

This mismatch has led to inconsistent behavior between environments, particularly with URL resolution for API requests, causing device CRUD operations to fail in development.

## Goals

1. Create environment parity between development and production
2. Resolve URL resolution issues with API requests
3. Provide a consistent approach to API URL construction in frontend code
4. Streamline the development workflow
5. Improve testing reliability

## Implementation Tasks

### 1. Nginx Configuration for Development

- Create a development-specific Nginx configuration based on production
- Configure locations for:
  - Static frontend assets
  - API requests
  - WebSocket connections (for HMR)
- Ensure proper header forwarding for development

```nginx
# Development-specific Nginx config (docker/nginx/nginx.dev.conf)
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    # Frontend proxy - Vite dev server
    location / {
        proxy_pass http://frontend:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for HMR
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://api:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
    }
}
```

### 2. Docker Compose Updates

- Add Nginx service to development docker-compose.yml
- Configure port mapping for Nginx (80:80)
- Update networking configuration
- Ensure proper service dependencies

```yaml
# Addition to docker-compose.yml
services:
  nginx:
    image: nginx:1.25
    container_name: netraven-nginx-dev
    ports:
      - "80:80"
    volumes:
      - ./docker/nginx/nginx.dev.conf:/etc/nginx/conf.d/default.conf
      - ./docker/nginx/security-headers.conf:/etc/nginx/conf.d/security-headers.conf
    depends_on:
      - frontend
      - api
    restart: unless-stopped
```

### 3. Frontend Configuration Updates

- Update Vite configuration to:
  - Remove proxy settings (no longer needed with Nginx)
  - Configure for internal port only (no external exposure)
  - Update HMR settings

```javascript
// vite.config.js updates
export default defineConfig({
  // ...existing config
  server: {
    host: '0.0.0.0', // Listen on all interfaces inside container
    port: 5173,
    strictPort: true,
    hmr: {
      clientPort: 80, // External port (through Nginx)
      host: 'localhost', // Host users will access
      protocol: 'ws'
    },
    watch: {
      usePolling: true,
      interval: 1000
    }
    // Remove proxy settings - handled by Nginx now
  }
})
```

### 4. API Service Standardization

- Standardize the frontend API service to consistently use `/api` prefix
- Remove special case handling and URL interception
- Update existing components to use the standardized approach

```javascript
// frontend/src/services/api.js
import axios from 'axios';
import { useAuthStore } from '../store/auth';

// Simple configuration with consistent base URL
const api = axios.create({
  baseURL: '/api', // Always use /api prefix
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Auth token handling
api.interceptors.request.use((config) => {
  const authStore = useAuthStore();
  const token = authStore.token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Simplified error handling
api.interceptors.response.use(
  response => response,
  error => {
    // Handle errors (auth, network, etc.)
    if (error.response?.status === 401) {
      const authStore = useAuthStore();
      authStore.logout();
    }
    return Promise.reject(error);
  }
);

export default api;
```

### 5. Updates to Docker Scripts and Documentation

- Update development environment scripts
- Create startup script with proper service order
- Document the new development workflow
- Update troubleshooting guide with common Nginx issues

## Implementation Steps

1. **Setup Phase**
   - Create development Nginx configuration in docker/nginx/
   - Update docker-compose.yml to include Nginx service

2. **Configuration Phase**
   - Modify Vite settings to work behind Nginx
   - Update frontend API service for consistent URL handling

3. **Testing Phase**
   - Test all CRUD operations through Nginx
   - Verify HMR functionality
   - Test all features that use API endpoints

4. **Documentation Phase**
   - Update development setup instructions
   - Document Nginx configuration choices
   - Add troubleshooting section for common issues

5. **Cleanup Phase**
   - Remove temporary URL handling workarounds
   - Update environment setup scripts
   - Ensure clean startup/shutdown process

## Testing Criteria

1. **API Functionality**
   - All API endpoints should be accessible through Nginx
   - URL resolution should work consistently for all HTTP methods

2. **HMR Functionality**
   - Hot Module Replacement should function properly
   - Frontend changes should reflect immediately

3. **Authentication Flow**
   - Login/logout should work through Nginx
   - Auth tokens should be properly passed

4. **Error Handling**
   - API errors should be properly transmitted through Nginx
   - Network errors should be handled gracefully

## Rollback Plan

If implementation issues arise:
1. Remove Nginx service from docker-compose.yml
2. Restore Vite proxy configuration
3. Return to direct API access with URL workarounds
4. Document issues encountered for future resolution

## Timeline

- Setup and Configuration: 3-4 hours
- Testing and Debugging: 2-3 hours
- Documentation and Cleanup: 2-3 hours
- Total: 7-10 hours 