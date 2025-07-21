#!/bin/bash

echo "Applying direct SQL fix to the user roles in the database..."

# Path to the database - modify if needed
DB_PATH="/app/data/tourmanager.db"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file not found at $DB_PATH"
    exit 1
fi

# Apply SQL fix
echo "
-- Fix user role values in the database
UPDATE users SET role = 'USER' WHERE role = 'user';
UPDATE users SET role = 'ADMIN' WHERE role = 'admin';

-- Check the results
SELECT username, role FROM users;
" | sqlite3 "$DB_PATH"

echo "Fix applied successfully!"
