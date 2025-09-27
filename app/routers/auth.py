"""
Authentication Router - API endpoints cho xác thực người dùng
Bao gồm đăng ký, đăng nhập, 2FA và quản lý token
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
from typing import Dict, Any

from ..database import get_db
from ..models.user import User
from ..schemas import (
    UserCreate, UserResponse, UserLogin, Token, Message,
    Enable2FA, Verify2FA
)
from ..utils.auth import (
    verify_password, get_password_hash, create_access_token,
    generate_totp_secret, generate_totp_qr_code, verify_totp_code,
    generate_backup_codes, generate_email_otp, is_otp_expired
)
from ..services.email_service import email_service
from ..middleware.auth import get_current_user
from ..config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ------------------ REGISTER ------------------
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Kiểm tra email đã tồn tại
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này đã được sử dụng"
        )

    # Kiểm tra username đã tồn tại
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username này đã được sử dụng"
        )

    # Tạo user mới
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        role=user_data.role.value,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Gửi email chào mừng
    await email_service.send_welcome_email(new_user.email, new_user.username)

    return new_user


# ------------------ LOGIN ------------------
@router.post("/login")
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Đăng nhập với email/password và 2FA (nếu bật)
    """

    # Tìm user theo email
    user = db.query(User).filter(User.email == user_credentials.email).first()

    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa"
        )

    # Nếu user đã bật 2FA
    if user.is_2fa_enabled:
        # Nếu chưa nhập mã 2FA → gửi OTP và báo frontend
        if not user_credentials.totp_code and not user_credentials.email_otp:
            otp = generate_email_otp()
            user.email_otp = otp
            user.email_otp_expiry = datetime.utcnow() + timedelta(minutes=5)
            db.commit()

            await email_service.send_otp_email(user.email, otp, user.username)

            return {
                "access_token": None,
                "token_type": None,
                "expires_in": 0,
                "requires_2fa": True,
                "message": "OTP_SENT"
            }

        # Xác thực bằng TOTP app
        if user_credentials.totp_code:
            if not user.totp_secret or not verify_totp_code(user.totp_secret, user_credentials.totp_code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Mã xác thực không hợp lệ"
                )

        # Xác thực bằng OTP email
        elif user_credentials.email_otp:
            if (not user.email_otp or
                user.email_otp != user_credentials.email_otp or
                is_otp_expired(user.email_otp_expiry)):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Mã OTP không hợp lệ hoặc đã hết hạn"
                )

            # Xóa OTP sau khi dùng
            user.email_otp = None
            user.email_otp_expiry = None
            db.commit()

    # Cập nhật last_login
    user.last_login = datetime.utcnow()
    db.commit()

    # Tạo access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "requires_2fa": False,
        "message": "LOGIN_SUCCESS"
    }
