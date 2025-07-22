#!/bin/bash

# Master fix script for Tour Manager application
# This script consolidates all fixes and applies them as needed

# ===== CONFIGURATION =====
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
BACKEND_CONTAINER=$(docker ps -q -f name=backend)
FRONTEND_CONTAINER=$(docker ps -q -f name=frontend)
SUCCESS_COUNT=0
FAILED_COUNT=0
LOG_FILE="$SCRIPT_DIR/fix_application.log"

# ===== UTILITY FUNCTIONS =====

# Print colored text
print_green() { echo -e "\033[0;32m$1\033[0m"; }
print_yellow() { echo -e "\033[0;33m$1\033[0m"; }
print_red() { echo -e "\033[0;31m$1\033[0m"; }
print_blue() { echo -e "\033[0;34m$1\033[0m"; }

# Log message to console and log file
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

log_success() {
    print_green "✅ $1" | tee -a "$LOG_FILE"
    ((SUCCESS_COUNT++))
}

log_warning() {
    print_yellow "⚠️ $1" | tee -a "$LOG_FILE"
}

log_error() {
    print_red "❌ $1" | tee -a "$LOG_FILE"
    ((FAILED_COUNT++))
}

log_info() {
    print_blue "ℹ️ $1" | tee -a "$LOG_FILE"
}

# Check if containers are running
check_containers() {
    log_info "Checking if containers are running..."
    
    if [ -z "$BACKEND_CONTAINER" ]; then
        log_error "Backend container is not running! Some fixes may fail."
    else
        log_success "Backend container found: $BACKEND_CONTAINER"
    fi
    
    if [ -z "$FRONTEND_CONTAINER" ]; then
        log_error "Frontend container is not running! Some fixes may fail."
    else
        log_success "Frontend container found: $FRONTEND_CONTAINER"
    fi
}

# ===== FIXES =====

# Fix 1: Email Configuration
fix_email_config() {
    log_info "Applying email configuration fix..."
    
    if [ -z "$BACKEND_CONTAINER" ]; then
        log_error "Cannot apply email configuration fix: Backend container not found"
        return 1
    fi
    
    # Copy the fixed email.py file into the container
    docker cp "$SCRIPT_DIR/fixes/patches/email.py" "$BACKEND_CONTAINER:/app/utils/email.py" 2>> "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        log_success "Email configuration fix applied successfully"
    else
        log_error "Failed to apply email configuration fix"
        return 1
    fi
}

# Fix 2: ResponseValidation Error
fix_response_validation() {
    log_info "Applying response validation fix..."
    
    if [ -z "$BACKEND_CONTAINER" ]; then
        log_error "Cannot apply response validation fix: Backend container not found"
        return 1
    fi
    
    # Copy the fixed_users.py to the container
    docker cp "$SCRIPT_DIR/fixes/patches/fixed_users.py" "$BACKEND_CONTAINER:/app/fixed_users.py" 2>> "$LOG_FILE"
    
    if [ $? -ne 0 ]; then
        log_error "Failed to copy fixed_users.py"
        return 1
    fi
    
    # Update the main.py to use the fixed_users module
    docker exec "$BACKEND_CONTAINER" bash -c 'sed -i "s/@app\.get(\"\/api\/users\".*/@app.get(\"\/api\/users\")/g" /app/main.py' 2>> "$LOG_FILE"
    docker exec "$BACKEND_CONTAINER" bash -c 'sed -i "s/def list_users([^:]*):.*def list_users\1:\n    from fixed_users import bypass_users\n    return bypass_users(current_user, db, UserModel, UserRole)/g" /app/main.py' 2>> "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        log_success "Response validation fix applied successfully"
    else
        log_error "Failed to apply response validation fix"
        return 1
    fi
}

# Fix 3: User Roles Case Sensitivity
fix_user_roles() {
    log_info "Applying user roles case sensitivity fix..."
    
    if [ -z "$BACKEND_CONTAINER" ]; then
        log_error "Cannot apply user roles fix: Backend container not found"
        return 1
    fi
    
    # Copy the fixed users.py model
    docker cp "$SCRIPT_DIR/fixes/patches/users.py" "$BACKEND_CONTAINER:/app/models/users.py" 2>> "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        log_success "User roles case sensitivity fix applied successfully"
    else
        log_error "Failed to apply user roles case sensitivity fix"
        return 1
    fi
}

# Feature: Email Verification Status Display
add_email_verification_status() {
    log_info "Adding email verification status display..."
    
    if [ -z "$BACKEND_CONTAINER" ]; then
        log_error "Cannot add email verification status: Backend container not found"
        return 1
    fi
    
    if [ -z "$FRONTEND_CONTAINER" ]; then
        log_error "Cannot add email verification status: Frontend container not found"
        return 1
    fi
    
    # Update backend schema
    docker cp "$SCRIPT_DIR/features/user_response_schema.py" "$BACKEND_CONTAINER:/app/schemas/users.py" 2>> "$LOG_FILE"
    
    if [ $? -ne 0 ]; then
        log_error "Failed to update backend schema"
        return 1
    fi
    
    # Update frontend component
    docker cp "$SCRIPT_DIR/features/AdminDashboard.vue" "$FRONTEND_CONTAINER:/app/src/views/AdminDashboard.vue" 2>> "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        log_success "Email verification status display added successfully"
    else
        log_error "Failed to add email verification status display"
        return 1
    fi
}

# ===== MAIN EXECUTION =====

# Initialize log file
echo "=== Tour Manager Fix Application Log $(date) ===" > "$LOG_FILE"
echo "================================================" >> "$LOG_FILE"

print_blue "
█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█ Tour Manager Fixer  █
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
"

log_info "Starting application fix process..."

# Check if containers are running
check_containers

# Ask which fixes to apply
echo ""
log_info "Which fixes would you like to apply?"
echo "1) Email Configuration Fix"
echo "2) Response Validation Fix"
echo "3) User Roles Case Sensitivity Fix"
echo "4) Add Email Verification Status Display"
echo "5) Apply All Fixes"
echo "0) Exit"
echo ""

read -p "Enter your choice (0-5): " choice

case $choice in
    1)
        fix_email_config
        ;;
    2)
        fix_response_validation
        ;;
    3)
        fix_user_roles
        ;;
    4)
        add_email_verification_status
        ;;
    5)
        log_info "Applying all fixes..."
        fix_email_config
        fix_response_validation
        fix_user_roles
        add_email_verification_status
        ;;
    0)
        log_info "Exiting without changes."
        exit 0
        ;;
    *)
        log_error "Invalid choice. Exiting."
        exit 1
        ;;
esac

# Restart containers to apply changes
if [ ! -z "$BACKEND_CONTAINER" ]; then
    log_info "Restarting backend container to apply changes..."
    docker restart "$BACKEND_CONTAINER"
    log_success "Backend container restarted"
fi

if [ ! -z "$FRONTEND_CONTAINER" ]; then
    log_info "Restarting frontend container to apply changes..."
    docker restart "$FRONTEND_CONTAINER"
    log_success "Frontend container restarted"
fi

# Print summary
echo ""
log_info "====== Fix Application Summary ======"
log_success "Successful operations: $SUCCESS_COUNT"

if [ $FAILED_COUNT -gt 0 ]; then
    log_error "Failed operations: $FAILED_COUNT"
    log_info "Check the log file for details: $LOG_FILE"
else
    log_success "All operations completed successfully!"
fi

echo ""
log_info "Application fixes have been applied. The application should now function correctly."
