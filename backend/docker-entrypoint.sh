#!/bin/bash

# Script to check and fix bcrypt compatibility issues

echo "Checking bcrypt and passlib versions..."

# Install specific compatible versions if needed
pip install --no-cache-dir bcrypt==4.0.1 passlib[bcrypt]==1.7.4

echo "Authentication libraries updated successfully."

# Continue with normal startup
exec "$@"
