#!/usr/bin/env python3
"""
Direct database fix for user roles.
This script uses SQLAlchemy to fix the user role values in the database.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db_fix')

# Database path (can be overridden via command-line argument)
DEFAULT_DB_PATH = '/app/data/tourmanager.db'

def fix_user_roles(db_path):
    """
    Fix user role values in the database by converting lowercase to uppercase.
    
    Args:
        db_path: Path to the SQLite database file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            logger.error(f"Error: 'users' table not found in database {db_path}")
            return False
        
        # Get the current role values
        cursor.execute("SELECT username, role FROM users")
        users = cursor.fetchall()
        
        if not users:
            logger.info(f"No users found in database {db_path}")
            return True
        
        logger.info(f"Found {len(users)} users in database:")
        for user in users:
            username, role = user
            logger.info(f"User: {username}, Role: {role}")
        
        # Update 'user' to 'USER'
        cursor.execute("UPDATE users SET role = 'USER' WHERE role = 'user'")
        user_count = cursor.rowcount
        
        # Update 'admin' to 'ADMIN'
        cursor.execute("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'")
        admin_count = cursor.rowcount
        
        # Commit the changes
        conn.commit()
        
        total_updated = user_count + admin_count
        logger.info(f"Updated {total_updated} user role values ({user_count} users, {admin_count} admins)")
        
        # Verify the changes
        cursor.execute("SELECT username, role FROM users")
        updated_users = cursor.fetchall()
        logger.info("Updated role values:")
        for user in updated_users:
            username, role = user
            logger.info(f"User: {username}, Role: {role}")
        
        conn.close()
        return True
    
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Get database path from command-line arguments or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH
    
    # Check if database file exists
    if not os.path.exists(db_path):
        logger.error(f"Error: Database file not found at {db_path}")
        sys.exit(1)
    
    print(f"Fixing user role values in database: {db_path}")
    
    if fix_user_roles(db_path):
        print("✅ Successfully fixed user role values in the database.")
    else:
        print("❌ Failed to fix user role values.")
        sys.exit(1)
