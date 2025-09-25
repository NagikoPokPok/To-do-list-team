"""
Authentication utilities - Xử lý xác thực và JWT tokens
Bao gồm password hashing, JWT token generation, và 2FA
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp
import qrcode
import io
import base64
from ..config import settings

# Khởi tạo password context cho bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Xác thực password với hash
    
    Args:
        plain_password: Mật khẩu người dùng nhập
        hashed_password: Mật khẩu đã hash trong database
        
    Returns:
        bool: True nếu password đúng
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password sử dụng bcrypt
    
    Args:
        password: Mật khẩu cần hash
        
    Returns:
        str: Mật khẩu đã được hash
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Tạo JWT access token
    
    Args:
        data: Dữ liệu cần encode vào token
        expires_delta: Thời gian hết hạn (optional)
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    
    # Thiết lập thời gian hết hạn
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    # Tạo và trả về JWT token
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Xác thực và decode JWT token
    
    Args:
        token: JWT token cần xác thực
        
    Returns:
        Optional[dict]: Payload của token nếu hợp lệ, None nếu không
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def generate_totp_secret() -> str:
    """
    Tạo TOTP secret key cho Google Authenticator
    
    Returns:
        str: Base32 encoded secret key
    """
    return pyotp.random_base32()


def generate_totp_qr_code(email: str, secret: str) -> str:
    """
    Tạo QR code cho Google Authenticator
    
    Args:
        email: Email của user
        secret: TOTP secret key
        
    Returns:
        str: Base64 encoded QR code image
    """
    # Tạo TOTP URI
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=settings.app_name
    )
    
    # Tạo QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    # Chuyển đổi thành image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 string
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"


def verify_totp_code(secret: str, code: str) -> bool:
    """
    Xác thực TOTP code từ Google Authenticator
    
    Args:
        secret: TOTP secret key
        code: Mã 6 số từ authenticator app
        
    Returns:
        bool: True nếu mã hợp lệ
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def generate_backup_codes(count: int = 10) -> list:
    """
    Tạo backup codes cho 2FA
    
    Args:
        count: Số lượng backup codes cần tạo
        
    Returns:
        list: Danh sách backup codes
    """
    import secrets
    import string
    
    codes = []
    for _ in range(count):
        # Tạo mã 8 ký tự gồm chữ và số
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        codes.append(code)
    
    return codes


def generate_email_otp() -> str:
    """
    Tạo OTP 6 số cho email verification
    
    Returns:
        str: OTP 6 số
    """
    import random
    return str(random.randint(100000, 999999))


def is_otp_expired(otp_expiry: datetime) -> bool:
    """
    Kiểm tra xem OTP có hết hạn không
    
    Args:
        otp_expiry: Thời gian hết hạn của OTP
        
    Returns:
        bool: True nếu OTP đã hết hạn
    """
    return datetime.utcnow() > otp_expiry