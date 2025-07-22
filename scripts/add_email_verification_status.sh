#!/bin/bash

# This script adds the email verification status display to the users page

echo "🔧 Adding email verification status display to the users page..."

# 1. Update the backend schema to include email_verified in the response
echo "Step 1: Updating UserResponse schema in backend..."
BACKEND_SCHEMA_PATH="/app/schemas/users.py"

# Check if we can find the container
BACKEND_CONTAINER_ID=$(docker ps -q -f name=backend)
if [ -z "$BACKEND_CONTAINER_ID" ]; then
    echo "❌ Backend container not found! Make sure it's running."
    exit 1
fi

# Update the UserResponse schema
docker exec $BACKEND_CONTAINER_ID bash -c "sed -i 's/class UserResponse(UserBase):/class UserResponse(UserBase):/g' $BACKEND_SCHEMA_PATH"
docker exec $BACKEND_CONTAINER_ID bash -c "sed -i '/last_login: Optional\[datetime\] = None/a \    email_verified: bool = False' $BACKEND_SCHEMA_PATH"

echo "✅ Updated backend schema"

# 2. Update the frontend to display the email verification status
echo "Step 2: Updating frontend AdminDashboard.vue..."

# Find the frontend container
FRONTEND_CONTAINER_ID=$(docker ps -q -f name=frontend)
if [ -z "$FRONTEND_CONTAINER_ID" ]; then
    echo "❌ Frontend container not found! Make sure it's running."
    exit 1
fi

# Path to the AdminDashboard.vue file
FRONTEND_FILE_PATH="/app/src/views/AdminDashboard.vue"

# Update the template to display email verification status
docker exec $FRONTEND_CONTAINER_ID bash -c "sed -i '/<span :class=\"\['\''status-badge'\'', `status-\${user.status.toLowerCase()}`\]\">/,/<\/span>/s/<\/span>/<\/span>\\n              <span v-if=\"!user.email_verified\" class=\"email-pending-badge\">\\n                Email Confirmation Pending\\n              <\/span>/' $FRONTEND_FILE_PATH"

# Add CSS styling for the email pending badge
docker exec $FRONTEND_CONTAINER_ID bash -c "sed -i '/.users-table th {/,/}/s/}/}\\n\\n.email-pending-badge {\\n  display: block;\\n  margin-top: 0.5rem;\\n  font-size: 0.75rem;\\n  padding: 0.2rem 0.5rem;\\n  background-color: #fff3cd;\\n  color: #856404;\\n  border: 1px solid #ffeeba;\\n  border-radius: 4px;\\n  font-weight: 500;\\n}/' $FRONTEND_FILE_PATH"

echo "✅ Updated frontend component"

# Restart the containers to apply the changes
echo "Step 3: Restarting containers to apply changes..."
docker restart $BACKEND_CONTAINER_ID
docker restart $FRONTEND_CONTAINER_ID

echo "✅ Email verification status display has been added to the users page!"
echo "You can now see which users have pending email confirmations in the admin dashboard."
