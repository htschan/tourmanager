"""
Database fixes and utilities for handling enum value inconsistencies.
Also includes utility functions for testing system configuration.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from models.users import UserRole, User as UserModel
import logging
import os
import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

logger = logging.getLogger(__name__)

def fix_user_role_case_sensitivity(db: Session):
    """
    Fix case sensitivity issues with UserRole enum values in the database.
    
    This function:
    1. Logs current user roles to identify inconsistencies
    2. Updates any lowercase 'user' values to 'USER' 
    3. Updates any lowercase 'admin' values to 'ADMIN'
    
    Args:
        db (Session): SQLAlchemy database session
    
    Returns:
        int: Number of records updated
    """
    try:
        # First, log all existing roles for debugging
        users = db.query(UserModel).all()
        logger.info(f"Current users in database: {len(users)}")
        
        for user in users:
            logger.info(f"User {user.username}: role={user.role} (type: {type(user.role)})")
        
        # Count values before update
        raw_data = db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'user'")).scalar()
        logger.info(f"Found {raw_data} users with lowercase 'user' role")
        
        raw_data = db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin'")).scalar()
        logger.info(f"Found {raw_data} users with lowercase 'admin' role")
        
        # Update lowercase values to uppercase
        result1 = db.execute(text("UPDATE users SET role = 'USER' WHERE role = 'user'"))
        result2 = db.execute(text("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'"))
        
        db.commit()
        
        total_updated = result1.rowcount + result2.rowcount
        logger.info(f"Updated {total_updated} user records to fix role case sensitivity")
        
        return total_updated
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error fixing user roles: {str(e)}", exc_info=True)
        raise


async def test_email_configuration(recipient_email: str = None):
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
        await fastmail.send_message(message)
        
        success_msg = f"Test email sent successfully to {recipient_email}"
        logger.info(success_msg)
        logger.info("==== EMAIL TEST COMPLETED SUCCESSFULLY ====")
        
        return {
            "success": True,
            "message": success_msg,
            "recipient": recipient_email,
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
