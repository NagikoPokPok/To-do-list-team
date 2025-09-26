"""
Model User - Quản lý thông tin người dùng
Bao gồm chức năng 2FA và phân quyền team manager/member
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    """
    Model User định nghĩa cấu trúc bảng người dùng
    Hỗ trợ 2FA và phân quyền
    """
    
    __tablename__ = "users"

    # Thông tin cơ bản
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200))
    phone_number = Column(String(20))
    avatar_url = Column(String(500))
    
    # Trạng thái tài khoản
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Thông tin 2FA
    totp_secret = Column(String(100))  # Secret key cho Google Authenticator
    is_2fa_enabled = Column(Boolean, default=False)
    backup_codes = Column(Text)  # Mã backup cho 2FA (JSON string)
    
    # OTP cho email verification
    email_otp = Column(String(10))
    email_otp_expiry = Column(DateTime)
    
    # Thời gian
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Quan hệ với các bảng khác
    teams = relationship("Team", back_populates="manager", foreign_keys="Team.manager_id")
    team_memberships = relationship("TeamMember", back_populates="user")
    tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")
    created_tasks = relationship("Task", back_populates="creator", foreign_keys="Task.creator_id")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
    
    def can_create_teams(self) -> bool:
        """Mọi user đều có thể tạo team"""
        return self.is_active
    
    def can_join_teams(self) -> bool:
        """Mọi user đều có thể tham gia team"""
        return self.is_active
    
    def is_team_manager(self) -> bool:
        """Kiểm tra user có quản lý ít nhất một team đang hoạt động không"""
        return any(team.is_active for team in self.teams if team.manager_id == self.id)

    def is_team_member(self) -> bool:
        """Kiểm tra user có đang là thành viên của bất kỳ team nào không"""
        return any(membership.is_active for membership in self.team_memberships)