"""
Authentication Controller
========================

Controller xử lý các request liên quan đến authentication
Điều phối giữa Router và Service layer
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import random

from ..models.user import User
from ..schemas import (
    UserCreate, UserResponse, UserLogin, Token, Message,
    Enable2FA, Verify2FA, EmailOTPRequest, EmailOTPVerify, UserUpdate, PasswordChange
)
from ..services.auth_service import AuthService
from ..services.email_service import email_service
from ..utils.auth import generate_email_otp, is_otp_expired
from datetime import datetime, timedelta


class AuthController:
    """Controller xử lý authentication logic"""
    
    def __init__(self):
        self.auth_service = AuthService()
        self.email_service = email_service
    
    async def register_user(self, user_data: UserCreate, db: Session) -> Dict[str, str]:
        """
        Đăng ký người dùng mới (Bước 1: Tạo tài khoản và gửi OTP)
        
        Args:
            user_data: Thông tin đăng ký người dùng
            db: Database session
            
        Returns:
            Dict: Thông báo kết quả
            
        Raises:
            HTTPException: Nếu email đã tồn tại
        """
        # Kiểm tra email đã tồn tại và đã được xác thực
        print(f"🔍 Checking email: {user_data.email}")
        verified_user = db.query(User).filter(
            User.email == user_data.email, 
            User.is_verified == True
        ).first()
        if verified_user:
            print(f"❌ Email already verified: {verified_user.email} (ID: {verified_user.id})")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email đã được sử dụng"
            )
        
        # Xóa user chưa xác thực cũ nếu có (để cho phép đăng ký lại)
        unverified_user = db.query(User).filter(
            User.email == user_data.email,
            User.is_verified == False
        ).first()
        if unverified_user:
            print(f"🗑️ Removing old unverified user: {unverified_user.email}")
            db.delete(unverified_user)
            db.commit()
        
        print(f"✅ Email available: {user_data.email}")
        
        # Hash password
        hashed_password = self.auth_service.get_password_hash(user_data.password)
        
        # Tạo OTP cho email verification
        otp_code = generate_email_otp()
        
        # Tạo user mới (chưa xác thực) - CHỈ sau khi xác thực OTP mới set is_verified=True
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            is_active=True,
            is_verified=False,  # Chưa xác thực - quan trọng!
            email_otp=otp_code,
            email_otp_expiry=datetime.utcnow() + timedelta(minutes=5)
        )
        
        # Lưu vào database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Gửi OTP qua email
        await self.email_service.send_otp_email(
            new_user.email, 
            otp_code, 
            new_user.full_name or new_user.email.split('@')[0]
        )
        
        return {
            "message": "Đăng ký thành công. Mã OTP đã được gửi tới email, vui lòng xác thực trong 5 phút."
        }
    
    async def verify_email(self, verify_data: EmailOTPVerify, db: Session) -> Dict[str, str]:
        """
        Xác thực email bằng OTP (Bước 2 của đăng ký)
        
        Args:
            verify_data: Email và OTP code
            db: Database session
            
        Returns:
            Dict: Thông báo kết quả
            
        Raises:
            HTTPException: Nếu OTP không hợp lệ hoặc đã hết hạn
        """
        # Tìm user theo email
        user = db.query(User).filter(User.email == verify_data.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản"
            )
        
        # Kiểm tra đã xác thực chưa
        if user.is_verified:
            return {"message": "Tài khoản đã được xác thực trước đó"}
        
        # Xác thực OTP
        if (not user.email_otp or 
            user.email_otp != verify_data.otp_code or 
            is_otp_expired(user.email_otp_expiry)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã OTP không hợp lệ hoặc đã hết hạn"
            )
        
        # Kích hoạt tài khoản
        user.is_verified = True
        user.email_otp = None
        user.email_otp_expiry = None
        db.commit()
        
        # Gửi email chào mừng
        await self.email_service.send_welcome_email(user.email, user.full_name or user.email.split('@')[0])
        
        return {"message": "Xác thực email thành công. Bạn có thể đăng nhập."}
    
    async def resend_registration_otp(self, email_req: EmailOTPRequest, db: Session) -> Dict[str, str]:
        """
        Gửi lại OTP đăng ký
        
        Args:
            email_req: Email request
            db: Database session
            
        Returns:
            Dict: Thông báo kết quả
            
        Raises:
            HTTPException: Nếu không tìm thấy tài khoản hoặc đã xác thực
        """
        # Tìm user
        user = db.query(User).filter(User.email == email_req.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản"
            )
        
        # Kiểm tra đã xác thực chưa
        if user.is_verified:
            return {"message": "Tài khoản đã được xác thực. Không cần gửi lại OTP."}
        
        # Tạo OTP mới
        otp_code = generate_email_otp()
        user.email_otp = otp_code
        user.email_otp_expiry = datetime.utcnow() + timedelta(minutes=5)
        db.commit()
        
        # Gửi OTP
        await self.email_service.send_otp_email(user.email, otp_code, user.full_name or user.email.split('@')[0])
        
        return {"message": "Đã gửi lại OTP. Vui lòng kiểm tra email."}
    
    async def login_user(self, user_credentials: UserLogin, db: Session) -> Dict[str, Any]:
        """
        Đăng nhập người dùng
        
        Args:
            user_credentials: Thông tin đăng nhập
            db: Database session
            
        Returns:
            Dict: Token thông tin
            
        Raises:
            HTTPException: Nếu thông tin đăng nhập không hợp lệ
        """
        # Tìm user theo email
        user = db.query(User).filter(User.email == user_credentials.email).first()
        
        if not user or not self.auth_service.verify_password(
            user_credentials.password, 
            user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không chính xác"
            )
        
        # Kiểm tra tài khoản active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đã bị vô hiệu hóa"
            )
        
        # Kiểm tra đã xác thực email
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản chưa được xác thực. Vui lòng kiểm tra email và xác thực tài khoản trước khi đăng nhập."
            )
        
        # Kiểm tra 2FA nếu đã bật
        if user.is_2fa_enabled:
            if not user_credentials.totp_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Yêu cầu mã 2FA"
                )
            
            if not self.auth_service.verify_totp(user.totp_secret, user_credentials.totp_code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Mã 2FA không chính xác"
                )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Tạo access token
        access_token_expires = timedelta(minutes=30)  # 30 phút
        access_token = self.auth_service.create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 30 * 60  # 30 phút tính bằng giây
        }
    
    async def send_login_otp(self, email_req: EmailOTPRequest, db: Session) -> Dict[str, str]:
        """
        Gửi OTP để đăng nhập (thay thế 2FA)
        
        Args:
            email_req: Email request
            db: Database session
            
        Returns:
            Dict: Thông báo kết quả
        """
        user = db.query(User).filter(User.email == email_req.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đã bị vô hiệu hóa"
            )
        
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vui lòng xác thực email trước"
            )
        
        # Tạo và gửi OTP
        otp = generate_email_otp()
        user.email_otp = otp
        user.email_otp_expiry = datetime.utcnow() + timedelta(minutes=5)
        db.commit()
        
        await self.email_service.send_otp_email(user.email, otp, user.full_name or user.email.split('@')[0])
        
        return {"message": "Mã OTP đã được gửi qua email và có hiệu lực trong 5 phút"}
    
    async def login_with_otp(self, otp_data: EmailOTPVerify, db: Session) -> Dict[str, Any]:
        """
        Đăng nhập bằng OTP email
        
        Args:
            otp_data: Email và OTP code
            db: Database session
            
        Returns:
            Dict: Token thông tin
        """
        user = db.query(User).filter(User.email == otp_data.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đã bị vô hiệu hóa"
            )
        
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vui lòng xác thực email trước"
            )
        
        # Xác thực OTP
        if (not user.email_otp or 
            user.email_otp != otp_data.otp_code or
            is_otp_expired(user.email_otp_expiry)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mã OTP không hợp lệ hoặc đã hết hạn"
            )
        
        # Xóa OTP sau khi sử dụng và update last login
        user.email_otp = None
        user.email_otp_expiry = None
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Tạo access token
        access_token_expires = timedelta(minutes=30)
        access_token = self.auth_service.create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 30 * 60
        }
    
    async def enable_2fa(self, current_user: User, db: Session) -> Dict[str, Any]:
        """
        Bật 2FA cho tài khoản
        
        Args:
            current_user: User hiện tại
            db: Database session
            
        Returns:
            Dict: Secret key và QR code
        """
        if current_user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA đã được bật cho tài khoản này"
            )
        
        # Tạo TOTP secret và QR code
        secret = self.auth_service.generate_totp_secret()
        qr_code = self.auth_service.generate_totp_qr_code(current_user.email, secret)
        
        # Tạo backup codes
        backup_codes = self.auth_service.generate_backup_codes()
        hashed_backup_codes = self.auth_service.hash_backup_codes(backup_codes)
        
        # Lưu secret (chưa enable 2FA)
        current_user.totp_secret = secret
        current_user.backup_codes = ','.join(hashed_backup_codes)
        db.commit()
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes,
            "message": "Vui lòng quét QR code bằng Google Authenticator và nhập mã 6 số để hoàn tất việc bật 2FA"
        }
    
    async def verify_and_enable_2fa(self, verify_data: Verify2FA, current_user: User, db: Session) -> Dict[str, str]:
        """
        Xác thực và hoàn tất việc bật 2FA
        
        Args:
            verify_data: Mã TOTP để xác thực
            current_user: User hiện tại
            db: Database session
            
        Returns:
            Dict: Thông báo thành công
        """
        if current_user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA đã được bật cho tài khoản này"
            )
        
        if not current_user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vui lòng enable 2FA trước khi xác thực"
            )
        
        # Xác thực TOTP code
        if not self.auth_service.verify_totp(current_user.totp_secret, verify_data.totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã 2FA không chính xác"
            )
        
        # Bật 2FA
        current_user.is_2fa_enabled = True
        db.commit()
        
        return {"message": "2FA đã được bật thành công cho tài khoản của bạn"}
    
    async def disable_2fa(self, verify_data: Verify2FA, current_user: User, db: Session) -> Dict[str, str]:
        """
        Tắt 2FA cho tài khoản
        
        Args:
            verify_data: Mã TOTP để xác thực
            current_user: User hiện tại
            db: Database session
            
        Returns:
            Dict: Thông báo thành công
        """
        if not current_user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA chưa được bật cho tài khoản này"
            )
        
        # Xác thực TOTP code
        if not self.auth_service.verify_totp(current_user.totp_secret, verify_data.totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã 2FA không chính xác"
            )
        
        # Tắt 2FA và xóa dữ liệu liên quan
        current_user.is_2fa_enabled = False
        current_user.totp_secret = None
        current_user.backup_codes = None
        db.commit()
        
        return {"message": "2FA đã được tắt cho tài khoản của bạn"}
    
    def get_user_profile(self, current_user: User) -> UserResponse:
        """
        Lấy thông tin profile user hiện tại
        
        Args:
            current_user: User hiện tại
            
        Returns:
            UserResponse: Thông tin user
        """
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            phone_number=current_user.phone_number,
            avatar_url=current_user.avatar_url,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            is_2fa_enabled=current_user.is_2fa_enabled,
            created_at=current_user.created_at,
            last_login=current_user.last_login
        )
    
    def update_user_profile(self, current_user: User, update_data: UserUpdate, db: Session) -> UserResponse:
        """
        Cập nhật thông tin profile user hiện tại
        
        Args:
            current_user: User hiện tại
            update_data: Dữ liệu cập nhật
            db: Database session
            
        Returns:
            UserResponse: Thông tin user đã cập nhật
        """
        # Cập nhật các trường được phép
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        # Cập nhật thời gian
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(current_user)
        
        return self.get_user_profile(current_user)
    
    async def change_password(self, password_data: PasswordChange, current_user: User, db: Session) -> Dict[str, str]:
        """
        Đổi mật khẩu của user hiện tại
        
        Args:
            password_data: Dữ liệu đổi mật khẩu (current_password, new_password)
            current_user: User hiện tại
            db: Database session
            
        Returns:
            Dict: Thông báo kết quả
            
        Raises:
            HTTPException: Nếu mật khẩu hiện tại không đúng
        """
        # Kiểm tra mật khẩu hiện tại
        if not self.auth_service.verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu hiện tại không chính xác"
            )
        
        # Kiểm tra mật khẩu mới không giống mật khẩu cũ
        if self.auth_service.verify_password(password_data.new_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu mới không được giống mật khẩu hiện tại"
            )
        
        # Hash mật khẩu mới
        hashed_new_password = self.auth_service.get_password_hash(password_data.new_password)
        
        # Cập nhật mật khẩu
        current_user.hashed_password = hashed_new_password
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Đổi mật khẩu thành công"}