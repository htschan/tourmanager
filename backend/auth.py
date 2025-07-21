from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models.users import User as UserModel, UserRole, UserStatus
from schemas.users import UserCreate, UserResponse, UserUpdate, UserInDB
from schemas.auth import Token, TokenData, PasswordChangeRequest
from database import SessionLocal

# Environment variables for authentication
import os
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# JWT configuration
def get_jwt_secret_key():
    secret_key_file = os.getenv("JWT_SECRET_KEY_FILE")
    if secret_key_file and os.path.exists(secret_key_file):
        with open(secret_key_file, 'r') as f:
            secret = f.read().strip()
            logger.info(f"JWT secret loaded from file: {secret_key_file}")
            logger.info(f"JWT secret preview: {secret[:4]}{'*' * 20}")
            return secret
    secret = os.getenv("JWT_SECRET_KEY", "your-secure-secret-key-here")
    logger.info(f"JWT secret loaded from environment variable")
    logger.info(f"JWT secret preview: {secret[:4]}{'*' * 20}")
    return secret

SECRET_KEY = get_jwt_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: Session, username: str):
    return db.query(UserModel).filter(UserModel.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(UserModel).filter(UserModel.email == email).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserModel = Depends(get_current_user)):
    from utils.logger import get_logger
    logger = get_logger(__name__)
    
    # Admin users always bypass email verification
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    
    # Check if user's email is verified (skip check for admin user)
    if not current_user.email_verified and current_user.username != admin_username:
        logger.warning(f"User {current_user.username} attempted to access with unverified email")
        raise HTTPException(
            status_code=401, 
            detail="Email not verified. Please verify your email before accessing this resource."
        )
    
    # Check if user is active (approved by admin)
    if current_user.status != UserStatus.ACTIVE:
        if current_user.status == UserStatus.PENDING:
            logger.warning(f"Pending user {current_user.username} attempted to access resources")
            raise HTTPException(
                status_code=401, 
                detail="Your account is awaiting admin approval. You will be notified once approved."
            )
        else:
            logger.warning(f"Inactive user {current_user.username} attempted to access resources")
            raise HTTPException(
                status_code=401, 
                detail="Your account is inactive. Please contact an administrator."
            )
    
    return current_user

def authenticate_user(db: Session, username: str, password: str):
    from utils.logger import get_logger
    logger = get_logger(__name__)
    
    user = get_user(db, username)
    
    # Check if user exists and password is correct
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Failed login attempt for username: {username}")
        return False
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info(f"User {username} authenticated successfully")
    return user

def create_initial_admin(db: Session = None):
    """
    Create initial admin user if it doesn't exist.
    Uses environment variables ADMIN_USERNAME, ADMIN_PASSWORD, and ADMIN_EMAIL.
    Falls back to default values if environment variables are not set.
    """
    try:
        from utils.logger import get_logger
        logger = get_logger("admin_setup")
    except ImportError:
        # Fallback to basic logging if logger module is not available yet
        import logging
        logger = logging.getLogger("admin_setup")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        logger.addHandler(handler)
    
    if db is None:
        db = SessionLocal()
        
    logger.info("Checking for admin user existence")

    try:
        # Check if admin user already exists
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin = get_user(db, username=admin_username)
        
        if not admin:
            # Create admin user
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")  # Default password should be changed immediately
            admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
            
            admin = UserModel(
                username=admin_username,
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                email_verified=True,  # Admin is automatically verified
                created_at=datetime.utcnow()
            )
            logger.info(f"Creating initial admin user: {admin_username}")
            
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
            logger.info(f"Initial admin user created successfully with email: {admin_email}")
            
            logger.info(f"Created initial admin user: {admin_username}")
        else:
            logger.info(f"Admin user already exists: {admin_username}")
            
        return admin
    
    except Exception as e:
        logger.error(f"Error creating initial admin user: {str(e)}")
        db.rollback()
        raise
    finally:
        if db:
            db.close()

async def change_password(password_change: PasswordChangeRequest, user: UserModel, db: Session):
    """Change user password"""
    if not verify_password(password_change.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    logger.info(f"Changing password for user: {user.username}")
    
    try:
        # Generate new password hash
        new_hash = get_password_hash(password_change.new_password)
        logger.info(f"New hash generated: {new_hash[:20]}...")
        
        # Use direct SQLite access for maximum reliability
        import sqlite3
        import os
        
        # Get database path from environment variables (same as in database.py)
        ENV = os.getenv("ENV", "development")
        if ENV == "test":
            default_db_path = ":memory:"
        elif os.getenv("DOCKER_ENV") == "true":
            default_db_path = "/app/data/tourmanager.db"
        else:
            default_db_path = "./tourmanager.db"
            
        db_path = os.getenv("DATABASE_PATH", default_db_path)
        logger.info(f"Using database path: {db_path}")
        
        # Connect directly to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update password
        cursor.execute("UPDATE users SET hashed_password = ? WHERE username = ?", 
                      (new_hash, user.username))
        rows_affected = cursor.rowcount
        logger.info(f"Rows affected by update: {rows_affected}")
        
        if rows_affected == 0:
            logger.error(f"No rows updated for user {user.username}")
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password - user not found"
            )
        
        # Commit changes
        conn.commit()
        
        # Verify the update worked
        cursor.execute("SELECT hashed_password FROM users WHERE username = ?", (user.username,))
        updated_hash = cursor.fetchone()[0]
        logger.info(f"Updated hash in database: {updated_hash[:20]}...")
        
        # Verify authentication works with new password
        verification_result = verify_password(password_change.new_password, updated_hash)
        logger.info(f"Password verification result: {verification_result}")
        
        if not verification_result:
            logger.error("Password verification failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password update succeeded but verification failed"
            )
        
        conn.close()
        
        # Also update the user model in memory
        user.hashed_password = new_hash
        
        return {"message": "Password updated successfully"}
            
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        try:
            if 'conn' in locals() and conn:
                conn.close()
            if 'db' in locals() and db:
                db.rollback()
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {str(e)}"
        )
