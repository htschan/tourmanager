from database import SessionLocal
from auth import create_initial_admin

def init_db():
    db = SessionLocal()
    try:
        create_initial_admin(db)
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized with admin user")
