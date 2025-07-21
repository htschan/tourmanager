"""
Database fixes and utilities for handling enum value inconsistencies.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from models.users import UserRole, User as UserModel
import logging

logger = logging.getLogger(__name__)

def fix_user_role_case_sensitivity(db: Session):
    """
    Fix case sensitivity issues with UserRole enum values in the database.
    
    This function:
    1. Logs current user roles to identify inconsistencies
    2. Updates any lowercase 'user' values to 'USER' 
    3. Updates any lowercase 'admin' values to 'ADMIN'
    
    Args:
        db (Session): SQLAlchemy database session
    
    Returns:
        int: Number of records updated
    """
    try:
        # First, log all existing roles for debugging
        users = db.query(UserModel).all()
        logger.info(f"Current users in database: {len(users)}")
        
        for user in users:
            logger.info(f"User {user.username}: role={user.role} (type: {type(user.role)})")
        
        # Count values before update
        raw_data = db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'user'")).scalar()
        logger.info(f"Found {raw_data} users with lowercase 'user' role")
        
        raw_data = db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin'")).scalar()
        logger.info(f"Found {raw_data} users with lowercase 'admin' role")
        
        # Update lowercase values to uppercase
        result1 = db.execute(text("UPDATE users SET role = 'USER' WHERE role = 'user'"))
        result2 = db.execute(text("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'"))
        
        db.commit()
        
        total_updated = result1.rowcount + result2.rowcount
        logger.info(f"Updated {total_updated} user records to fix role case sensitivity")
        
        return total_updated
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error fixing user roles: {str(e)}", exc_info=True)
        raise
