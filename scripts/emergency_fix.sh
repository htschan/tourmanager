#!/bin/bash

# Emergency fix for response validation errors
# This is a last resort that directly edits the list_users implementation

echo "Applying emergency fix to response validation error..."

# Check if we're running in the container
if [ ! -f "/app/main.py" ]; then
    echo "❌ Error: /app/main.py not found. This script must run inside the backend container."
    echo "Run with: docker-compose exec backend /scripts/emergency_fix.sh"
    exit 1
fi

# Create a backup
cp /app/main.py /app/main.py.bak.$(date +%s)

# Directly insert a working implementation into main.py
# This approach is more direct and avoids parsing issues

# Step 1: Add JSONResponse import if needed
if ! grep -q "from fastapi.responses import JSONResponse" /app/main.py; then
    sed -i '1s/^/from fastapi.responses import JSONResponse\n/' /app/main.py
    echo "✅ Added JSONResponse import"
fi

# Step 2: Create the replacement function text
cat > /tmp/fixed_users_endpoint.txt << 'EOF'
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
        
        # Build a safe response that doesn't require model validation
        result = []
        for user in users:
            user_dict = {
                "username": user.username,
                "email": user.email,
                "role": str(user.role).split('.')[1] if hasattr(user.role, "name") else str(user.role),
                "status": str(user.status).split('.')[1] if hasattr(user.status, "name") else str(user.status)
            }
            
            # Add optional fields if they exist
            if hasattr(user, "created_at") and user.created_at:
                user_dict["created_at"] = user.created_at.isoformat()
            else:
                user_dict["created_at"] = None
                
            if hasattr(user, "last_login") and user.last_login:
                user_dict["last_login"] = user.last_login.isoformat()
            else:
                user_dict["last_login"] = None
            
            result.append(user_dict)
        
        # Use JSONResponse to bypass FastAPI's response validation
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching users: {str(e)}"
        )
EOF

# Step 3: Create a sed script to replace the endpoint
cat > /tmp/replace_endpoint.sed << EOF
/\@app\.get\(\"\/api\/users/,/^\@app\./ {
    /^\@app\.get\(\"\/api\/users/,/^\@app\./ {
        /^\@app\.get\(\"\/api\/users/ {
            r /tmp/fixed_users_endpoint.txt
            d
        }
        /^\@app\./ !d
        /^\@app\.get\(\"\/api\/users/ d
    }
}
EOF

# Step 4: Apply the sed script
sed -i -f /tmp/replace_endpoint.sed /app/main.py

echo "✅ Applied emergency fix to list_users endpoint"

# Step 5: Fix enum handling in User model
if [ -f "/app/models/users.py" ]; then
    cp /app/models/users.py /app/models/users.py.bak.$(date +%s)
    
    # Check if CaseInsensitiveEnum already exists
    if ! grep -q "class CaseInsensitiveEnum" /app/models/users.py; then
        cat > /tmp/case_insensitive_enum.txt << 'EOF'
class CaseInsensitiveEnum(enum.Enum):
    """Base enum class that provides case-insensitive value comparison"""
    
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            # Look for a case-insensitive match
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None

EOF
        
        # Insert it before UserRole
        sed -i '/class UserRole/i\'$(cat /tmp/case_insensitive_enum.txt) /app/models/users.py
        
        # Update UserRole to inherit from it
        sed -i 's/class UserRole(enum.Enum):/class UserRole(CaseInsensitiveEnum):/' /app/models/users.py
        
        echo "✅ Added CaseInsensitiveEnum to models/users.py"
    fi
fi

# Step 6: Fix database enum values
echo "Fixing database enum values..."
if [ -f "/app/data/tourmanager.db" ]; then
    sqlite3 /app/data/tourmanager.db << EOF
UPDATE users SET role = 'USER' WHERE role = 'user';
UPDATE users SET role = 'ADMIN' WHERE role = 'admin';
SELECT username, role FROM users;
EOF
    echo "✅ Fixed database enum values"
fi

# Step 7: Restart the application
echo "Restarting the application..."
pkill -f "uvicorn main:app"

echo "✅ Emergency fix complete. The application will restart automatically."
