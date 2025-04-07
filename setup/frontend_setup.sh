#!/bin/bash

# Define the frontend directory
FRONTEND_DIR="$(pwd)/frontend"

echo "📂 Frontend directory: $FRONTEND_DIR"

# Navigate to the frontend directory
cd "$FRONTEND_DIR" || exit

# Ensure nodenv is initialized
export PATH="$HOME/.nodenv/bin:$PATH"
eval "$(nodenv init -)"

# Install the required Node.js version if not already installed
NODE_VERSION="14.5.0"
if ! nodenv versions --bare | grep -q "^$NODE_VERSION$"; then
    echo "📦 Installing Node.js version $NODE_VERSION..."
    nodenv install "$NODE_VERSION"
fi

# Set the local Node.js version for the project
nodenv local "$NODE_VERSION"

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
npm install

# Install Tailwind CSS and its dependencies
echo "📦 Installing Tailwind CSS and its dependencies..."
npm install -D tailwindcss postcss autoprefixer

# Initialize Tailwind CSS configuration
echo "⚙️  Initializing Tailwind CSS configuration..."
npx tailwindcss init -p

echo "✅ Frontend setup completed successfully."
