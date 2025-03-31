# Frontend Development Guide

This guide provides instructions for developing and deploying the Vue.js frontend application for the NetRaven network device backup and management system.

## Directory Structure

The frontend application is part of the NetRaven project structure:

```
/NetRaven
  /netraven             <- Main Python package
    /web                <- Web components
      /frontend         <- Vue.js frontend
      /backend          <- FastAPI backend
    /core               <- Core functionality
```

## Development Setup

### Option 1: Using Root Docker Compose (Recommended)

The easiest way to run the complete NetRaven environment (both frontend and backend) is using the root Docker Compose file:

```bash
# From the project root directory
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
# Build and start the container from the frontend directory
cd netraven/web/frontend
docker compose up --build

# The server will be available at http://localhost:8080
```

### Option 3: Standard Setup

For direct development without Docker:

```bash
# Navigate to the frontend directory
cd netraven/web/frontend

# Install dependencies
npm install

# Start development server
npm run serve
```

## WSL Development

When running the frontend in WSL (Windows Subsystem for Linux), you may encounter UNC path errors like:
```
UNC paths are not supported. Defaulting to Windows directory.
```

To work around this issue when using WSL:
1. Use Linux native Node.js instead of the Windows version
2. Run the npm commands directly in the WSL terminal, not through Windows paths
3. Use Docker (see Option 2 above)
4. Use VS Code Remote-WSL extension

### VS Code Remote-WSL Development

VS Code's Remote-WSL extension provides a seamless way to develop in WSL without path issues:

1. Install the [Remote - WSL extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl) in VS Code
2. Click the green remote indicator in the bottom-left corner of VS Code
3. Select "Remote-WSL: New Window" or "Remote-WSL: Reopen Folder in WSL"
4. Navigate to your project directory
5. Open a terminal in VS Code - it will be a WSL terminal
6. Run npm commands from this terminal to avoid path issues

## Linting and Production Preparation

### Current Development Configuration

For development, ESLint is currently disabled in `vue.config.js` to prevent linting errors from blocking the development server.

### Production Preparation Checklist

**Before deploying to production, ensure you:**

1. **Enable and fix linting issues**:
   ```bash
   # Run linting to identify issues
   npm run lint
   
   # Fix auto-fixable issues
   npm run lint -- --fix
   ```

2. **Verify eslint configuration**:
   - Ensure `.eslintrc.js` is properly configured
   - Check that all required dependencies are installed

3. **Test production build locally**:
   ```bash
   npm run build
   ```

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

## Project Structure

- `/src/components` - Reusable Vue components
- `/src/views` - Page components
- `/src/store` - Pinia stores for state management
- `/src/router` - Vue Router configuration
- `/src/api` - API service modules
- `/src/assets` - Static assets

## References

For the complete frontend documentation, refer to the original README.md file in the frontend directory:
`netraven/web/frontend/README.md` 