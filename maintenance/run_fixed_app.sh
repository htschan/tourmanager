#!/bin/bash

# Script to run the Tour Manager application with all fixes applied

echo "🚀 Starting Tour Manager with all fixes applied..."
echo "---------------------------------------------"

# Change to project root directory
cd "$(dirname "$0")/.."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running! Please start Docker and try again."
  exit 1
fi

# Run with the fixed docker-compose file
docker-compose -f maintenance/fixes/docker-compose.fixed.yml up --build

# Note: Use Ctrl+C to stop the application
