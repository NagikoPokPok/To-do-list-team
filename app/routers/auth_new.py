"""
Authentication Router - API endpoints cho xác thực người dùng
Bao gồm đăng ký, đăng nhập, 2FA và quản lý token
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..models.user import User
from ..schemas import (
    UserCreate, UserResponse, UserLogin, Token, Message,
    Enable2FA, Verify2FA, EmailOTPRequest, EmailOTPVerify
)
from ..controllers.auth_controller import AuthController
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Khởi tạo controller
auth_controller = AuthController()


@router.post("/register", response_model=Message, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Đăng ký tài khoản mới (Bước 1: Gửi OTP xác thực email)
    
    Quy trình:
    1. User nhập thông tin đăng ký
    2. Hệ thống tạo tài khoản với trạng thái chưa xác thực
    3. Gửi OTP 6 số qua email
    4. User phải gọi /verify-email để kích hoạt tài khoản
    """
    result = await auth_controller.register_user(user_data, db)
    return Message(message=result["message"])


@router.post("/verify-email", response_model=Message)
async def verify_email(
    verify_data: EmailOTPVerify,
    db: Session = Depends(get_db)
):
    """
    Xác thực email bằng OTP (Bước 2 của đăng ký)
    
    Sau khi đăng ký, người dùng nhập email + OTP để kích hoạt tài khoản
    """
    result = await auth_controller.verify_email(verify_data, db)
    return Message(message=result["message"])


@router.post("/resend-registration-otp", response_model=Message)
async def resend_registration_otp(
    email_req: EmailOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Gửi lại OTP đăng ký nếu user chưa xác thực
    """
    result = await auth_controller.resend_registration_otp(email_req, db)
    return Message(message=result["message"])


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Đăng nhập với email/password và 2FA (nếu bật)
    
    Args:
        user_credentials: Thông tin đăng nhập (email, password, totp_code optional)
        db: Database session
        
    Returns:
        Token: JWT access token với thời gian hết hạn
        
    Raises:
        HTTPException: Nếu thông tin đăng nhập không hợp lệ
    """
    result = await auth_controller.login_user(user_credentials, db)
    return Token(
        access_token=result["access_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"]
    )


@router.post("/send-otp", response_model=Message)
async def send_email_otp(
    email_request: EmailOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Gửi OTP qua email để đăng nhập (thay thế cho 2FA)
    
    Dành cho users không muốn sử dụng Google Authenticator
    """
    result = await auth_controller.send_login_otp(email_request, db)
    return Message(message=result["message"])


@router.post("/login-otp", response_model=Token)
async def login_with_otp(
    otp_data: EmailOTPVerify,
    db: Session = Depends(get_db)
):
    """
    Đăng nhập bằng OTP email (không cần mật khẩu)
    
    Args:
        otp_data: Email và OTP code
        db: Database session
        
    Returns:
        Token: JWT access token
    """
    result = await auth_controller.login_with_otp(otp_data, db)
    return Token(
        access_token=result["access_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"]
    )


@router.post("/enable-2fa", response_model=Dict[str, Any])
async def enable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bật 2FA cho tài khoản
    
    Tạo TOTP secret và QR code cho Google Authenticator.
    Trả về secret key, QR code URI và backup codes.
    User cần gọi /verify-2fa để hoàn tất việc bật 2FA.
    
    Args:
        current_user: User hiện tại từ JWT token
        db: Database session
        
    Returns:
        Dict: Secret key, QR code URI và backup codes
    """
    return await auth_controller.enable_2fa(current_user, db)


@router.post("/verify-2fa", response_model=Message)
async def verify_and_enable_2fa(
    verify_data: Verify2FA,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xác thực và hoàn tất việc bật 2FA
    
    User nhập mã 6 số từ Google Authenticator để xác nhận việc setup 2FA
    
    Args:
        verify_data: Mã TOTP 6 số
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công
    """
    result = await auth_controller.verify_and_enable_2fa(verify_data, current_user, db)
    return Message(message=result["message"])


@router.post("/disable-2fa", response_model=Message)
async def disable_2fa(
    verify_data: Verify2FA,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tắt 2FA cho tài khoản
    
    User phải nhập mã TOTP để xác nhận việc tắt 2FA
    
    Args:
        verify_data: Mã TOTP để xác thực
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công
    """
    result = await auth_controller.disable_2fa(verify_data, current_user, db)
    return Message(message=result["message"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Lấy thông tin profile user hiện tại
    
    Args:
        current_user: User hiện tại từ JWT token
        
    Returns:
        UserResponse: Thông tin chi tiết user
    """
    return auth_controller.get_user_profile(current_user)


@router.get("/health")
async def auth_health_check():
    """
    Health check cho authentication service
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "features": [
            "user_registration",
            "email_verification",
            "password_login", 
            "otp_login",
            "2fa_totp",
            "jwt_tokens"
        ]
    }