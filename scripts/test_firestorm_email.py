#!/usr/bin/env python
"""
Script to test email configuration with Firestorm.ch

Usage:
    python test_firestorm_email.py [recipient_email]

If recipient_email is not provided, the test email will be sent to the MAIL_FROM address.

This script helps verify if your email configuration with Firestorm.ch works correctly.
"""

import asyncio
import sys
import os

# Fix the Python import path to work both inside and outside Docker
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("dotenv module not found, skipping .env loading")
    print("If you need to use .env files, install python-dotenv with pip")

async def main():
    try:
        # First try direct import (when running from project root)
        from backend.utils.db_fixes import test_email_configuration
    except ImportError:
        # If that fails, try relative import (when running from scripts dir)
        sys.path.append(os.path.join(parent_dir, "backend"))
        try:
            from utils.db_fixes import test_email_configuration
        except ImportError:
            print("ERROR: Could not import test_email_configuration function.")
            print("Make sure you're running this script from the project root or scripts directory.")
            print("Current directory structure:")
            for path in sys.path:
                print(f"  - {path}")
            sys.exit(1)
    
    # Get recipient email from command line argument if provided
    recipient_email = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("=== Testing Firestorm.ch Email Configuration ===")
    print(f"Recipient: {recipient_email or os.getenv('MAIL_FROM', 'Not set')}")
    
    # Run the test
    result = await test_email_configuration(recipient_email)
    
    # Print result
    if result['success']:
        print("\n✅ SUCCESS! Email sent successfully!")
        print(f"   Recipient: {result['recipient']}")
        print(f"   Server: {result['config']['server']}:{result['config']['port']}")
    else:
        print("\n❌ ERROR! Failed to send email.")
        print(f"   Error: {result['error']}")
        print(f"   Server attempted: {result['config']['server']}:{result['config']['port']}")
        print("\nCheck your .env file and make sure your email configuration is correct.")
        print("If you're using Firestorm.ch, make sure you have the correct SMTP server settings.")

if __name__ == "__main__":
    asyncio.run(main())
