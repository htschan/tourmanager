#!/bin/bash

# Generate a secure JWT secret for local development
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Create .env file from example if it doesn't exist
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    sed -i "s/your-secure-secret-key-here/$JWT_SECRET/g" backend/.env
fi

# Export the JWT secret for docker-compose
export JWT_SECRET_KEY=$JWT_SECRET

# Start the application
docker compose up --build
