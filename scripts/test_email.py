#!/usr/bin/env python
"""
Standalone script to test email configuration with Firestorm.ch

Usage:
    python test_email.py [recipient_email]

If recipient_email is not provided, the test email will be sent to the MAIL_FROM address.
"""

import asyncio
import sys
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("email_test")

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
except ImportError:
    logger.warning("dotenv module not found, skipping .env loading")
    logger.info("If you need to use .env files, install python-dotenv with pip")

# FastMail imports - handle gracefully if not installed
try:
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
    FASTMAIL_AVAILABLE = True
except ImportError:
    logger.error("fastapi_mail module not found. Please install it with pip install fastapi-mail")
    FASTMAIL_AVAILABLE = False

async def test_email_configuration(recipient_email=None):
    """
    Test the email configuration by sending a test email.
    Useful for verifying if the email server (like firestorm.ch) is properly configured.
    
    Args:
        recipient_email (str): Email address to receive the test email.
                              If None, will use the configured MAIL_FROM address.
                              
    Returns:
        dict: Results of the email sending attempt
    """
    logger.info("==== TESTING EMAIL CONFIGURATION ====")
    
    if not FASTMAIL_AVAILABLE:
        return {
            "success": False,
            "error": "fastapi_mail module not installed",
            "details": "Install with: pip install fastapi-mail"
        }
    
    # Log all environment variables related to email
    email_vars = {
        "MAIL_SERVER": os.getenv("MAIL_SERVER", "Not set"),
        "MAIL_PORT": os.getenv("MAIL_PORT", "Not set"),
        "MAIL_USERNAME": os.getenv("MAIL_USERNAME", "Not set"),
        "MAIL_PASSWORD": "******" if os.getenv("MAIL_PASSWORD") else "Not set",
        "MAIL_FROM": os.getenv("MAIL_FROM", "Not set"),
        "MAIL_STARTTLS": os.getenv("MAIL_STARTTLS", "True"),
        "MAIL_SSL_TLS": os.getenv("MAIL_SSL_TLS", "False"),
        "USE_CREDENTIALS": os.getenv("USE_CREDENTIALS", "True"),
    }
    
    for key, value in email_vars.items():
        logger.info(f"{key}: {value}")
    
    # Ensure we have the minimum required settings
    required_settings = ["MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_FROM", "MAIL_SERVER"]
    missing_settings = [setting for setting in required_settings if not os.getenv(setting)]
    
    if missing_settings:
        error_msg = f"Missing required email settings: {', '.join(missing_settings)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "details": "Check your .env file and ensure all required email variables are set"
        }
    
    # If no recipient is provided, use the sender address
    if not recipient_email:
        recipient_email = os.getenv("MAIL_FROM")
        logger.info(f"No recipient specified, using sender address: {recipient_email}")
    
    try:
        # Create mail configuration
        conf = ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
            MAIL_FROM=os.getenv("MAIL_FROM"),
            MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
            MAIL_SERVER=os.getenv("MAIL_SERVER"),
            MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() == "true",
            MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
            USE_CREDENTIALS=os.getenv("USE_CREDENTIALS", "True").lower() == "true"
        )
        
        # Create FastMail client
        logger.info(f"Initializing FastMail with server {os.getenv('MAIL_SERVER')}:{os.getenv('MAIL_PORT', '587')}")
        fastmail = FastMail(conf)
        
        # Create message
        message = MessageSchema(
            subject="Test Email from Tour Manager",
            recipients=[recipient_email],
            body=f"""
            <html>
                <body>
                    <h1>Email Configuration Test</h1>
                    <p>This is a test email from Tour Manager to verify your email configuration.</p>
                    <p>If you're seeing this, your email configuration with the following settings is working correctly:</p>
                    <ul>
                        <li>Server: {os.getenv('MAIL_SERVER')}</li>
                        <li>Port: {os.getenv('MAIL_PORT', '587')}</li>
                        <li>Sender: {os.getenv('MAIL_FROM')}</li>
                        <li>TLS Enabled: {os.getenv('MAIL_STARTTLS', 'True')}</li>
                    </ul>
                    <p>You can now use these settings for your application.</p>
                </body>
            </html>
            """,
            subtype="html"
        )
        
        # Send test email
        logger.info(f"Sending test email to {recipient_email}...")
        import time
        start_time = time.time()
        
        await fastmail.send_message(message)
        
        duration = time.time() - start_time
        success_msg = f"Test email sent successfully to {recipient_email} (took {duration:.2f}s)"
        logger.info(success_msg)
        logger.info("==== EMAIL TEST COMPLETED SUCCESSFULLY ====")
        
        return {
            "success": True,
            "message": success_msg,
            "recipient": recipient_email,
            "duration_seconds": duration,
            "config": {
                "server": os.getenv("MAIL_SERVER"),
                "port": os.getenv("MAIL_PORT", "587"),
                "from": os.getenv("MAIL_FROM"),
                "username": os.getenv("MAIL_USERNAME")
            }
        }
        
    except Exception as e:
        error_msg = f"Failed to send test email: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Error type: {type(e).__name__}")
        logger.info("==== EMAIL TEST FAILED ====")
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "recipient": recipient_email,
            "config": {
                "server": os.getenv("MAIL_SERVER"),
                "port": os.getenv("MAIL_PORT", "587"),
                "from": os.getenv("MAIL_FROM"),
                "username": os.getenv("MAIL_USERNAME")
            }
        }

async def main():
    # Get recipient email from command line argument if provided
    recipient_email = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("=== Testing Email Configuration ===")
    print(f"Recipient: {recipient_email or os.getenv('MAIL_FROM', 'Not set')}")
    
    # Run the test
    result = await test_email_configuration(recipient_email)
    
    # Print result
    if result['success']:
        print("\n✅ SUCCESS! Email sent successfully!")
        print(f"   Recipient: {result['recipient']}")
        print(f"   Server: {result['config']['server']}:{result['config']['port']}")
        if 'duration_seconds' in result:
            print(f"   Time taken: {result['duration_seconds']:.2f} seconds")
    else:
        print("\n❌ ERROR! Failed to send email.")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"   Server attempted: {result['config'].get('server', 'Unknown')}:{result['config'].get('port', 'Unknown')}")
        print("\nCheck your .env file and make sure your email configuration is correct.")
        print("If you're using Firestorm.ch, make sure you have the correct SMTP server settings.")

if __name__ == "__main__":
    asyncio.run(main())
