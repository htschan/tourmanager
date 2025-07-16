from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from models.users import User as UserModel, UserRole, UserStatus
from schemas.users import User, UserCreate, UserInDB, UserBase
from database import SessionLocal

# Environment variables for authentication
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
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

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    status: Optional[str] = None

class UserResponse(BaseModel):
    username: str
    email: EmailStr
    role: str
    status: str
    created_at: datetime
    last_login: Optional[datetime] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

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
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_initial_admin(db: Session = None):
    """
    Create initial admin user if it doesn't exist.
    Uses environment variables ADMIN_USERNAME, ADMIN_PASSWORD, and ADMIN_EMAIL.
    Falls back to default values if environment variables are not set.
    """
    if db is None:
        db = SessionLocal()

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
                created_at=datetime.utcnow()
            )
            
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
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
    
    user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
