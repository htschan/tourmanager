#!/bin/bash

# Ultimate direct fix for the database issue - SQL only
# This bypasses Python entirely and applies the fix directly to the database

echo "Applying direct SQL fix to the user roles in database..."

# Get the database path from environment or use default
DB_PATH=${DATABASE_PATH:-"/app/data/tourmanager.db"}

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Database file not found at $DB_PATH"
    echo "Looking for database files..."
    find /app -name "*.db" -type f
    
    # Try a secondary location
    if [ -f "/app/data/tourmanager.db" ]; then
        DB_PATH="/app/data/tourmanager.db"
        echo "Found database at $DB_PATH"
    else
        echo "No database found. Please specify the correct path."
        exit 1
    fi
fi

echo "Using database: $DB_PATH"
echo "Current user records:"
echo "SELECT username, email, role, status FROM users;" | sqlite3 "$DB_PATH"

# Fix user role values
echo "
-- Fix user role values in the database
UPDATE users SET role = 'USER' WHERE role = 'user';
UPDATE users SET role = 'ADMIN' WHERE role = 'admin';

-- Check the results
SELECT username, email, role, status FROM users;
" | sqlite3 "$DB_PATH"

echo "✅ Direct database fix applied"
