"""
Authentication Router (Consolidated)
===================================

Gộp logic từ router cũ, chuẩn hóa prefix /api/v1/auth và đặt tên endpoint
phù hợp với frontend hiện tại (register, verify-otp, resend-otp, login, me, ...)
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..models.user import User
from ..schemas import (
    UserCreate, UserResponse, UserLogin, Token, Message,
    Enable2FA, Verify2FA, EmailOTPRequest, EmailOTPVerify, OTPVerify, OTPRequest,
    PasswordReset, PasswordResetConfirm
)
from ..controllers.auth_controller import AuthController
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

auth_controller = AuthController()


# ---- Registration & Email Verification ----
@router.post("/register", response_model=Message, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    result = await auth_controller.register_user(user_data, db)
    return Message(message=result["message"])


@router.post("/verify-email", response_model=Message)
async def verify_email(verify_data: EmailOTPVerify, db: Session = Depends(get_db)):
    result = await auth_controller.verify_email(verify_data, db)
    return Message(message=result["message"])


# Alias cho frontend đang gọi /verify-otp
@router.post("/verify-otp", response_model=Message)
async def verify_email_alias(otp_data: OTPVerify, db: Session = Depends(get_db)):
    verify_payload = EmailOTPVerify(email=otp_data.email, otp_code=otp_data.otp_code)
    result = await auth_controller.verify_email(verify_payload, db)
    return Message(message=result["message"])


@router.post("/resend-registration-otp", response_model=Message)
async def resend_registration_otp(email_req: EmailOTPRequest, db: Session = Depends(get_db)):
    result = await auth_controller.resend_registration_otp(email_req, db)
    return Message(message=result["message"])


# Alias cho /resend-otp nếu FE dùng
@router.post("/resend-otp", response_model=Message)
async def resend_registration_otp_alias(otp_req: OTPRequest, db: Session = Depends(get_db)):
    email_req = EmailOTPRequest(email=otp_req.email)
    result = await auth_controller.resend_registration_otp(email_req, db)
    return Message(message=result["message"])


# ---- Login flows ----
@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    result = await auth_controller.login_user(user_credentials, db)
    return Token(
        access_token=result["access_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"]
    )


# Optional: OTP login (giữ lại nếu cần về sau)
@router.post("/login-otp", response_model=Token)
async def login_with_otp(otp_data: EmailOTPVerify, db: Session = Depends(get_db)):
    result = await auth_controller.login_with_otp(otp_data, db)
    return Token(
        access_token=result["access_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"]
    )


# ---- 2FA ----
@router.post("/enable-2fa", response_model=Dict[str, Any])
async def enable_2fa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return await auth_controller.enable_2fa(current_user, db)


@router.post("/verify-2fa", response_model=Message)
async def verify_and_enable_2fa(verify_data: Verify2FA, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = await auth_controller.verify_and_enable_2fa(verify_data, current_user, db)
    return Message(message=result["message"])


@router.post("/disable-2fa", response_model=Message)
async def disable_2fa(verify_data: Verify2FA, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = await auth_controller.disable_2fa(verify_data, current_user, db)
    return Message(message=result["message"])


# ---- Profile ----
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return auth_controller.get_user_profile(current_user)


# ---- Health / Misc ----
@router.get("/health")
async def auth_health_check():
    return {
        "status": "healthy",
        "service": "authentication",
        "prefix": "/api/v1/auth",
        "features": [
            "user_registration",
            "email_verification",
            "password_login",
            "otp_login",
            "2fa_totp",
            "jwt_tokens"
        ]
    }
