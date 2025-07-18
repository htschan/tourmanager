#!/usr/bin/env python3
"""
Fix for the main.py file to correct syntax errors
"""

import os
import sys

def main():
    main_py_path = "/home/hts/pj/komoot/backend/main.py"
    
    # Read the content of main.py
    with open(main_py_path, "r") as f:
        content = f.read()
    
    # Fix the logger initialization
    content = content.replace(
        "logger = logging.getLogger(__name    # Username, hash, and status are extracted above", 
        "logger = logging.getLogger(__name__)"
    )
    
    # Fix the HTTPException syntax error
    content = content.replace(
        """raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        }.setLevel(logging.INFO)""", 
        """raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )"""
    )
    
    # Write the corrected content back to main.py
    with open(main_py_path, "w") as f:
        f.write(content)
    
    print("Fixed syntax errors in main.py")

if __name__ == "__main__":
    main()
