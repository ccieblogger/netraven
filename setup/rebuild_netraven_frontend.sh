#!/bin/bash

set -e

# Resolve absolute path of the script, then jump to the frontend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../frontend"

echo "🚀 Resetting your Vue/Vite/Tailwind environment..."

if [ ! -f "$FRONTEND_DIR/package.json" ]; then
  echo "❌ Cannot find frontend/package.json. Are you sure the path is correct?"
  exit 1
fi

cd "$FRONTEND_DIR"

echo "📁 In $(pwd)"

# Cleanup
echo "🧹 Cleaning node_modules, cache, dist, and lock files..."
rm -rf node_modules
rm -rf .vite
rm -rf dist
rm -f package-lock.json

# Install fresh dependencies
echo "📦 Installing dependencies..."
npm install

# Start Vite dev server
echo "⚡ Starting Vite dev server with fresh cache..."
npx vite --clearScreen false --force