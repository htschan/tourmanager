from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth import get_db, pwd_context, get_user_by_email, UserResponse
from utils.email import (
    create_verification_token,
    create_password_reset_token,
    verify_token,
    send_verification_email,
    send_password_reset_email
)
from models.users import UserStatus
from pydantic import BaseModel, EmailStr

router = APIRouter()

class EmailRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

@router.post("/request-verification")
async def request_verification(
    email_req: EmailRequest,
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, email_req.email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    if user.email_verified:
        raise HTTPException(
            status_code=400,
            detail="Email already verified"
        )

    token = create_verification_token(user.email)
    user.verification_token = token
    db.commit()

    await send_verification_email(user.email, token)
    return {"message": "Verification email sent"}

@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    email = verify_token(token)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )

    user = get_user_by_email(db, email)
    if not user or user.verification_token != token:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification token"
        )

    user.email_verified = True
    user.verification_token = None
    db.commit()

    return {"message": "Email verified successfully"}

@router.post("/request-password-reset")
async def request_password_reset(
    email_req: EmailRequest,
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, email_req.email)
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link will be sent"}

    token = create_password_reset_token(user.email)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    await send_password_reset_email(user.email, token)
    return {"message": "If the email exists, a reset link will be sent"}

@router.post("/reset-password")
async def reset_password(
    reset_req: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    email = verify_token(reset_req.token)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )

    user = get_user_by_email(db, email)
    if not user or user.reset_token != reset_req.token:
        raise HTTPException(
            status_code=400,
            detail="Invalid reset token"
        )

    if user.reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Reset token has expired"
        )

    user.hashed_password = pwd_context.hash(reset_req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password reset successfully"}
