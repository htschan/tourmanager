#!/usr/bin/env python3
"""
Complete fix for user API issues:
1. Case-insensitive enum handling
2. Fix response validation
"""

import os
import sys
import logging
import sqlite3
import re
import shutil
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('user_api_fix')

# Paths
MAIN_PY = '/app/main.py'
USERS_MODEL_PY = '/app/models/users.py'
DB_PATH = '/app/data/tourmanager.db'

def create_backup(file_path):
    """Create a backup of the specified file"""
    backup_path = f"{file_path}.bak.{int(os.path.getmtime(file_path))}"
    shutil.copy(file_path, backup_path)
    logger.info(f"Created backup at {backup_path}")
    return backup_path

def fix_database_enum_values():
    """Fix enum values in the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check current values
        cursor.execute("SELECT username, role FROM users")
        users = cursor.fetchall()
        logger.info(f"Current users in database: {len(users)}")
        for username, role in users:
            logger.info(f"User: {username}, Role: {role}")
        
        # Fix values
        cursor.execute("UPDATE users SET role = 'USER' WHERE role = 'user'")
        user_count = cursor.rowcount
        
        cursor.execute("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'")
        admin_count = cursor.rowcount
        
        conn.commit()
        
        total_fixed = user_count + admin_count
        logger.info(f"Fixed {total_fixed} user records in the database")
        
        return True
    except Exception as e:
        logger.error(f"Database fix failed: {str(e)}", exc_info=True)
        return False

def fix_users_model():
    """Add case-insensitive enum handling to the User model"""
    try:
        # Create backup
        create_backup(USERS_MODEL_PY)
        
        # Read the current file
        with open(USERS_MODEL_PY, 'r') as f:
            content = f.read()
        
        # Check if CaseInsensitiveEnum already exists
        if 'class CaseInsensitiveEnum' not in content:
            # Replace the UserRole enum with a case-insensitive version
            new_enum = """import enum
from datetime import datetime

class CaseInsensitiveEnum(enum.Enum):
    # Base enum class that provides case-insensitive value comparison
    
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            # Look for a case-insensitive match
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None

class UserRole(CaseInsensitiveEnum):
    ADMIN = "admin"
    USER = "user"
"""
            # Replace the import and UserRole definition
            pattern = r'import enum\s+from datetime import datetime\s+class UserRole\(enum\.Enum\):\s+ADMIN = "admin"\s+USER = "user"'
            content = re.sub(pattern, new_enum, content, flags=re.DOTALL)
            
            # Write the updated content
            with open(USERS_MODEL_PY, 'w') as f:
                f.write(content)
            
            logger.info("Added CaseInsensitiveEnum to users model")
        else:
            logger.info("CaseInsensitiveEnum already exists in users model")
        
        return True
    except Exception as e:
        logger.error(f"Failed to fix users model: {str(e)}", exc_info=True)
        return False

def fix_list_users_endpoint():
    """Fix the list_users endpoint to avoid response validation errors"""
    try:
        # Create backup
        create_backup(MAIN_PY)
        
        # Read the file
        with open(MAIN_PY, 'r') as f:
            content = f.read()
        
        # Check if JSONResponse is imported
        if 'from fastapi.responses import JSONResponse' not in content:
            # Add import at the top
            imports = 'from fastapi import FastAPI, HTTPException, Query, Depends, Request, status, File, UploadFile, Form\n'
            new_imports = 'from fastapi import FastAPI, HTTPException, Query, Depends, Request, status, File, UploadFile, Form\nfrom fastapi.responses import JSONResponse\n'
            content = content.replace(imports, new_imports)
        
        # Find and replace the list_users endpoint
        endpoint_pattern = r'@app\.get\([\'"]\/api\/users[\'"](, [^\)]+)?\)\s+async def list_users\([^)]+\):[^@]+'
        
        # New endpoint implementation
        new_endpoint = '''@app.get("/api/users")
async def list_users(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view user list"
        )
    
    try:
        users = db.query(UserModel).all()
        logger.info(f"Successfully fetched {len(users)} users")
        
        # Convert enum values to strings to avoid serialization issues
        result = []
        for user in users:
            # Create a dictionary with the user data
            user_dict = {
                "username": user.username,
                "email": user.email,
                "role": user.role.name if hasattr(user.role, "name") else str(user.role),
                "status": user.status.name if hasattr(user.status, "name") else str(user.status),
                "created_at": user.created_at.isoformat() if hasattr(user, "created_at") and user.created_at else None,
                "last_login": user.last_login.isoformat() if hasattr(user, "last_login") and user.last_login else None
            }
            result.append(user_dict)
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching users: {str(e)}"
        )

'''
        
        # Replace the endpoint
        new_content = re.sub(endpoint_pattern, new_endpoint, content, flags=re.DOTALL)
        
        # Write the updated content
        with open(MAIN_PY, 'w') as f:
            f.write(new_content)
            
        logger.info("Updated list_users endpoint to use JSONResponse")
        
        return True
    except Exception as e:
        logger.error(f"Failed to fix list_users endpoint: {str(e)}", exc_info=True)
        return False

def main():
    """Apply all fixes"""
    success = True
    
    # Step 1: Fix enum values in the database
    logger.info("Step 1: Fixing database enum values...")
    if fix_database_enum_values():
        logger.info("✓ Database enum values fixed")
    else:
        logger.error("✗ Failed to fix database enum values")
        success = False
    
    # Step 2: Fix User model for case-insensitive enum handling
    logger.info("Step 2: Fixing User model for case-insensitive enum handling...")
    if fix_users_model():
        logger.info("✓ User model updated")
    else:
        logger.error("✗ Failed to update User model")
        success = False
    
    # Step 3: Fix list_users endpoint to avoid response validation
    logger.info("Step 3: Fixing list_users endpoint...")
    if fix_list_users_endpoint():
        logger.info("✓ list_users endpoint updated")
    else:
        logger.error("✗ Failed to update list_users endpoint")
        success = False
    
    # Final result
    if success:
        logger.info("All fixes applied successfully!")
        logger.info("Restarting the application...")
        os.system("pkill -f 'uvicorn main:app'")
        return 0
    else:
        logger.error("Some fixes failed. Check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
