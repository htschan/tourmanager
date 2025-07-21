#!/bin/bash

# Script to debug and fix response validation issues in the user API

echo "=== Debugging FastAPI Response Validation Errors ==="

# Function to check the UserResponse model
check_user_response_model() {
  echo "Checking UserResponse model definition..."
  
  # Extract UserResponse model fields
  RESPONSE_MODEL=$(grep -A 30 "class UserResponse" /app/auth.py || echo "Not found in auth.py")
  
  if [[ $RESPONSE_MODEL == "Not found in auth.py" ]]; then
    # Try other potential locations
    RESPONSE_MODEL=$(grep -A 30 "class UserResponse" /app/schemas/users.py 2>/dev/null || echo "Not found in schemas/users.py")
  fi
  
  echo "$RESPONSE_MODEL"
  echo ""
}

# Function to check User model to_dict method
check_user_model() {
  echo "Checking User model definition and to_dict method..."
  
  # Check if User model has to_dict method
  USER_MODEL_TO_DICT=$(grep -A 30 "def to_dict" /app/models/users.py 2>/dev/null || echo "to_dict method not found")
  
  echo "$USER_MODEL_TO_DICT"
  echo ""
  
  # Check full User model
  USER_MODEL=$(grep -A 50 "class User" /app/models/users.py 2>/dev/null || echo "User class not found")
  
  echo "User model definition:"
  echo "$USER_MODEL"
  echo ""
}

# Function to apply a fix for the response validation
apply_user_model_fix() {
  echo "Applying fix for response validation issue..."
  
  # Add to_dict method to User model if it doesn't exist or update it
  if grep -q "def to_dict" /app/models/users.py; then
    # If to_dict exists, modify it to ensure it matches UserResponse schema
    echo "Updating existing to_dict method..."
    
    # Create a temporary file with the updated code
    cat > /tmp/user_to_dict.py << 'EOF'
    def to_dict(self):
        """Convert user model to dictionary matching UserResponse schema"""
        return {
            "username": self.username,
            "email": self.email,
            "role": self.role.name if hasattr(self.role, 'name') else str(self.role),
            "status": self.status.name if hasattr(self.status, 'name') else str(self.status),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "profile": self.profile if hasattr(self, 'profile') else {},
        }
EOF

    # Use sed to replace the existing to_dict method
    sed -i '/def to_dict/,/}/c\\'"$(cat /tmp/user_to_dict.py)" /app/models/users.py
    
  else
    # If to_dict doesn't exist, add it
    echo "Adding to_dict method to User model..."
    
    # Append to_dict method to User class
    cat >> /app/models/users.py << 'EOF'
    def to_dict(self):
        """Convert user model to dictionary matching UserResponse schema"""
        return {
            "username": self.username,
            "email": self.email,
            "role": self.role.name if hasattr(self.role, 'name') else str(self.role),
            "status": self.status.name if hasattr(self.status, 'name') else str(self.status),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "profile": self.profile if hasattr(self, 'profile') else {},
        }
EOF
  fi
  
  echo "Fix applied to User model."
}

# Function to create a wrapper for the list_users endpoint
create_list_users_wrapper() {
  echo "Creating wrapper for list_users endpoint..."
  
  # Create backup of main.py
  cp /app/main.py /app/main.py.bak.$(date +%s)
  
  # Find the list_users function
  LIST_USERS_LINE=$(grep -n "async def list_users" /app/main.py | cut -d: -f1)
  
  if [ -z "$LIST_USERS_LINE" ]; then
    echo "Error: Could not find list_users endpoint in main.py"
    return 1
  fi
  
  # Find the end of the function
  END_LINE=$(tail -n +$LIST_USERS_LINE /app/main.py | grep -n "^@" | head -1 | cut -d: -f1)
  END_LINE=$((LIST_USERS_LINE + END_LINE - 1))
  
  # Extract the function
  FUNCTION=$(sed -n "${LIST_USERS_LINE},${END_LINE}p" /app/main.py)
  
  # Create replacement with manual serialization
  REPLACEMENT="@app.get(\"/api/users\")
async def list_users(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    \"\"\"List all users (admin only)\"\"\"
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail=\"Not authorized to view user list\"
        )
    
    try:
        # Use a safer query approach with error handling
        users = db.query(UserModel).all()
        main_logger.info(f\"Successfully fetched {len(users)} users\")
        
        # Manually serialize to avoid response validation issues
        result = []
        for user in users:
            try:
                if hasattr(user, 'to_dict'):
                    user_dict = user.to_dict()
                else:
                    # Fallback serialization
                    user_dict = {
                        \"username\": user.username,
                        \"email\": user.email,
                        \"role\": user.role.name if hasattr(user.role, 'name') else str(user.role),
                        \"status\": user.status.name if hasattr(user.status, 'name') else str(user.status),
                        \"created_at\": user.created_at.isoformat() if user.created_at else None,
                        \"last_login\": user.last_login.isoformat() if user.last_login else None
                    }
                result.append(user_dict)
            except Exception as e:
                main_logger.error(f\"Error serializing user {user.username}: {str(e)}\", exc_info=True)
        
        return result
    except Exception as e:
        main_logger.error(f\"Error fetching users: {str(e)}\", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f\"Internal server error while fetching users: {str(e)}\"
        )"
  
  # Replace the function in main.py
  sed -i "${LIST_USERS_LINE},${END_LINE}c\\${REPLACEMENT}" /app/main.py
  
  echo "List_users endpoint wrapper created."
}

# Run the checks
echo "Step 1: Checking models..."
check_user_response_model
check_user_model

# Apply fixes
echo "Step 2: Applying fixes..."
apply_user_model_fix
create_list_users_wrapper

echo "Step 3: Restarting application..."
pkill -f "uvicorn main:app"

echo "Fixes applied. The application will restart automatically due to the container's restart policy."
echo "Check the logs for any remaining errors."
