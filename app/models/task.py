"""
Model Task - Quản lý công việc trong Todo List
Hỗ trợ gán task cho team member và theo dõi trạng thái
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class TaskStatus(enum.Enum):
    """Enum định nghĩa trạng thái của task"""
    PENDING = "pending"         # Đang chờ
    IN_PROGRESS = "in_progress" # Đang thực hiện
    COMPLETED = "completed"     # Hoàn thành
    CANCELLED = "cancelled"     # Đã hủy


class TaskPriority(enum.Enum):
    """Enum định nghĩa độ ưu tiên của task"""
    LOW = "low"         # Thấp
    MEDIUM = "medium"   # Trung bình
    HIGH = "high"       # Cao
    URGENT = "urgent"   # Khẩn cấp


class Task(Base):
    """
    Model Task định nghĩa cấu trúc bảng công việc
    Hỗ trợ phân công và theo dõi tiến độ
    """
    
    __tablename__ = "tasks"

    # Thông tin cơ bản
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Trạng thái và độ ưu tiên
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, index=True)
    
    # Thời gian
    start_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Quan hệ với User
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    
    # Quan hệ với Team
    team_id = Column(Integer, ForeignKey("teams.id"))
    
    # Relationships
    creator = relationship("User", back_populates="created_tasks", foreign_keys=[creator_id])
    assignee = relationship("User", back_populates="tasks", foreign_keys=[assignee_id])
    team = relationship("Team", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status.value}')>"
    
    def is_overdue(self) -> bool:
        """Kiểm tra xem task có quá hạn không"""
        if self.due_date and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            from datetime import datetime
            return datetime.now() > self.due_date.replace(tzinfo=None)
        return False
    
    def can_be_edited_by(self, user) -> bool:
        """Kiểm tra xem user có thể chỉnh sửa task này không"""
        return (
            user.id == self.creator_id or  # Người tạo task
            user.id == self.assignee_id or  # Người được gán task
            user.is_team_manager()  # Team manager
        )