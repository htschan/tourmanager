#!/bin/bash

# A direct approach to fix the response validation error
# This script directly patches the main.py file without attempting to parse it

echo "Applying direct fix to response validation error..."

# Create a backup of the original file
cp /app/main.py /app/main.py.bak.$(date +%s)
echo "✅ Created backup of main.py"

# Inspect the list_users endpoint
grep -A 10 "def list_users" /app/main.py
echo ""

# Create a temporary file with the fixed endpoint implementation
cat > /tmp/fixed_list_users.py << 'EOF'
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
EOF

# Ensure we have the JSONResponse import
if ! grep -q "from fastapi.responses import JSONResponse" /app/main.py; then
    # Add the import at the top of the file
    sed -i '1s/^/from fastapi.responses import JSONResponse\n/' /app/main.py
    echo "✅ Added JSONResponse import"
fi

# Find all list_users implementations and replace them
START_LINE=$(grep -n "@app.get(\"/api/users\"" /app/main.py | cut -d: -f1 | head -1)

if [ -z "$START_LINE" ]; then
    START_LINE=$(grep -n "def list_users" /app/main.py | cut -d: -f1 | head -1)
    # Go back to find the decorator
    if [ ! -z "$START_LINE" ]; then
        START_LINE=$((START_LINE - 1))
    fi
fi

if [ -z "$START_LINE" ]; then
    echo "❌ Could not find list_users endpoint in main.py"
    exit 1
fi

# Find the next endpoint
END_SEARCH_PATTERN="@app..*\|def [a-zA-Z_]"
END_LINE=$(tail -n +$((START_LINE + 1)) /app/main.py | grep -n "$END_SEARCH_PATTERN" | head -1 | cut -d: -f1)
END_LINE=$((START_LINE + END_LINE - 1))

# Replace the endpoint in the file
sed -i "${START_LINE},${END_LINE}c\\$(cat /tmp/fixed_list_users.py)" /app/main.py

echo "✅ Replaced list_users endpoint"

# Restart the uvicorn server
echo "Restarting the backend service..."
pkill -f "uvicorn main:app"

echo "Fix applied. The application will restart automatically."
echo "Check the logs for any remaining errors."
