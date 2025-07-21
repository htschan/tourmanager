#!/usr/bin/env python3
"""
Direct fix for FastAPI response validation issues in the user API.
This script modifies the list_users endpoint to handle response validation properly.
"""

import os
import re
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('response_fix')

# Main.py path
MAIN_PY_PATH = '/app/main.py'

def backup_file(file_path):
    """Create a backup of the file"""
    backup_path = f"{file_path}.bak.{int(os.path.getmtime(file_path))}"
    with open(file_path, 'r') as src, open(backup_path, 'w') as dest:
        dest.write(src.read())
    logger.info(f"Created backup at {backup_path}")
    return backup_path

def modify_list_users_endpoint():
    """Replace the list_users endpoint with a version that doesn't use response_model"""
    try:
        # Read the main.py file
        with open(MAIN_PY_PATH, 'r') as f:
            content = f.read()
        
        # Find the list_users endpoint
        pattern = r'@app\.get\("/api/users", response_model=List\[UserResponse\]\)\s+async def list_users\([^)]+\):[^@]+'
        list_users_match = re.search(pattern, content, re.DOTALL)
        
        if not list_users_match:
            logger.error("Could not find the list_users endpoint in main.py")
            return False
        
        # Create the new endpoint code
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
        # Use a safer query approach with error handling
        users = db.query(UserModel).all()
        logger.info(f"Successfully fetched {len(users)} users")
        
        # Manually serialize to avoid validation issues
        result = []
        for user in users:
            user_dict = {
                "username": user.username,
                "email": user.email,
                "role": user.role.name if hasattr(user.role, 'name') else str(user.role),
                "status": user.status.name if hasattr(user.status, 'name') else str(user.status),
                "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                "last_login": user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
            }
            result.append(user_dict)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching users: {str(e)}"
        )

'''
        
        # Replace the endpoint in the content
        new_content = re.sub(pattern, new_endpoint, content, flags=re.DOTALL)
        
        # Write the modified content back to the file
        with open(MAIN_PY_PATH, 'w') as f:
            f.write(new_content)
        
        logger.info("Successfully modified the list_users endpoint")
        return True
    
    except Exception as e:
        logger.error(f"Error modifying list_users endpoint: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    # Check if we're running in the correct environment
    if not os.path.exists(MAIN_PY_PATH):
        logger.error(f"Error: {MAIN_PY_PATH} not found. Make sure you're running this script in the right environment.")
        sys.exit(1)
    
    # Create a backup of main.py
    backup_file(MAIN_PY_PATH)
    
    # Modify the list_users endpoint
    if modify_list_users_endpoint():
        print("✅ Successfully fixed the response validation issue in the list_users endpoint.")
        print("   The application will need to be restarted for changes to take effect.")
    else:
        print("❌ Failed to fix the response validation issue.")
        sys.exit(1)
