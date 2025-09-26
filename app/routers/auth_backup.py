"""
Authentication Router - API endpoints cho xác thực người dùng
Bao gồm đăng ký, đăng nhập, 2FA và quản lý token
"""

from fastapi import APIRouter, Depends, HTTPException, status
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


@router.post("/register", response_model=Message, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Đăng ký tài khoản mới (Bước 1: Gửi OTP xác thực email)

    Quy trình mới: Người dùng tạo tài khoản ở trạng thái chưa xác thực (is_verified=False).
    Hệ thống tạo OTP 6 số gửi tới email. Người dùng phải gọi /auth/verify-email để kích hoạt.
    """
    # Kiểm tra email / username đã tồn tại
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        # Nếu đã tồn tại nhưng chưa verified cho phép resend OTP qua endpoint khác
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này đã được sử dụng"
        )

    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username này đã được sử dụng"
        )

    hashed_password = get_password_hash(user_data.password)

    # Tạo user chưa xác thực
    otp_code = generate_email_otp()
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        is_active=True,
        is_verified=False,
        email_otp=otp_code,
        email_otp_expiry=datetime.utcnow() + timedelta(minutes=5)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Gửi OTP xác thực (không gửi email welcome trước khi verify)
    await email_service.send_otp_email(new_user.email, otp_code, new_user.username)

    return Message(message="Đăng ký thành công. Mã OTP đã được gửi tới email, vui lòng xác thực trong 5 phút.")


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Đăng nhập với email/password và 2FA (nếu bật)
    
    Args:
        user_credentials: Thông tin đăng nhập
        db: Database session
        
    Returns:
        Token: JWT access token
        
    Raises:
        HTTPException: Nếu thông tin đăng nhập không hợp lệ
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

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email chưa được xác thực. Vui lòng kiểm tra email để xác thực tài khoản."
        )
    
    # Kiểm tra 2FA nếu đã bật
    if user.is_2fa_enabled:
        if not user_credentials.totp_code and not user_credentials.email_otp:
            # Gửi OTP qua email nếu không có TOTP code
            otp = generate_email_otp()
            user.email_otp = otp
            user.email_otp_expiry = datetime.utcnow() + timedelta(minutes=5)
            db.commit()
            
            await email_service.send_otp_email(user.email, otp, user.username)
            
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Mã OTP đã được gửi qua email. Vui lòng nhập mã để hoàn tất đăng nhập."
            )
        
        # Xác thực TOTP code từ authenticator app
        if user_credentials.totp_code:
            if not user.totp_secret or not verify_totp_code(user.totp_secret, user_credentials.totp_code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Mã xác thực không hợp lệ"
                )
        
        # Xác thực email OTP
        elif user_credentials.email_otp:
            if (not user.email_otp or 
                user.email_otp != user_credentials.email_otp or
                is_otp_expired(user.email_otp_expiry)):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Mã OTP không hợp lệ hoặc đã hết hạn"
                )
            
            # Xóa OTP sau khi sử dụng
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
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.post("/enable-2fa", response_model=Dict[str, Any])
async def enable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bật 2FA cho tài khoản
    Tạo TOTP secret và QR code cho Google Authenticator
    
    Args:
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Dict: Secret key và QR code để setup authenticator app
    """
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA đã được bật cho tài khoản này"
        )
    
    # Tạo TOTP secret
    secret = generate_totp_secret()
    qr_code = generate_totp_qr_code(current_user.email, secret)
    
    # Tạo backup codes
    backup_codes = generate_backup_codes()
    
    # Lưu secret (chưa enable 2FA)
    current_user.totp_secret = secret
    current_user.backup_codes = json.dumps(backup_codes)
    db.commit()
    
    return {
        "secret": secret,
        "qr_code": qr_code,
        "backup_codes": backup_codes,
        "message": "Vui lòng quét QR code bằng Google Authenticator và nhập mã 6 số để hoàn tất việc bật 2FA"
    }


