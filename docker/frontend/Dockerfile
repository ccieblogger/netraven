# ----------- Build Stage -----------
    FROM node:20-alpine AS build

    WORKDIR /app
    
    # Install dependencies
    COPY frontend/package*.json ./
    RUN npm ci
    RUN npm install dayjs
    
    # Copy application code
    COPY frontend/. .
    
    # Build the application (outputs to /app/dist)
    RUN npm run build
    
    # ----------- Production Stage -----------
    FROM nginx:alpine
    
    # Install additional utilities for security and monitoring (optional)
    RUN apk add --no-cache curl bash tzdata
    
    # Copy built static files from build stage
    COPY --from=build /app/dist /usr/share/nginx/html
    
    # Copy NGINX configuration files from docker/frontend/
    COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf
    COPY docker/frontend/nginx-security-headers.conf /etc/nginx/conf.d/security-headers.conf
    
    # Healthcheck script (optional, for Docker health monitoring)
    COPY docker/frontend/docker-healthcheck.sh /usr/local/bin/docker-healthcheck
    RUN chmod +x /usr/local/bin/docker-healthcheck
    
    # Expose HTTP port
    EXPOSE 80
    
    # Set up Docker healthcheck
    HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD ["/usr/local/bin/docker-healthcheck"]
    
    # Start NGINX in foreground
    CMD ["nginx", "-g", "daemon off;"]