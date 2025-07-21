"""
Direct fix for user role enum issues in SQLAlchemy.
This file will be mounted directly into the container.
"""
from sqlalchemy import event, inspect, Column
from sqlalchemy.ext.declarative import declarative_base
import logging

logger = logging.getLogger(__name__)

def apply_enum_fixes(engine):
    """
    Apply direct fixes to database for enum values.
    
    Args:
        engine: SQLAlchemy engine connected to the database
    """
    try:
        # Connect directly to the database and fix the user role values
        with engine.begin() as conn:
            # Check if there are any lowercase 'user' values
            result = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
            user_count = result.scalar()
            
            if user_count > 0:
                logger.info(f"Found {user_count} users with lowercase 'user' role, fixing...")
                conn.execute("UPDATE users SET role = 'USER' WHERE role = 'user'")
            
            # Check if there are any lowercase 'admin' values
            result = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = result.scalar()
            
            if admin_count > 0:
                logger.info(f"Found {admin_count} users with lowercase 'admin' role, fixing...")
                conn.execute("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'")
            
            # Log the corrected state
            result = conn.execute("SELECT username, role FROM users")
            users = result.fetchall()
            logger.info(f"User roles after fix: {', '.join([f'{u.username}:{u.role}' for u in users])}")
        
        return True
    except Exception as e:
        logger.error(f"Error applying enum fixes: {str(e)}", exc_info=True)
        return False


class SafeEnumAttribute:
    """
    Descriptor class that normalizes enum values to uppercase.
    Use this to wrap the 'role' attribute in your User model.
    """
    def __init__(self, name):
        self.name = name
        self.private_name = f"_{name}"
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name)
    
    def __set__(self, obj, value):
        if value and isinstance(value, str):
            # Convert string values to uppercase
            value = value.upper()
        setattr(obj, self.private_name, value)
