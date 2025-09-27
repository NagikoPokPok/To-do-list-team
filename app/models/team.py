"""
Model Team và TeamMember - Quản lý nhóm và thành viên
Hỗ trợ phân quyền team manager và team member
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..database import Base


class Team(Base):
    """
    Model Team định nghĩa cấu trúc bảng nhóm
    Mỗi team có một manager và nhiều member
    """
    
    __tablename__ = "teams"

    # Thông tin cơ bản
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    
    # Thông tin manager
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Team invitation link
    invite_code = Column(String(100), unique=True, index=True)
    invite_link_active = Column(Boolean, default=True)
    
    # Cài đặt team
    is_active = Column(Boolean, default=True)
    max_members = Column(Integer, default=50)
    
    # Thời gian
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    manager = relationship("User", back_populates="teams", foreign_keys=[manager_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="team")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', manager_id={self.manager_id})>"
    
    def get_member_count(self) -> int:
        """Lấy số lượng thành viên hiện tại"""
        return len([m for m in self.members if m.is_active])
    
    def can_add_member(self) -> bool:
        """Kiểm tra xem có thể thêm thành viên mới không"""
        return self.get_member_count() < self.max_members
    
    def is_manager(self, user_id: int) -> bool:
        """Kiểm tra xem user có phải manager của team này không"""
        return self.manager_id == user_id
    
    def generate_invite_code(self) -> str:
        """Tạo mã mời tham gia team"""
        self.invite_code = str(uuid.uuid4()).replace('-', '')[:16]
        return self.invite_code
    
    def get_invite_link(self, base_url: str = "http://localhost:8000") -> str:
        """Lấy link mời tham gia team"""
        if not self.invite_code:
            self.generate_invite_code()
        return f"{base_url}/join-team/{self.invite_code}"


class TeamMember(Base):
    """
    Model TeamMember định nghĩa quan hệ giữa User và Team
    Lưu trữ thông tin thành viên trong team
    """
    
    __tablename__ = "team_members"

    # Khóa chính
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Thông tin thành viên
    role = Column(String(50), default="member")  # member, deputy, etc.
    is_active = Column(Boolean, default=True)
    
    # Thời gian
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True))
    
    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")
    
    def __repr__(self):
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id}, role='{self.role}')>"
    
    def can_manage_tasks(self) -> bool:
        """Kiểm tra xem member có thể quản lý tasks không"""
        return self.role in ["deputy", "lead"] or self.user.is_team_manager()