#!/bin/bash

# Script to apply the direct fix to main.py in the container
# Run this script with: docker-compose exec backend /scripts/apply_enum_fix.sh

echo "Applying enum fix to handle case sensitivity..."

# Create a direct fix for the main.py file
cat > /app/enum_fix.py << 'EOF'
"""
Direct fix for user role enum handling
"""
import enum
from sqlalchemy import event
from sqlalchemy.engine import Engine
from utils.logger import get_logger

logger = get_logger(__name__)

class CaseInsensitiveEnum(enum.Enum):
    """
    Enum class that handles case-insensitive comparison
    """
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    logger.info(f"Converting enum value from '{value}' to '{member.value}'")
                    return member
        return None

# Apply direct fixes to the database
def fix_db_enums(db_session):
    """Fix enum values in the database"""
    try:
        # Execute direct SQL to fix the values
        result = db_session.execute("UPDATE users SET role = 'USER' WHERE role = 'user'")
        users_fixed = result.rowcount
        
        result = db_session.execute("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'")
        admins_fixed = result.rowcount
        
        total_fixed = users_fixed + admins_fixed
        if total_fixed > 0:
            logger.info(f"Fixed {total_fixed} user role records in the database")
        
        # Commit the changes
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to fix enum values: {str(e)}", exc_info=True)
EOF

# Create patch instructions
cat > /app/apply_patch.py << 'EOF'
"""
Script to patch the main.py file
"""
import os
import re
import sys
import shutil
from utils.logger import get_logger

logger = get_logger("patch_script")

def patch_main_py():
    """Apply patch to main.py to add the CaseInsensitiveEnum"""
    try:
        # Backup the original file
        shutil.copy('/app/main.py', '/app/main.py.bak')
        logger.info("Created backup of main.py")
        
        # Read the original file
        with open('/app/main.py', 'r') as f:
            content = f.read()
        
        # Add import for enum_fix
        if "from enum_fix import CaseInsensitiveEnum, fix_db_enums" not in content:
            import_pattern = r"from models.users import User as UserModel, UserRole, UserStatus"
            new_import = "from models.users import User as UserModel, UserStatus\nfrom enum_fix import CaseInsensitiveEnum, fix_db_enums\n\n# Patch UserRole to use case insensitive enum\nclass UserRole(CaseInsensitiveEnum):\n    ADMIN = \"admin\"\n    USER = \"user\"\n"
            content = re.sub(import_pattern, new_import, content)
            
        # Add database fix to startup event
        if "fix_db_enums" not in content:
            startup_pattern = r"async def startup_event\(\):\s+create_initial_admin\(\)"
            new_startup = "async def startup_event():\n    create_initial_admin()\n    \n    # Fix database enum values\n    with SessionLocal() as db:\n        fix_db_enums(db)\n        logger.info('Applied enum fixes to database')"
            content = re.sub(startup_pattern, new_startup, content)
        
        # Write the modified file
        with open('/app/main.py', 'w') as f:
            f.write(content)
        
        logger.info("Successfully patched main.py file")
        return True
    except Exception as e:
        logger.error(f"Failed to patch main.py: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if patch_main_py():
        print("✅ Successfully applied patch to main.py")
        sys.exit(0)
    else:
        print("❌ Failed to apply patch to main.py")
        sys.exit(1)
EOF

# Apply the patch
echo "Running patch script..."
python /app/apply_patch.py

# Restart the uvicorn service to apply changes
echo "Restarting the application..."
pkill -f "uvicorn main:app"

echo "Fix applied. The application will restart automatically due to the container's restart policy."
