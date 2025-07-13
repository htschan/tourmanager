from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.username"))
    action = Column(String, nullable=False)  # LOGIN, PROFILE_UPDATE, PASSWORD_CHANGE, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)  # Additional action details

    # Relationship
    user = relationship("User", back_populates="activities")
