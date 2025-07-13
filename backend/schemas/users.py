from pydantic import BaseModel, EmailStr
from enum import Enum
from datetime import datetime
from typing import Optional, Dict


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"


class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.PENDING


class UserCreate(UserBase):
    password: str


class User(UserBase):
    created_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False
    full_name: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[Dict] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: str
