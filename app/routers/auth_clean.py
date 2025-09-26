"""
Clean Authentication Router
=========================

Router cho auth endpoints sạch sẽ và đơn giản
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database.database import get_db
from app.schemas import (
    UserCreate, UserLogin, UserResponse, Token, OTPVerify, 
    OTPRequest, PasswordReset, PasswordResetConfirm
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Import auth service và các dependencies
try:
    from app.services.auth_service_clean import AuthService
    from app.middleware.auth import get_current_user
    from models import User
except ImportError as e:
    logger.warning(f"Import warning: {e}")
    # Fallback imports
    pass

@router.post("/register", response_model=dict)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Đăng ký tài khoản mới
    
    Bước 1: Tạo tài khoản và gửi OTP qua email
    User cần gọi /verify-otp để kích hoạt tài khoản
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.register_user(user_data)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Đăng ký thất bại: {str(e)}"
        )

@router.post("/verify-otp", response_model=dict)
async def verify_otp(
    otp_data: OTPVerify,
    db: AsyncSession = Depends(get_db)
):
    """
    Xác thực OTP để kích hoạt tài khoản
    
    Bước 2: Nhập OTP từ email để hoàn tất đăng ký
    """
    auth_service = AuthService(db)
    return await auth_service.verify_otp(otp_data.email, otp_data.otp_code)

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Đăng nhập với email và mật khẩu
    
    Yêu cầu tài khoản đã được xác thực qua OTP
    """
    auth_service = AuthService(db)
    return await auth_service.login_user(login_data)

@router.post("/resend-otp", response_model=dict)
async def resend_otp(
    otp_request: OTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Gửi lại OTP xác thực đăng ký
    
    Dành cho trường hợp user chưa nhận được hoặc OTP đã hết hạn
    """
    auth_service = AuthService(db)
    return await auth_service.resend_otp(otp_request.email)

@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    password_reset: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """
    Yêu cầu reset mật khẩu
    
    Gửi OTP qua email để reset mật khẩu
    """
    auth_service = AuthService(db)
    return await auth_service.forgot_password(password_reset.email)

@router.post("/reset-password", response_model=dict)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset mật khẩu với OTP
    
    Xác nhận reset mật khẩu bằng OTP từ email
    """
    auth_service = AuthService(db)
    return await auth_service.reset_password(
        reset_data.email, 
        reset_data.otp_code, 
        reset_data.new_password
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Lấy thông tin người dùng hiện tại
    """
    return current_user

@router.post("/logout", response_model=dict)
async def logout():
    """
    Đăng xuất
    
    Client nên xóa token từ storage
    """
    return {"message": "Đăng xuất thành công"}

@router.get("/health", response_model=dict)
async def health_check():
    """
    Kiểm tra trạng thái service authentication
    """
    return {
        "status": "healthy",
        "service": "clean_authentication",
        "features": [
            "email_registration_with_otp",
            "password_login",
            "password_reset_with_otp",
            "jwt_tokens"
        ]
    }