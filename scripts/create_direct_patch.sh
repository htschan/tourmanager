#!/bin/bash

# Direct user API fix for Docker environment
# This script creates a direct replacement for the list_users function in your FastAPI application

echo "Creating patch file for direct application..."

cat > patch_list_users.py << 'EOF'
#!/usr/bin/env python3

"""
Emergency patch for user API response validation issues.
This script directly modifies the main.py file to fix the response validation error.
"""

import re
import os
import sys
import logging
import traceback

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('patch')

def apply_patch():
    """Apply direct patch to main.py"""
    try:
        # Path to main.py
        main_file = "/app/main.py"
        
        # Backup the original file
        backup_file = f"{main_file}.bak.{os.getpid()}"
        with open(main_file, 'r') as src, open(backup_file, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Created backup at {backup_file}")
        
        # Read the original content
        with open(main_file, 'r') as f:
            content = f.read()
        
        # Add JSONResponse import if needed
        if 'from fastapi.responses import JSONResponse' not in content:
            pattern = r'from fastapi\.responses import'
            replacement = 'from fastapi.responses import JSONResponse, '
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
            else:
                # Add import at top
                content = 'from fastapi.responses import JSONResponse\n' + content
            logger.info("Added JSONResponse import")
        
        # Create new endpoint code
        new_endpoint = '''
@app.get("/api/users")
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
        
        # Manual serialization to bypass validation
        result = []
        for user in users:
            try:
                user_dict = {
                    "username": user.username,
                    "email": user.email,
                    "role": str(user.role).replace("UserRole.", "") if user.role else "USER",
                    "status": str(user.status).replace("UserStatus.", "") if user.status else "PENDING",
                }
                
                # Handle dates carefully
                if hasattr(user, "created_at") and user.created_at:
                    try:
                        user_dict["created_at"] = user.created_at.isoformat()
                    except:
                        user_dict["created_at"] = str(user.created_at)
                else:
                    user_dict["created_at"] = None
                
                if hasattr(user, "last_login") and user.last_login:
                    try:
                        user_dict["last_login"] = user.last_login.isoformat()
                    except:
                        user_dict["last_login"] = str(user.last_login)
                else:
                    user_dict["last_login"] = None
                
                result.append(user_dict)
                
            except Exception as e:
                logger.error(f"Error processing user {getattr(user, 'username', 'unknown')}: {str(e)}")
        
        # Use JSONResponse to bypass validation
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching users: {str(e)}"
        )
'''
        
        # Find the list_users endpoint
        patterns = [
            r'@app\.get\([\'"]\/api\/users[\'"](,\s*response_model=[^\)]+)?\)\s*\nasync def list_users\([^)]+\):.*?(?=\n@app\.|\Z)',
            r'@app\.get\([\'"]\/api\/users[\'"]\).*?async def list_users\([^)]+\):.*?(?=\n@app\.|\Z)',
            r'async def list_users\([^)]+\):.*?(?=\n@app\.|\Z)'
        ]
        
        replaced = False
        for pattern in patterns:
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, new_endpoint, content, flags=re.DOTALL)
                replaced = True
                logger.info(f"Replaced list_users endpoint using pattern: {pattern[:30]}...")
                break
        
        if not replaced:
            logger.error("Could not find list_users endpoint!")
            return False
        
        # Write the updated content
        with open(main_file, 'w') as f:
            f.write(content)
        
        logger.info("Successfully applied patch!")
        return True
        
    except Exception as e:
        logger.error(f"Error applying patch: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if apply_patch():
        print("✅ Patch successfully applied!")
        print("🔄 Restart the server for changes to take effect:")
        print("   pkill -f 'uvicorn main:app'")
        sys.exit(0)
    else:
        print("❌ Patch failed!")
        sys.exit(1)
EOF

echo "Patch file created. To apply it, run:"
echo "docker cp patch_list_users.py tourmanager-backend-1:/app/"
echo "docker exec tourmanager-backend-1 python /app/patch_list_users.py"
echo "docker exec tourmanager-backend-1 pkill -f 'uvicorn main:app'"  # This will trigger auto-restart
echo ""
echo "Or as a one-liner:"
echo "docker cp patch_list_users.py tourmanager-backend-1:/app/ && docker exec tourmanager-backend-1 python /app/patch_list_users.py && docker exec tourmanager-backend-1 pkill -f 'uvicorn main:app'"
