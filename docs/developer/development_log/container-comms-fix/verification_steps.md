# NetRaven Container Communication Fix - Verification Steps

## Testing Procedure

Follow these steps to verify that the container communication issues have been fixed:

### Development Environment Testing

1. Start the development environment:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

2. Verify frontend can access API:
   - Open browser to http://localhost:5173
   - Check browser console for API connection errors
   - Log in to the application (if authentication is required)
   - Verify that API requests are successful

3. Check CORS configuration:
   - Review browser console for CORS-related errors
   - All API requests should complete without CORS errors

### Production Environment Testing

1. Start the production environment:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up --build
   ```

2. Verify frontend can access API:
   - Open browser to http://localhost (port 80)
   - Check browser console for API connection errors
   - Log in to the application
   - Verify that all features requiring API access function correctly

3. Test API proxy:
   - Open browser to http://localhost/api/health
   - Should receive "status": "ok" response
   - This verifies that the Nginx proxy to the API is working

## Monitoring and Troubleshooting

If issues are encountered during testing:

1. Check container logs:
   ```bash
   docker-compose logs frontend
   docker-compose logs api
   ```

2. Verify network connectivity between containers:
   ```bash
   docker-compose exec frontend ping api
   docker-compose exec api ping frontend
   ```

3. Check environment variables in containers:
   ```bash
   docker-compose exec frontend env | grep VITE_API
   ```

4. Inspect Nginx configuration:
   ```bash
   docker-compose exec frontend nginx -T
   ```

## Rollback Procedure

If necessary, you can roll back the changes with the following steps:

1. Revert `frontend/src/services/api.js` to use hard-coded `API_BASE_URL`
2. Remove API proxy configuration from `frontend/nginx.conf`
3. Restore original environment variable settings in Docker compose files
4. Restart the containers with the original configuration 