# NetRaven Installation Guide

This guide provides step-by-step instructions for installing and running the NetRaven application.

## Prerequisites

- Git
- Docker and Docker Compose
- Python 3.10+ (for manual setup only)

## Quick Start with Docker (Recommended)

The easiest way to get NetRaven up and running is using Docker Compose:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/netraven.git
   cd netraven
   ```

2. Start the application:
   ```bash
   docker compose up
   ```

3. Access the application:
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Creating an Admin User

To test authentication, create an admin user:

```bash
# Run from the project root directory
python3 scripts/create_admin.py
```

This creates a user with the following default credentials:
- Username: admin
- Password: adminpass123
- Email: admin@example.com

You can customize these by passing arguments:

```bash
python3 scripts/create_admin.py my_username my_password my_email@example.com
```

## Manual Installation (Alternative)

If you prefer not to use Docker:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/netraven.git
   cd netraven
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Start the backend API:
   ```bash
   uvicorn netraven.web:app --reload --port 8000
   ```

5. In a separate terminal, start the frontend:
   ```bash
   cd netraven/web/frontend
   npm install
   npm run serve
   ```

## Troubleshooting

### Docker Issues

- **WSL UNC Path Errors**: If using WSL, ensure you're using Linux paths, not Windows UNC paths
- **Permission Issues**: The Docker containers run as user 1001 - ensure your host directories have appropriate permissions
- **Port Conflicts**: If ports 8000 or 8080 are in use, modify the port mappings in docker-compose.yml
- **Missing Dependencies**: If you encounter errors related to missing modules like 'email-validator', install them in the container:
  ```bash
  # Install email-validator in the backend container
  docker exec -it netraven-api-1 pip install email-validator
  
  # Restart the container to apply changes
  docker restart netraven-api-1
  ```

### Frontend Issues

- **ESLint Errors**: For development, ESLint is disabled by default. To fix issues before production, run `npm run lint -- --fix`
- **Node Module Issues**: If you encounter module not found errors, try deleting node_modules and running `npm install` again
- **Login Issues**: If you can't log in and see "404 Not Found" errors in the logs when accessing `/api/v1/auth/token`, check the API URL configuration:
  ```bash
  # The API URL should be set to the base URL without the /api/v1 part
  # In docker-compose.yml:
  environment:
    - VUE_APP_API_URL=http://localhost:8000
  
  # After changing the configuration, restart the containers:
  docker-compose down && docker-compose up -d
  ```

### Backend Issues

- **Database Errors**: Check that the database file is accessible and has correct permissions
- **API Connection Issues**: Verify that the frontend API service is configured with the correct backend URL

For more detailed troubleshooting, refer to the project README and documentation. 