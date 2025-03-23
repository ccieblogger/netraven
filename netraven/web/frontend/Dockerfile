FROM node:18-alpine

WORKDIR /app

# Create a non-root user with UID/GID 1001 to avoid conflicts
RUN addgroup -S netraven -g 1001 && \
    adduser -S -G netraven -u 1001 netraven

# Copy package.json and package-lock.json first for better layer caching
COPY package*.json ./

# Install dependencies and make sure all required packages are installed
RUN npm install && \
    npm install --save date-fns vue-toastification@2.0.0-rc.5 && \
    npm install --save-dev @babel/core @babel/eslint-parser @babel/preset-env && \
    chown -R netraven:netraven /app

# Switch to non-root user
USER netraven

# The source code will be mounted as a volume in docker-compose.yml
# This allows for hot-reloading

# Expose the server port
EXPOSE 8080

# Default command to run the app
CMD ["npm", "run", "serve"] 