# Nginx Container Source of Truth Documentation

## Overview
The Nginx container serves as the reverse proxy and web server for the NetRaven system. It manages HTTP traffic routing, load balancing, and provides a unified entry point for both the frontend UI and backend API services. The container is built on the official Nginx Alpine image and configured to handle routing, caching, and serving of the Vue.js SPA frontend application.

## Core Purpose
- Provide a unified entry point for the NetRaven application
- Route requests appropriately between frontend and API services
- Handle web serving optimizations including compression and caching
- Manage HTTP/HTTPS traffic and TLS termination when configured
- Provide health check endpoints for monitoring
- Support WebSocket connections for development and real-time features

## Architecture and Design
### Technical Stack
- **Base Image**: nginx:alpine
- **Configuration**: Custom Nginx configuration files for routing and optimization
- **Exposed Ports**: Port 80 (HTTP), configurable for 443 (HTTPS) when TLS is enabled

### Configuration Structure
The Nginx container uses several configuration files:
- `default.conf`: Primary configuration file defining server blocks and proxy settings
- `frontend-nginx.conf`: Frontend-specific configuration for the Vue.js SPA

## Routing Configuration
### Frontend Routing
- Routes all requests to the root path (`/`) to the frontend service
- Configures proxy headers for proper client IP and protocol forwarding
- Supports WebSocket connections for the development server

### API Routing
- Routes requests to `/api/*` paths to the backend API service
- Preserves headers for authentication and client information
- Includes a dedicated health check endpoint (`/api/health`)

## Performance Optimizations
- **Gzip Compression**: Enabled for text-based content types to reduce bandwidth usage
- **Static Asset Caching**: Long-term caching configured for static assets (.js, .css, images)
- **SPA Routing Support**: Configuration to handle single-page application client-side routing

## Security Features
- **Header Management**: Sets secure headers for proxied connections
- **TLS Support**: Can be configured for HTTPS with appropriate certificates
- **Connection Upgrade Support**: Properly manages connection upgrades for WebSockets

## Containerization Details
### Base Image
- Uses the lightweight nginx:alpine image for minimal attack surface and resource usage

### Build Process
- Simple build using the official Nginx Alpine image
- Copies custom configuration files into the container

### Security Measures
- Runs as the default Nginx user (non-root)
- Limited container capabilities

### Exposed Ports
- Port 80 (HTTP) exposed by default
- Can be configured to expose port 443 (HTTPS) when TLS is enabled

### Volume Mounts
None by default in the standard configuration, but can be configured to mount:
- SSL/TLS certificates
- Custom Nginx configuration files
- Static assets

### Health Checks
The container includes health check endpoints that can be used by orchestration systems:
- `/health` endpoint for frontend health checks
- `/api/health` endpoint for API service health checks

## Integration with NetRaven System
The Nginx container integrates with other NetRaven services:
- **Frontend service**: Proxies frontend requests and serves the Vue.js SPA
- **API service**: Routes API requests to the backend service
- **Network**: Operates on the shared netraven-network

## Deployment Configuration
In the Docker Compose configuration, the Nginx container is defined as:
```yaml
nginx:
  build:
    context: ./docker/nginx
    dockerfile: Dockerfile
  ports:
    - "80:80"
  depends_on:
    - api
    - frontend
  networks:
    - netraven-network
```

## Development and Production Differences
- In development environments, the container includes additional WebSocket support for hot reloading
- Production environments may include additional security configurations and TLS setup
- Health check endpoints are configured in both environments but may be more comprehensive in production

## Customization Options
The Nginx container can be customized by:
- Modifying the configuration files to change routing rules
- Adding SSL/TLS certificates for HTTPS support
- Adjusting caching and compression settings for optimal performance
- Adding custom error pages or redirects

## Future Considerations
- Enhanced TLS configuration with automatic certificate renewal
- HTTP/2 and HTTP/3 support for improved performance
- Advanced load balancing for multi-instance deployments
- Enhanced security headers and configuration 