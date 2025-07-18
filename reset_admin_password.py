from passlib.context import CryptContext
import sqlite3
import os

# Setup password context (same as in auth.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generate hash for default password
default_password = "admin123"
hashed_password = pwd_context.hash(default_password)
print(f"Generated hash for password '{default_password}': {hashed_password}")

# Get database path
if os.getenv("DOCKER_ENV") == "true":
    db_path = "/app/data/tourmanager.db"
else:
    db_path = "./tourmanager.db"
db_path = os.getenv("DATABASE_PATH", db_path)

try:
    # Connect to database
    print(f"Connecting to database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update admin password
    cursor.execute("UPDATE users SET hashed_password = ? WHERE username = ?", (hashed_password, "admin"))
    rows_affected = cursor.rowcount
    
    if rows_affected > 0:
        print(f"Password reset successful. {rows_affected} user(s) updated.")
        conn.commit()
    else:
        print("Admin user not found. No password was reset.")
    
    # Verify admin exists
    cursor.execute("SELECT username FROM users WHERE username = ?", ("admin",))
    admin = cursor.fetchone()
    if admin:
        print(f"Admin user '{admin[0]}' exists in the database.")
    else:
        print("Admin user does not exist in the database.")
    
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    if 'conn' in locals():
        conn.close()
