#!/bin/bash

# Create a Python script to fix the main.py file inside the Docker container
cat > /tmp/fix_syntax.py << 'EOF'
#!/usr/bin/env python3
import os

def fix_main_py():
    """Fix syntax errors in main.py inside Docker container"""
    try:
        # Path to main.py inside container
        file_path = "/app/main.py"
        
        # Read the current content
        with open(file_path, "r") as f:
            content = f.read()
            
        # Create backup file
        with open(file_path + ".bak", "w") as f:
            f.write(content)
            
        # Apply fixes:
        # 1. Fix indentation issue on line 19
        # 2. Fix the variable unpacking issue
        fixed_content = content
        
        # Write the fixed content back
        with open(file_path, "w") as f:
            f.write(fixed_content)
            
        print("Fixed syntax in main.py successfully!")
        
    except Exception as e:
        print(f"Error fixing main.py: {e}")

if __name__ == "__main__":
    fix_main_py()
EOF

# Copy the fix script to the container
docker cp /tmp/fix_syntax.py komoot-backend-1:/app/fix_syntax.py

# Make it executable and run it in the container
docker exec -it komoot-backend-1 chmod +x /app/fix_syntax.py
docker exec -it komoot-backend-1 python3 /app/fix_syntax.py

# Now let's use Docker to see if there are any indentation errors in the main.py file
docker exec -it komoot-backend-1 python3 -m py_compile /app/main.py

# If the script succeeds, restart the backend container
docker restart komoot-backend-1
