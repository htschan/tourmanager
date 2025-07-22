#!/bin/bash

# Script to fix email configuration issues in running Docker container

echo "🔧 Fixing email configuration in the running backend container..."

# Get the container ID
CONTAINER_ID=$(docker ps -q -f name=backend)

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Backend container not found! Make sure it's running."
    exit 1
fi

echo "✅ Found backend container: $CONTAINER_ID"

# Copy the fixed email.py file into the container
docker cp ../backend/utils/email.py $CONTAINER_ID:/app/utils/

echo "✅ Updated email.py file in container"

# Restart the container to apply changes
echo "🔄 Restarting backend container..."
docker restart $CONTAINER_ID

echo "✅ Email configuration fix completed!"
echo "The user registration should now work correctly."
