from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Determine the environment
ENV = os.getenv("ENV", "development")

# Set default database path based on environment
if ENV == "test":
    # For tests, use an in-memory database by default
    default_db_path = ":memory:"
elif os.getenv("DOCKER_ENV") == "true":
    default_db_path = "/app/data/tourmanager.db"
else:
    default_db_path = "./tourmanager.db"

DATABASE_PATH = os.getenv("DATABASE_PATH", default_db_path)

# Only create directories if we're not using an in-memory database
if DATABASE_PATH != ":memory:":
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir:  # Only try to create directory if path contains a directory part
        try:
            os.makedirs(db_dir, exist_ok=True)
        except PermissionError:
            # If we can't create the directory, fall back to current directory
            DATABASE_PATH = "./test.db"

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed only for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database and create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise
