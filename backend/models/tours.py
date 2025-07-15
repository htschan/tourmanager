from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from database import Base

class Tour(Base):
    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String)
    date = Column(String, nullable=False)  # Consider using DateTime in the future
    ebike = Column(Boolean, default=False)
    speed_kmh = Column(Float, default=0)
    distance_km = Column(Float)
    duration_s = Column(Float)
    elevation_up = Column(Float, default=0)
    elevation_down = Column(Float, default=0)
    start_lat = Column(Float)
    start_lon = Column(Float)
