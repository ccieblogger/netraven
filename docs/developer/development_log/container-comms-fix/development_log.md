# NetRaven Container Communication Fix - Development Log

## Initial Analysis (2023-06-14)

Today I performed a comprehensive analysis of the NetRaven containerized services to identify communication issues between them. The main problems identified were:

1. Hard-coded API URL in the frontend service
2. Improper environment variable configuration
3. Incorrect network configuration for container-to-container communication
4. Missing API proxy in the Nginx configuration

I've created a detailed implementation plan that outlines the steps needed to fix these issues, which can be found in `implementation_plan.md` in this directory.

## Implementation (2023-06-14)

### Phase 1: Fixed Frontend-to-API Communication

1. Updated `frontend/src/services/api.js` to use environment variables:
   - Changed hard-coded `API_BASE_URL` to use `import.meta.env.VITE_API_URL` with fallback
   - This ensures the frontend can dynamically connect to the proper API endpoint based on environment

2. Created environment variable files for frontend:
   - Added `frontend/.env.development` with `VITE_API_URL=http://api:8000`
   - Added `frontend/.env.production` with `VITE_API_URL=http://api:8000`

### Phase 2: Updated Docker Configuration

1. Updated docker-compose files:
   - Modified `docker-compose.yml` to set `VITE_API_URL=http://api:8000` for development
   - Modified `docker-compose.prod.yml` to set `VITE_API_URL=http://api:8000` for production
   - Using container service names allows for proper inter-container communication

### Phase 3: Configured API Gateway and CORS

1. Enhanced Nginx configuration:
   - Added API proxy configuration to `frontend/nginx.conf`
   - Added proxy settings to route `/api/` requests to the API service
   - Set appropriate headers for proxying

2. Updated CORS configuration:
   - Refined CORS settings in `netraven/api/main.py`
   - Organized allowed origins with clear comments
   - Ensured all relevant container hostnames and names are included

## Browser Resolution Fix (2023-06-15)

After initial implementation, we discovered a name resolution issue in the browser. While container-to-container communication can use service names (`http://api:8000`), browsers running on the host machine cannot resolve these names. 

### Updates Made:

1. Changed API URL in environment files:
   - Modified `frontend/.env.development` to use `VITE_API_URL=http://localhost:8000`
   - Modified `frontend/.env.production` to use `VITE_API_URL=http://localhost:8000`

2. Updated docker-compose environment variables:
   - Changed `docker-compose.yml` to use `VITE_API_URL=http://localhost:8000`
   - Changed `docker-compose.prod.yml` to use `VITE_API_URL=http://localhost:8000`

This change ensures that the browser (running on the host machine) can properly resolve the API endpoint while still maintaining the Nginx proxy configuration for production use.

## Database Initialization Fix (2023-06-16)

After fixing the API URL resolution issue, we encountered a database initialization problem. The API container was attempting to access database tables before they were created.

### Updates Made:

1. Created an entrypoint script (`docker/api/entrypoint.sh`) that:
   - Waits for the PostgreSQL database to be ready
   - Runs database migrations using Alembic
   - Creates an admin user if it doesn't exist
   - Starts the API server with the appropriate arguments

2. Updated Docker configurations:
   - Modified `docker/api/Dockerfile.dev` to use the entrypoint script
   - Modified `docker/api/Dockerfile.prod` to use the entrypoint script with production-specific arguments
   - Added proper environment variable handling for different runtime modes

This change ensures that the database is properly initialized before the API server starts, preventing errors related to missing database tables.

## Next Steps

The implementation is now complete. The next steps are:

1. Test the changes to ensure proper communication between services
2. Verify that the frontend can access the API in both development and production environments
3. Monitor for any issues during container startup and runtime

## Reference Materials

During my research, I found the following best practices for container microservices communication:

1. Use service names instead of localhost for inter-container communication
2. Implement proper environment variable configuration for different environments
3. Configure API gateways for streamlined communication
4. Ensure CORS settings allow connections from all relevant origins
5. Leverage Docker networking for service discovery 