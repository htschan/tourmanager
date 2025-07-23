#!/bin/bash

# Install required packages in the Docker container
echo "Installing required Python packages in Docker container..."
docker compose exec backend pip install fastapi-mail python-dotenv

echo "Packages installed. Now you can run the email test."
echo ""
echo "To test email functionality, use:"
echo "./scripts/run_email_test.sh your-test-email@example.com"
