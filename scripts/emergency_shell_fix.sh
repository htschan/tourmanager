#!/bin/bash

# EMERGENCY OVERRIDE - Complete replacement of users API
# This script takes over the container shell and manually modifies files

# Find the backend container
BACKEND_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "komoot.*backend|tourmanager.*backend" | head -1)

if [ -z "$BACKEND_CONTAINER" ]; then
    echo "❌ Error: Backend container not found! Is it running?"
    docker ps
    exit 1
fi

echo "🔍 Found backend container: $BACKEND_CONTAINER"

# Execute bash inside the container
echo "🚀 Launching emergency fix inside container..."
docker exec -it $BACKEND_CONTAINER bash -c '
set -e  # Exit on error

echo "🔧 Starting emergency fix procedure"

# Create backup of main.py
cp /app/main.py /app/main.py.bak.emergency

echo "⚙️ Adding JSONResponse import"
# Add JSONResponse import if needed
if ! grep -q "from fastapi.responses import JSONResponse" /app/main.py; then
    sed -i "1s/^/from fastapi.responses import JSONResponse\\n/" /app/main.py
fi

echo "🔄 Finding user API endpoint"
# Find the users endpoint in main.py
if grep -q "@app.get(\"/api/users\"" /app/main.py; then
    # Found it - proceed with replacement
    
    # Create a temporary file for our replacement code
    cat > /tmp/fixed_users_endpoint.txt << '\''EOF'\''
@app.get("/api/users")
async def list_users(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only) - EMERGENCY FIXED VERSION"""
    if not hasattr(current_user, "role") or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view user list"
        )
    
    try:
        users = db.query(UserModel).all()
        logger.info(f"Successfully fetched {len(users)} users")
        
        # Manual serialization to avoid validation issues
        result = []
        for user in users:
            # Build a completely safe representation
            user_dict = {}
            
            # Safe get attribute helper function
            def safe_get(obj, attr, default=""):
                if hasattr(obj, attr):
                    val = getattr(obj, attr)
                    return val if val is not None else default
                return default
            
            # Basic fields
            user_dict["username"] = safe_get(user, "username")
            user_dict["email"] = safe_get(user, "email")
            
            # Role handling
            if hasattr(user, "role"):
                if user.role == UserRole.ADMIN:
                    user_dict["role"] = "ADMIN"
                else:
                    user_dict["role"] = "USER"
            else:
                user_dict["role"] = "USER"
            
            # Status handling
            if hasattr(user, "status"):
                user_dict["status"] = str(user.status).upper()
                if "." in user_dict["status"]:
                    user_dict["status"] = user_dict["status"].split(".")[-1]
            else:
                user_dict["status"] = "ACTIVE"
            
            # Date fields
            for date_field in ["created_at", "last_login"]:
                user_dict[date_field] = None
                if hasattr(user, date_field) and getattr(user, date_field):
                    try:
                        user_dict[date_field] = getattr(user, date_field).isoformat()
                    except:
                        user_dict[date_field] = str(getattr(user, date_field))
            
            result.append(user_dict)
        
        # Use JSONResponse to bypass FastAPI validation
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching users: {str(e)}"
        )
EOF
    
    echo "🔁 Replacing users endpoint"
    # Replace the entire endpoint using a marker-based approach
    awk '\''
    BEGIN { p=1 }
    /^@app\.get\("\/api\/users"/ { p=0; print; system("cat /tmp/fixed_users_endpoint.txt"); next }
    /^@app\./ && p==0 { p=1 }
    p==1 { print }
    '\'' /app/main.py > /app/main.py.new
    
    # Replace the original file
    mv /app/main.py.new /app/main.py
    
    echo "✅ Users endpoint replaced successfully!"
else
    echo "❌ Could not find users endpoint in main.py"
    echo "📝 Trying to create a new endpoint instead"
    
    # Create a new endpoint at the end of the file
    cat >> /app/main.py << '\''EOF'\''

# EMERGENCY FIXED USERS ENDPOINT
@app.get("/api/users")
async def list_users(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only) - EMERGENCY FIXED VERSION"""
    if not hasattr(current_user, "role") or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view user list"
        )
    
    try:
        users = db.query(UserModel).all()
        logger.info(f"Successfully fetched {len(users)} users")
        
        # Manual serialization to avoid validation issues
        result = []
        for user in users:
            # Build a completely safe representation
            user_dict = {}
            
            # Safe get attribute helper function
            def safe_get(obj, attr, default=""):
                if hasattr(obj, attr):
                    val = getattr(obj, attr)
                    return val if val is not None else default
                return default
            
            # Basic fields
            user_dict["username"] = safe_get(user, "username")
            user_dict["email"] = safe_get(user, "email")
            
            # Role handling
            if hasattr(user, "role"):
                if user.role == UserRole.ADMIN:
                    user_dict["role"] = "ADMIN"
                else:
                    user_dict["role"] = "USER"
            else:
                user_dict["role"] = "USER"
            
            # Status handling
            if hasattr(user, "status"):
                user_dict["status"] = str(user.status).upper()
                if "." in user_dict["status"]:
                    user_dict["status"] = user_dict["status"].split(".")[-1]
            else:
                user_dict["status"] = "ACTIVE"
            
            # Date fields
            for date_field in ["created_at", "last_login"]:
                user_dict[date_field] = None
                if hasattr(user, date_field) and getattr(user, date_field):
                    try:
                        user_dict[date_field] = getattr(user, date_field).isoformat()
                    except:
                        user_dict[date_field] = str(getattr(user, date_field))
            
            result.append(user_dict)
        
        # Use JSONResponse to bypass FastAPI validation
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching users: {str(e)}"
        )
EOF

    echo "✅ New users endpoint added at the end of main.py"
fi

echo "💻 Verifying the changes"
tail -n 20 /app/main.py

echo "🔄 Restarting the application"
pkill -f "uvicorn main:app" || true

echo "✅ Emergency fix complete. The application will restart automatically."
'

echo ""
echo "🎬 Emergency fix procedure completed"
echo "🔍 Check the application logs for errors:"
echo "   docker logs $BACKEND_CONTAINER"
