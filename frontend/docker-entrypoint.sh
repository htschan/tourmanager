#!/bin/sh

# Debug info first to ensure script is running
echo "🔧 Generating runtime config..."
echo "🔧 VITE_API_BASE_URL=${VITE_API_BASE_URL:-not set}"

# Determine API URL based on environment
if [ -n "$VITE_API_BASE_URL" ]; then
  # If running in Docker, convert backend:8000 to localhost:8000 for browser access
  API_URL=$(echo "$VITE_API_BASE_URL" | sed 's/backend:8000/localhost:8000/')
else
  API_URL="http://localhost:8000"
fi

echo "🔧 Final API_URL=$API_URL"

# Create config with environment variables
echo "window.APP_CONFIG = {" > /app/dist/config.js
echo "  apiBaseUrl: '$API_URL'" >> /app/dist/config.js
echo "};" >> /app/dist/config.js

# Ensure config.js is readable
chmod 644 /app/dist/config.js

# Start the server
exec "$@"
