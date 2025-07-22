from sqlalchemy import Boolean, Column, String, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

class CaseInsensitiveEnum(enum.Enum):
    """Base enum class that provides case-insensitive value comparison"""
    
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            # Look for a case-insensitive match
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None

class UserRole(CaseInsensitiveEnum):
    ADMIN = "admin"
    USER = "user"

class UserStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"

class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.USER)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    # Profile fields
    full_name = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    preferences = Column(JSON, nullable=True)
    avatar_url = Column(String, nullable=True)

    # Relationships
    activities = relationship("UserActivity", back_populates="user")

class UserActivity(Base):
    __tablename__ = "user_activities"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="activities")
