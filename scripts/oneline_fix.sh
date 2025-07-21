#!/bin/bash

# One-line direct fix for the response validation error
# Run this directly on the container with:
# docker-compose exec backend bash -c "cat > /app/direct_patch.py && python /app/direct_patch.py" < scripts/oneline_fix.sh

cat > /app/direct_patch.py << 'EOF'
# Direct patch script for the response validation error
import re
import os
import sys

def apply_patch():
    # Create backup
    os.system('cp /app/main.py /app/main.py.bak.$(date +%s)')
    
    # Make sure we have the JSONResponse import
    with open('/app/main.py', 'r') as f:
        content = f.read()
    
    if 'from fastapi.responses import JSONResponse' not in content:
        content = content.replace(
            'from fastapi.responses import',
            'from fastapi.responses import JSONResponse,'
        )
        if 'from fastapi.responses import' not in content:
            content = content.replace(
                'from fastapi import FastAPI',
                'from fastapi import FastAPI\nfrom fastapi.responses import JSONResponse'
            )
    
    # Replace the endpoint completely
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
    
    users = db.query(UserModel).all()
    
    # Convert to safe dictionary format
    result = []
    for user in users:
        user_dict = {
            "username": user.username,
            "email": user.email,
            "role": str(user.role).replace("UserRole.", ""),
            "status": str(user.status).replace("UserStatus.", ""),
            "created_at": user.created_at.isoformat() if hasattr(user, "created_at") and user.created_at else None,
            "last_login": user.last_login.isoformat() if hasattr(user, "last_login") and user.last_login else None
        }
        result.append(user_dict)
    
    return JSONResponse(content=result)
'''
    
    # Find the start of the list_users endpoint
    pattern = r'@app\.get\([\'"]\/api\/users[\'"].*?\)\s*\nasync def list_users\('
    match = re.search(pattern, content)
    
    if match:
        start_pos = match.start()
        
        # Find the end of the function
        end_pattern = r'\n@app\.'
        rest_content = content[start_pos:]
        end_match = re.search(end_pattern, rest_content)
        
        if end_match:
            end_pos = start_pos + end_match.start()
            
            # Replace the endpoint
            new_content = content[:start_pos] + new_endpoint + content[end_pos:]
            
            # Write the updated content
            with open('/app/main.py', 'w') as f:
                f.write(new_content)
            
            print("✅ Successfully applied the fix")
            return True
    
    print("❌ Could not find list_users endpoint")
    return False

if __name__ == "__main__":
    if apply_patch():
        # Restart the application
        os.system('pkill -f "uvicorn main:app"')
        print("🔄 Restarting the application...")
    else:
        print("❌ Fix failed")
        sys.exit(1)
EOF

echo "Run the following command to apply the fix:"
echo "docker-compose exec backend bash -c \"python /app/direct_patch.py\""
