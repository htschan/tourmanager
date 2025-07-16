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

# Environment variables for authentication
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# JWT configuration
SECRET_KEY = get_jwt_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

def get_db():
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(db: Session, username: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(UserModel).filter(UserModel.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(UserModel).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=UserRole.USER,
        status=UserStatus.PENDING
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_status(db: Session, username: str, status: UserStatus):
    db_user = get_user(db, username)
    if db_user:
        db_user.status = status
        db.commit()
        db.refresh(db_user)
    return db_user

# Create initial admin user if not exists
def create_initial_admin(db: Session):
    admin = get_user(db, "admin")
    if not admin:
        admin = UserModel(
            username="admin",
            email="admin@example.com",
            hashed_password=pwd_context.hash("admin"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            email_verified=True,
            created_at=datetime.utcnow()
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info("Created initial admin user")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def change_user_password(db: Session, username: str, current_password: str, new_password: str) -> bool:
    db_user = get_user(db, username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(current_password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    db_user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True

async def change_password(
    password_change: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Change the password for the current user.
    Requires current password and new password.
    """
    try:
        success = change_user_password(
            db,
            current_user.username,
            password_change.current_password,
            password_change.new_password
        )
        return {"message": "Password changed successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def authenticate_user(db: Session, username: str, password: str) -> Optional[UserModel]:
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if user.status != UserStatus.ACTIVE:
        return None
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserModel:
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
        
    user = db.query(UserModel).filter(UserModel.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
