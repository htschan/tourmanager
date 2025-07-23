from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from typing import List
import jwt
from datetime import datetime, timedelta
from auth import SECRET_KEY, ALGORITHM

# Email configuration
def get_mail_config() -> ConnectionConfig:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    
    logger.info("==== INITIALIZING EMAIL CONFIGURATION ====")
    
    required_settings = ["MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_FROM"]
    missing_settings = [setting for setting in required_settings if not os.getenv(setting)]
    
    # Log environment variables (safely)
    logger.info("Email environment variables:")
    logger.info(f"  - MAIL_USERNAME: {'✓ Set' if os.getenv('MAIL_USERNAME') else '✗ Missing'}")
    logger.info(f"  - MAIL_PASSWORD: {'✓ Set (hidden)' if os.getenv('MAIL_PASSWORD') else '✗ Missing'}")
    logger.info(f"  - MAIL_FROM: {os.getenv('MAIL_FROM') or '✗ Missing'}")
    logger.info(f"  - MAIL_PORT: {os.getenv('MAIL_PORT', '587 (default)')}")
    logger.info(f"  - MAIL_SERVER: {os.getenv('MAIL_SERVER', 'smtp.gmail.com (default)')}")
    logger.info(f"  - MAIL_STARTTLS: True (hardcoded)")
    logger.info(f"  - MAIL_SSL_TLS: False (hardcoded)")
    logger.info(f"  - USE_CREDENTIALS: True (hardcoded)")
    logger.info(f"  - FRONTEND_URL: {os.getenv('FRONTEND_URL', 'http://localhost:3000 (default)')}")
    
    if missing_settings:
        logger.warning(f"Missing required email settings: {', '.join(missing_settings)}")
        logger.warning("Email functionality will be disabled")
        logger.info("==== EMAIL CONFIGURATION FAILED ====")
        return None
    
    try:
        config = ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
            MAIL_FROM=os.getenv("MAIL_FROM"),
            MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
            MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True
        )
        logger.info("Email configuration successfully created")
        logger.info("==== EMAIL CONFIGURATION COMPLETED ====")
        return config
    except Exception as e:
        logger.error(f"Failed to create email configuration: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.info("==== EMAIL CONFIGURATION FAILED ====")
        return None

# Initialize email client with detailed logging
from utils.logger import get_logger
logger = get_logger(__name__)

try:
    logger.info("Initializing FastMail client...")
    conf = get_mail_config()
    fastmail = FastMail(conf) if conf else None
    
    if fastmail:
        logger.info("FastMail client initialized successfully")
    else:
        logger.warning("FastMail client not initialized (no configuration)")
except Exception as e:
    logger.error(f"Failed to initialize FastMail client: {str(e)}")
    logger.error(f"Error type: {type(e).__name__}")
    fastmail = None

def create_verification_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode(
        {"exp": expire, "email": email},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def create_password_reset_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=1)
    return jwt.encode(
        {"exp": expire, "email": email, "type": "reset"},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("email")
    except:
        return None

async def send_verification_email(email: str, token: str):
    from utils.logger import get_logger
    logger = get_logger(__name__)
    
    # Detailed parameter logging
    logger.info("==== EMAIL VERIFICATION REQUESTED ====")
    logger.info(f"Parameters received:")
    logger.info(f"  - Email: {email}")
    logger.info(f"  - Token length: {len(token)} chars")
    logger.info(f"  - Token first 10 chars: {token[:10]}...")
    
    # Log environment variables used
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    logger.info(f"Email configuration:")
    logger.info(f"  - FRONTEND_URL: {frontend_url}")
    logger.info(f"  - MAIL_SERVER: {os.getenv('MAIL_SERVER', 'Not configured')}")
    logger.info(f"  - MAIL_PORT: {os.getenv('MAIL_PORT', 'Not configured')}")
    logger.info(f"  - MAIL_FROM: {os.getenv('MAIL_FROM', 'Not configured')}")
    logger.info(f"  - MAIL_USERNAME: {os.getenv('MAIL_USERNAME', 'Not configured')}")
    
    verify_url = f"{frontend_url}/verify-email?token={token}"
    
    if not fastmail:
        logger.warning(f"Email not configured. Verification email cannot be sent to {email}")
        logger.info(f"Verification URL for {email}: {verify_url}")
        logger.info("==== EMAIL VERIFICATION SKIPPED (No configuration) ====")
        return
    
    logger.info(f"Preparing verification email for {email}")
    
    # Create message
    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=f"""
        <html>
            <body>
                <h1>Verify your email address</h1>
                <p>Click the link below to verify your email address:</p>
                <p><a href="{verify_url}">Verify Email</a></p>
                <p>This link will expire in 24 hours.</p>
                <p>After verification, an administrator will review and approve your account.</p>
            </body>
        </html>
        """,
        subtype="html"
    )
    
    # Log message details
    logger.info(f"Email content prepared:")
    logger.info(f"  - Subject: {message.subject}")
    logger.info(f"  - Recipients: {message.recipients}")
    logger.info(f"  - Verify URL: {verify_url}")
    
    try:
        logger.info(f"Attempting to send verification email to {email}...")
        start_time = datetime.utcnow()
        
        await fastmail.send_message(message)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Email sent successfully to {email} (took {duration:.2f}s)")
        logger.info("==== EMAIL VERIFICATION COMPLETED SUCCESSFULLY ====")
        
        return {
            "success": True,
            "email": email,
            "verify_url": verify_url,
            "duration_seconds": duration
        }
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        
        # In development, print the verification URL to console
        logger.info(f"Verification URL: {verify_url}")
        logger.info("==== EMAIL VERIFICATION FAILED ====")
        
        return {
            "success": False,
            "email": email,
            "verify_url": verify_url,
            "error": str(e),
            "error_type": type(e).__name__
        }

async def send_password_reset_email(email: str, token: str):
    from utils.logger import get_logger
    logger = get_logger(__name__)
    
    # Detailed parameter logging
    logger.info("==== PASSWORD RESET EMAIL REQUESTED ====")
    logger.info(f"Parameters received:")
    logger.info(f"  - Email: {email}")
    logger.info(f"  - Token length: {len(token)} chars")
    logger.info(f"  - Token first 10 chars: {token[:10]}...")
    
    # Log environment variables used
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    logger.info(f"Email configuration:")
    logger.info(f"  - FRONTEND_URL: {frontend_url}")
    
    reset_url = f"{frontend_url}/reset-password?token={token}"
    
    if not fastmail:
        logger.warning(f"Email not configured. Password reset email cannot be sent to {email}")
        logger.info(f"Password reset URL for {email}: {reset_url}")
        logger.info("==== PASSWORD RESET EMAIL SKIPPED (No configuration) ====")
        return
        
    # Create message
    message = MessageSchema(
        subject="Reset your password",
        recipients=[email],
        body=f"""
        <html>
            <body>
                <h1>Reset your password</h1>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """,
        subtype="html"
    )
    
    # Log message details
    logger.info(f"Email content prepared:")
    logger.info(f"  - Subject: {message.subject}")
    logger.info(f"  - Recipients: {message.recipients}")
    logger.info(f"  - Reset URL: {reset_url}")
    
    try:
        logger.info(f"Attempting to send password reset email to {email}...")
        start_time = datetime.utcnow()
        
        await fastmail.send_message(message)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Password reset email sent successfully to {email} (took {duration:.2f}s)")
        logger.info("==== PASSWORD RESET EMAIL COMPLETED SUCCESSFULLY ====")
        
        return {
            "success": True,
            "email": email,
            "reset_url": reset_url,
            "duration_seconds": duration
        }
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        
        # In development, print the reset URL to console
        logger.info(f"Reset URL: {reset_url}")
        logger.info("==== PASSWORD RESET EMAIL FAILED ====")
        
        return {
            "success": False,
            "email": email,
            "reset_url": reset_url,
            "error": str(e),
            "error_type": type(e).__name__
        }

async def send_account_approved_email(email: str):
    """
    Send an email to notify the user that their account has been approved by an admin.
    
    Args:
        email (str): The recipient's email address
    """
    from utils.logger import get_logger
    logger = get_logger(__name__)
    
    # Detailed parameter logging
    logger.info("==== ACCOUNT APPROVAL EMAIL REQUESTED ====")
    logger.info(f"Parameters received:")
    logger.info(f"  - Email: {email}")
    
    # Log environment variables used
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    logger.info(f"Email configuration:")
    logger.info(f"  - FRONTEND_URL: {frontend_url}")
    
    if not fastmail:
        logger.warning(f"Email not configured. Account approval notification for {email} could not be sent")
        logger.info("==== ACCOUNT APPROVAL EMAIL SKIPPED (No configuration) ====")
        return
    
    login_url = f"{frontend_url}/login"
    
    # Create message
    message = MessageSchema(
        subject="Your Account Has Been Approved",
        recipients=[email],
        body=f"""
        <html>
            <body>
                <h1>Account Approved</h1>
                <p>Your account has been approved by an administrator.</p>
                <p>You can now <a href="{login_url}">log in</a> to access the application.</p>
                <p>Thank you for your patience.</p>
            </body>
        </html>
        """,
        subtype="html"
    )
    
    # Log message details
    logger.info(f"Email content prepared:")
    logger.info(f"  - Subject: {message.subject}")
    logger.info(f"  - Recipients: {message.recipients}")
    logger.info(f"  - Login URL: {login_url}")
    
    try:
        logger.info(f"Attempting to send account approval email to {email}...")
        start_time = datetime.utcnow()
        
        await fastmail.send_message(message)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Account approval email sent successfully to {email} (took {duration:.2f}s)")
        logger.info("==== ACCOUNT APPROVAL EMAIL COMPLETED SUCCESSFULLY ====")
        
        return {
            "success": True,
            "email": email,
            "login_url": login_url,
            "duration_seconds": duration
        }
    except Exception as e:
        logger.error(f"Failed to send account approval notification to {email}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        
        # In development, print the message
        logger.info(f"Account approval notification content would have been sent to {email}")
        logger.info("==== ACCOUNT APPROVAL EMAIL FAILED ====")
        
        return {
            "success": False,
            "email": email,
            "login_url": login_url,
            "error": str(e),
            "error_type": type(e).__name__
        }
