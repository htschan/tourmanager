from fastapi.responses import JSONResponse
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

def bypass_users(current_user, db, UserModel, UserRole):
    """Completely bypassed users endpoint"""
    if not hasattr(current_user, "role") or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to view user list")

    users = db.query(UserModel).all()

    result = []
    for user in users:
        user_dict = {}
        # Basic fields
        for field in ["username", "email"]:
            if hasattr(user, field):
                user_dict[field] = getattr(user, field) or ""
            else:
                user_dict[field] = ""

        # Handle role
        if hasattr(user, "role"):
            if hasattr(user.role, "name"):
                user_dict["role"] = user.role.name
            else:
                role_str = str(user.role)
                if "ADMIN" in role_str.upper():
                    user_dict["role"] = "ADMIN"
                else:
                    user_dict["role"] = "USER"
        else:
            user_dict["role"] = "USER"

        # Handle status
        if hasattr(user, "status"):
            if hasattr(user.status, "name"):
                user_dict["status"] = user.status.name
            else:
                status_str = str(user.status)
                if "PENDING" in status_str.upper():
                    user_dict["status"] = "PENDING"
                elif "DISABLED" in status_str.upper():
                    user_dict["status"] = "DISABLED"
                else:
                    user_dict["status"] = "ACTIVE"
        else:
            user_dict["status"] = "ACTIVE"

        # Handle dates
        for date_field in ["created_at", "last_login"]:
            user_dict[date_field] = None
            if hasattr(user, date_field) and getattr(user, date_field):
                try:
                    user_dict[date_field] = getattr(user, date_field).isoformat()
                except:
                    user_dict[date_field] = str(getattr(user, date_field))
                    
        # Handle email verification status
        if hasattr(user, "email_verified"):
            user_dict["email_verified"] = bool(user.email_verified)
        else:
            user_dict["email_verified"] = False

        result.append(user_dict)

    return JSONResponse(content=result)
