from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from typing import List
import jwt
from datetime import datetime, timedelta
from auth import SECRET_KEY, ALGORITHM

# Email configuration
def get_mail_config() -> ConnectionConfig:
    required_settings = ["MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_FROM"]
    missing_settings = [setting for setting in required_settings if not os.getenv(setting)]
    
    if missing_settings:
        print(f"Warning: Missing required email settings: {', '.join(missing_settings)}")
        print("Email functionality will be disabled")
        return None
    
    return ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_FROM=os.getenv("MAIL_FROM"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True
    )

conf = get_mail_config()
fastmail = FastMail(conf) if conf else None

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
    
    verify_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={token}"
    
    if not fastmail:
        logger.warning(f"Email not configured. Verification email cannot be sent to {email}")
        logger.info(f"Verification URL for {email}: {verify_url}")
        return
    
    logger.info(f"Preparing verification email for {email}")
    
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
    
    try:
        logger.info(f"Sending verification email to {email}")
        await fastmail.send_message(message)
        logger.info(f"Verification email sent successfully to {email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
        # In development, print the verification URL to console
        logger.info(f"Verification URL: {verify_url}")

async def send_password_reset_email(email: str, token: str):
    if not fastmail:
        print(f"Email not configured. Password reset URL for {email}: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}")
        return
        
    reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}"
    
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
    
    try:
        await fastmail.send_message(message)
    except Exception as e:
        print(f"Failed to send password reset email to {email}: {str(e)}")
        # In development, print the reset URL to console
        print(f"Reset URL: {reset_url}")

async def send_account_approved_email(email: str):
    """
    Send an email to notify the user that their account has been approved by an admin.
    
    Args:
        email (str): The recipient's email address
    """
    from utils.logger import get_logger
    logger = get_logger(__name__)
    
    if not fastmail:
        logger.info(f"Email not configured. Account approval notification for {email} could not be sent")
        return
    
    login_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/login"
    
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
    
    try:
        logger.info(f"Sending account approval notification to {email}")
        await fastmail.send_message(message)
        logger.info(f"Account approval notification sent successfully to {email}")
    except Exception as e:
        logger.error(f"Failed to send account approval notification to {email}: {str(e)}")
        # In development, print the message
        logger.info(f"Account approval notification content would have been sent to {email}")