@router.post("/verify-2fa", response_model=Message)
async def verify_and_enable_2fa(
    verify_data: Verify2FA,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xác thực và hoàn tất việc bật 2FA
    
    Args:
        verify_data: Mã TOTP để xác thực
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công
    """
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA đã được bật cho tài khoản này"
        )
    
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn cần tạo TOTP secret trước khi xác thực"
        )
    
    # Xác thực TOTP code
    if not verify_totp_code(current_user.totp_secret, verify_data.totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã xác thực không hợp lệ"
        )
    
    # Bật 2FA
    current_user.is_2fa_enabled = True
    db.commit()
    
    return Message(message="2FA đã được bật thành công cho tài khoản của bạn")


@router.post("/disable-2fa", response_model=Message)
async def disable_2fa(
    verify_data: Verify2FA,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tắt 2FA cho tài khoản
    
    Args:
        verify_data: Mã TOTP để xác thực
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công
    """
    if not current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA chưa được bật cho tài khoản này"
        )
    
    # Xác thực TOTP code
    if not verify_totp_code(current_user.totp_secret, verify_data.totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã xác thực không hợp lệ"
        )
    
    # Tắt 2FA và xóa dữ liệu liên quan
    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    current_user.backup_codes = None
    db.commit()
    
    return Message(message="2FA đã được tắt cho tài khoản của bạn")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Lấy thông tin user hiện tại
    
    Args:
        current_user: User hiện tại
        
    Returns:
        UserResponse: Thông tin user
    """
    return current_user


@router.post("/send-otp", response_model=Message)
async def send_email_otp(
    email_request: EmailOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Gửi OTP qua email để đăng nhập (thay thế cho 2FA)
    
    Args:
        email_request: Email request với địa chỉ email
        db: Database session
        
    Returns:
        Message: Thông báo đã gửi OTP
    """
    user = db.query(User).filter(User.email == email_request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài khoản với email này"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa"
        )
    
    # Tạo và gửi OTP với thời hạn 5 phút
    otp = generate_email_otp()
    user.email_otp = otp
    user.email_otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    db.commit()
    
    await email_service.send_otp_email(user.email, otp, user.username)
    
    return Message(message="Mã OTP đã được gửi qua email và có hiệu lực trong 5 phút")


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
    user = db.query(User).filter(User.email == otp_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài khoản với email này"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email chưa được xác thực. Vui lòng xác thực trước khi đăng nhập."
        )
    
    # Xác thực OTP
    if (not user.email_otp or 
        user.email_otp != otp_data.otp_code or
        is_otp_expired(user.email_otp_expiry)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mã OTP không hợp lệ hoặc đã hết hạn"
        )
    
    # Xóa OTP sau khi sử dụng
    user.email_otp = None
    user.email_otp_expiry = None
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
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.post("/verify-email", response_model=Message)
async def verify_email(
    verify_data: EmailOTPVerify,
    db: Session = Depends(get_db)
):
    """Xác thực email bằng OTP (Bước 2 của đăng ký)

    Sau khi đăng ký người dùng cung cấp email + mã OTP để kích hoạt tài khoản.
    """
    user = db.query(User).filter(User.email == verify_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài khoản")

    if user.is_verified:
        return Message(message="Tài khoản đã được xác thực trước đó")

    if (not user.email_otp or user.email_otp != verify_data.otp_code or is_otp_expired(user.email_otp_expiry)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mã OTP không hợp lệ hoặc đã hết hạn")

    # Xác thực thành công
    user.is_verified = True
    user.email_otp = None
    user.email_otp_expiry = None
    db.commit()

    # Gửi email chào mừng sau khi verify
    await email_service.send_welcome_email(user.email, user.username)

    return Message(message="Xác thực email thành công. Bạn có thể đăng nhập.")


@router.post("/resend-registration-otp", response_model=Message)
async def resend_registration_otp(
    email_req: EmailOTPRequest,
    db: Session = Depends(get_db)
):
    """Gửi lại OTP đăng ký nếu user chưa xác thực.
    """
    user = db.query(User).filter(User.email == email_req.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài khoản")

    if user.is_verified:
        return Message(message="Tài khoản đã được xác thực. Không cần gửi lại OTP.")

    # Tạo OTP mới
    otp_code = generate_email_otp()
    user.email_otp = otp_code
    user.email_otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    db.commit()

    await email_service.send_otp_email(user.email, otp_code, user.username)
    return Message(message="Đã gửi lại OTP. Vui lòng kiểm tra email.")