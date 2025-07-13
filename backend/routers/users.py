from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from auth import (
    get_db,
    get_current_active_user,
    create_user,
    get_users,
    get_user,
    update_user_status,
    UserCreate,
    UserUpdate,
    UserResponse
)
from models.users import User, UserRole, UserStatus

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    return create_user(db=db, user=user)

@router.get("/users", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view all users"
        )
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.patch("/users/{username}/status", response_model=UserResponse)
async def update_user_status_endpoint(
    username: str,
    status: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update user status"
        )
    
    try:
        new_status = UserStatus[status.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join([s.value for s in UserStatus])}"
        )
    
    updated_user = update_user_status(db, username, new_status)
    if not updated_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return updated_user
