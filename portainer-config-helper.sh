#!/bin/bash
# Script to help migrate from .env configuration to Portainer stack configuration
# It reads your .env file and formats the variables for easy copy-paste into Portainer

ENV_FILE="./backend/.env"
REQUIRED_VARS=("MAIL_USERNAME" "MAIL_PASSWORD" "MAIL_FROM" "JWT_SECRET_KEY")
OPTIONAL_VARS=("MAIL_SERVER" "MAIL_PORT" "FRONTEND_URL" "DATABASE_PATH")

echo "===== Tour Manager Portainer Configuration Helper ====="
echo "This script helps you extract environment variables from your .env file"
echo "for use in Portainer stack configuration."
echo

if [ ! -f "$ENV_FILE" ]; then
    echo "Warning: $ENV_FILE does not exist. Showing default configuration."
else
    echo "Reading configuration from $ENV_FILE"
fi

echo
echo "===== Required Environment Variables ====="

for var in "${REQUIRED_VARS[@]}"; do
    value=""
    if [ -f "$ENV_FILE" ]; then
        value=$(grep "^$var=" "$ENV_FILE" | cut -d '=' -f2-)
    fi
    
    if [ -z "$value" ]; then
        echo "$var: [Not found in .env file - YOU MUST SET THIS IN PORTAINER]"
    else
        echo "$var: $value"
    fi
done

echo
echo "===== Optional Environment Variables ====="

for var in "${OPTIONAL_VARS[@]}"; do
    value=""
    if [ -f "$ENV_FILE" ]; then
        value=$(grep "^$var=" "$ENV_FILE" | cut -d '=' -f2-)
    fi
    
    if [ -z "$value" ]; then
        echo "$var: [Using default]"
    else
        echo "$var: $value"
    fi
done

echo
echo "===== Volume Configuration ====="
echo "SCRIPT_VOLUME_PATH: [Set this to your scripts directory path]"
echo "DATA_VOLUME_PATH: [Set this to your data directory path]"

echo
echo "===== Instructions ====="
echo "1. In Portainer, create a new stack"
echo "2. Upload the portainer-stack.yml file"
echo "3. Add the environment variables listed above"
echo "4. Set your volume paths for scripts and data"
echo "5. Deploy the stack"
echo 
echo "For more details, see portainer-email-guide.md"
