"""
Model OTPCode - Quản lý mã OTP cho xác thực email
Hỗ trợ OTP cho đăng ký và reset password
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class OTPCode(Base):
    """
    Model OTPCode định nghĩa cấu trúc bảng mã OTP
    Hỗ trợ xác thực email và reset password
    """
    
    __tablename__ = "otp_codes"

    # Thông tin cơ bản
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    otp_code = Column(String(10), nullable=False)
    
    # Loại OTP (registration, password_reset)
    otp_type = Column(String(50), nullable=False, default="registration")
    
    # Trạng thái
    is_used = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Thời gian
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<OTPCode(email='{self.email}', type='{self.otp_type}', used={self.is_used})>"
    
    def is_expired(self):
        """Kiểm tra OTP đã hết hạn chưa"""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Kiểm tra OTP có hợp lệ không"""
        return self.is_active and not self.is_used and not self.is_expired()