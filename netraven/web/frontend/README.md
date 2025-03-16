# NetRaven Frontend

This is the Vue.js frontend application for the NetRaven network device backup and management system.

## Directory Structure

This frontend application is part of the NetRaven project structure:

```
/NetRaven
  /netraven             <- Main Python package
    /web                <- Web components
      /frontend         <- THIS DIRECTORY (Vue.js frontend)
      /backend          <- FastAPI backend
    /core               <- Core functionality
```

**IMPORTANT**: Always develop and run the frontend from this directory (`/netraven/web/frontend`). 
Developing in any other directory (such as `/web/frontend`) will lead to structure inconsistencies.

## Development Setup

### Option 1: Using Root Docker Compose (Recommended)

The easiest way to run the complete NetRaven environment (both frontend and backend) is using the root Docker Compose file:

```bash
# From the project root directory (not this frontend directory)
cd ../../../
docker compose up
```

This will:
- Build and start both the backend API and frontend containers
- Mount the appropriate volumes for development
- Expose the frontend on port 8080 
- Enable hot-reloading for frontend changes

### Option 2: Frontend-Only Docker Development

If you want to run only the frontend in Docker:

```bash
# Build and start the container from this directory
docker compose up --build

# The server will be available at http://localhost:8080
```

To stop the container:

```bash
docker compose down
```

### Option 3: Standard Setup

For direct development without Docker:

```bash
# Install dependencies
npm install

# Start development server
npm run serve
```

#### Security Note: Running without Root Privileges

Our Docker configuration is set up to run as a non-root user for improved security:

- The containers run using a custom `netraven` user (UID 1001)
- Services bind to non-privileged ports (8080 instead of 80)
- File permissions are properly handled for volumes

This approach reduces security risks associated with running containers as root.

## WSL Issues

When running the frontend in WSL (Windows Subsystem for Linux), you may encounter UNC path errors like:
```
UNC paths are not supported. Defaulting to Windows directory.
```

To work around this issue when using WSL:
1. Use Linux native Node.js instead of the Windows version
2. Run the npm commands directly in the WSL terminal, not through Windows paths
3. Use Docker (see Option 2 above)
4. Use VS Code Remote-WSL extension (see VS Code section below)

## VS Code Remote-WSL Development

VS Code's Remote-WSL extension provides a seamless way to develop in WSL without path issues:

1. Install the [Remote - WSL extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl) in VS Code
2. Click the green remote indicator in the bottom-left corner of VS Code
3. Select "Remote-WSL: New Window" or "Remote-WSL: Reopen Folder in WSL"
4. Navigate to your project directory
5. Open a terminal in VS Code - it will be a WSL terminal
6. Run npm commands from this terminal to avoid path issues

## Linting and Production Preparation

### Current Development Configuration

For development, ESLint is currently disabled in `vue.config.js` to prevent linting errors from blocking the development server:

```javascript
module.exports = {
  lintOnSave: false,
  devServer: {
    client: {
      overlay: false,
    },
  },
}
```

### Known Linting Issues

The project uses `@babel/eslint-parser` for linting Vue files, which requires the following dependencies:
- `@babel/core`
- `@babel/eslint-parser`
- `@babel/preset-env`

These dependencies are explicitly installed in the Dockerfile.dev to ensure proper functioning.

### Production Preparation Checklist

**Before deploying to production, ensure you:**

1. **Enable and fix linting issues**:
   ```bash
   # Run linting to identify issues
   npm run lint
   
   # Fix auto-fixable issues
   npm run lint -- --fix
   ```

2. **Update vue.config.js for production**:
   - For the build process, remove or modify `vue.config.js` to enforce linting
   ```javascript
   module.exports = {
     lintOnSave: 'warning', // Enable linting but don't fail the build
     // ...other production settings
   }
   ```

3. **Verify eslint configuration**:
   - Ensure `.eslintrc.js` is properly configured
   - Check that all required dependencies are installed

4. **Test production build locally**:
   ```bash
   npm run build
   ```

Failing to address linting issues before production can result in:
- Degraded application performance
- Potential runtime errors
- Maintenance challenges for future development

## Building for Production

### Option 1: Standard Build

```bash
# Build for production
npm run build
```

### Option 2: Docker Production Deployment (Recommended)

This project includes a production-ready Docker setup that:
1. Builds the Vue.js application
2. Serves it using Nginx for optimal performance
3. Runs as a non-root user for enhanced security
4. Includes health checks and proper restart policies

To deploy using Docker:

```bash
# Build and start the container
docker compose up -d

# The application will be available at http://localhost:8080
```

#### Customizing the Deployment

The Docker setup can be customized in several ways:

1. **Environment Variables**: Add environment variables in docker-compose.yml
2. **SSL/TLS**: Mount SSL certificates for HTTPS support

#### Cloud Deployment

The Docker container can be deployed to various cloud services:

1. **AWS**:
   ```bash
   # Build the container
   docker build -t netraven-frontend:latest -f Dockerfile.prod .
   
   # Push to Amazon ECR
   aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
   docker tag netraven-frontend:latest your-account-id.dkr.ecr.your-region.amazonaws.com/netraven-frontend:latest
   docker push your-account-id.dkr.ecr.your-region.amazonaws.com/netraven-frontend:latest
   ```

2. **Digital Ocean**:
   ```bash
   # Deploy directly using the App Platform and connecting to your GitHub repository
   # Select the Dockerfile.prod as the build method
   ```

## Project Structure

- `/src/components` - Reusable Vue components
- `/src/views` - Page components
- `/src/store` - Pinia stores for state management
- `/src/router` - Vue Router configuration
- `/src/api` - API service modules
- `/src/assets` - Static assets 