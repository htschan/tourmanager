from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from auth import (
    get_db,
    get_current_active_user,
    get_user,
    get_password_hash,
)
from models.users import User, UserRole, UserStatus
from schemas.users import UserCreate, UserResponse, UserUpdate

router = APIRouter()

def create_user(db: Session, user: UserCreate):
    import secrets
    from utils.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info(f"Creating new user: {user.username}, {user.email}")
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=UserRole.USER,
        status=UserStatus.PENDING,  # User starts as pending until admin approves
        email_verified=False,
        verification_token=verification_token
    )
    
    logger.info(f"New user {user.username} created with PENDING status")
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def update_user_status(db: Session, username: str, status: UserStatus):
    user = get_user(db, username)
    if user:
        user.status = status
        db.commit()
        db.refresh(user)
    return user

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    from utils.email import send_verification_email
    from utils.logger import get_logger
    
    logger = get_logger(__name__)
    
    # Check if username is already taken
    db_user = get_user(db, username=user.username)
    if db_user:
        logger.warning(f"Registration attempt with existing username: {user.username}")
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email is already used
    from auth import get_user_by_email
    existing_email = get_user_by_email(db, user.email)
    if existing_email:
        logger.warning(f"Registration attempt with existing email: {user.email}")
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create user with pending status
    db_user = create_user(db=db, user=user)
    logger.info(f"User registered: {user.username}, awaiting email verification and admin approval")
    
    # Send verification email
    try:
        logger.info(f"Initiating verification email for new user: {user.username} ({db_user.email})")
        email_result = await send_verification_email(db_user.email, db_user.verification_token)
        
        # Log the detailed result from the email function
        if email_result and email_result.get("success"):
            logger.info(f"Verification email successfully sent to {db_user.email}")
            logger.info(f"Email details: took {email_result.get('duration_seconds', 'unknown')} seconds")
        else:
            logger.warning(f"Verification email not sent successfully to {db_user.email}")
            if email_result:
                logger.warning(f"Email error: {email_result.get('error', 'unknown error')}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {db_user.email}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        # We don't want to fail registration if email sending fails
        # The admin can still manually verify users
    
    return db_user

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

@router.delete("/users/{username}")
async def delete_user(
    username: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user. Admin users cannot delete themselves.
    """
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete users"
        )
    
    # Prevent admin from deleting themselves
    if current_user.username == username:
        raise HTTPException(
            status_code=400,
            detail="Admin users cannot delete their own account"
        )
    
    # Get the user to delete
    user_to_delete = get_user(db, username=username)
    if not user_to_delete:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Delete the user
    try:
        db.delete(user_to_delete)
        db.commit()
        return {"message": f"User {username} has been deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete user: {str(e)}"
        )

@router.get("/verify-email/{token}", response_model=UserResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    from utils.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info(f"Processing email verification with token")
    
    # Find user with this verification token
    user = db.query(User).filter(User.verification_token == token).first()
    
    if not user:
        logger.warning(f"Invalid verification token used")
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )
    
    # Update user's email verification status
    user.email_verified = True
    user.verification_token = None  # Clear the token after use
    
    # User is now verified but still needs admin approval
    logger.info(f"Email verified for user {user.username}, awaiting admin approval")
    
    db.commit()
    db.refresh(user)
    
    return user

@router.get("/admin/pending-users", response_model=List[UserResponse])
async def list_pending_users(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    from utils.logger import get_logger
    
    logger = get_logger(__name__)
    
    # Check if the current user is an admin
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted to access pending users")
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view pending users"
        )
    
    # Query pending users
    pending_users = db.query(User).filter(User.status == UserStatus.PENDING).all()
    logger.info(f"Admin {current_user.username} viewed list of {len(pending_users)} pending users")
    
    return pending_users

@router.post("/admin/approve-user/{username}", response_model=UserResponse)
async def approve_user(
    username: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    from utils.logger import get_logger
    
    logger = get_logger(__name__)
    
    # Check if the current user is an admin
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted to approve user {username}")
        raise HTTPException(
            status_code=403,
            detail="Not authorized to approve users"
        )
    
    # Find the pending user
    user = get_user(db, username)
    if not user:
        logger.warning(f"Attempted to approve non-existent user: {username}")
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Check if the user is pending
    if user.status != UserStatus.PENDING:
        logger.warning(f"Attempted to approve user {username} with status {user.status}")
        raise HTTPException(
            status_code=400,
            detail=f"User is not pending approval (current status: {user.status.value})"
        )
    
    # Check if email is verified
    if not user.email_verified:
        logger.warning(f"Attempted to approve user {username} with unverified email")
        raise HTTPException(
            status_code=400,
            detail="User's email is not verified yet"
        )
    
    # Update user status to ACTIVE
    user.status = UserStatus.ACTIVE
    db.commit()
    db.refresh(user)
    
    logger.info(f"Admin {current_user.username} approved user {username}")
    
    # Notify the user that their account was approved
    try:
        from utils.email import send_account_approved_email
        await send_account_approved_email(user.email)
        logger.info(f"Account approval notification sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send approval notification to {user.email}: {str(e)}")
    
    return user
