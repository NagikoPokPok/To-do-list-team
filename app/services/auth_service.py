"""
Authentication Service
======================

Service xử lý các chức năng xác thực và phân quyền người dùng
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Union

import bcrypt
import pyotp
from passlib.context import CryptContext
from jose import JWTError, jwt

from ..config import settings


class AuthService:
    """Service xử lý authentication và authorization"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    def get_password_hash(self, password: str) -> str:
        """Hash mật khẩu sử dụng bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Xác minh mật khẩu"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Tạo JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Xác minh JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def generate_totp_secret(self) -> str:
        """Tạo TOTP secret cho 2FA"""
        return pyotp.random_base32()
    
    def generate_totp_uri(self, secret: str, email: str, issuer: str = None) -> str:
        """Tạo TOTP URI cho QR code"""
        if not issuer:
            issuer = settings.app_name
        
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=issuer
        )
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Xác minh TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # Allow 1 window tolerance
        except Exception:
            return False
    
    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """Tạo backup codes cho 2FA"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()  # 8 character hex codes
            codes.append(f"{code[:4]}-{code[4:]}")  # Format: XXXX-XXXX
        return codes
    
    def hash_backup_codes(self, codes: list[str]) -> list[str]:
        """Hash backup codes để lưu trong database"""
        return [self.get_password_hash(code) for code in codes]
    
    def verify_backup_code(self, code: str, hashed_codes: list[str]) -> bool:
        """Xác minh backup code"""
        for hashed_code in hashed_codes:
            if self.verify_password(code, hashed_code):
                return True
        return False
    
    def generate_email_otp(self, length: int = 6) -> str:
        """Tạo OTP gửi qua email"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    def generate_invitation_token(self, team_id: int, email: str) -> str:
        """Tạo token để mời vào team"""
        data = {
            "team_id": team_id,
            "email": email,
            "type": "invitation",
            "exp": datetime.utcnow() + timedelta(days=7)  # Token expires in 7 days
        }
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)
    
    def verify_invitation_token(self, token: str) -> Optional[dict]:
        """Xác minh invitation token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") == "invitation":
                return payload
            return None
        except JWTError:
            return None
    
    def generate_password_reset_token(self, email: str) -> str:
        """Tạo token để reset mật khẩu"""
        data = {
            "email": email,
            "type": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        }
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Xác minh password reset token và trả về email"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") == "password_reset":
                return payload.get("email")
            return None
        except JWTError:
            return None