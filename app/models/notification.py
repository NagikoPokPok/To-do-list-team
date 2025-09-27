"""
Model Notification - Quản lý thông báo cho người dùng
Hỗ trợ thông báo real-time và lưu trữ lịch sử
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from ..database import Base


class NotificationTypeEnum(PyEnum):
    """Enum cho các loại thông báo"""
    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_OVERDUE = "task_overdue"
    TEAM_INVITE = "team_invite"
    TEAM_JOINED = "team_joined"
    TEAM_LEFT = "team_left"
    COMMENT_ADDED = "comment_added"


class NotificationPriorityEnum(PyEnum):
    """Enum cho mức độ ưu tiên thông báo"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """
    Model Notification định nghĩa cấu trúc bảng thông báo
    Lưu trữ tất cả thông báo của người dùng
    """
    
    __tablename__ = "notifications"

    # Khóa chính
    id = Column(Integer, primary_key=True, index=True)
    
    # Thông tin người nhận
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Nội dung thông báo
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationTypeEnum), nullable=False)
    priority = Column(Enum(NotificationPriorityEnum), default=NotificationPriorityEnum.NORMAL)
    
    # Metadata
    data = Column(Text)  # JSON string chứa dữ liệu bổ sung
    action_url = Column(String(500))  # URL để thực hiện hành động
    
    # Trạng thái
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)  # Đã gửi qua email/push
    
    # Reference đến đối tượng liên quan
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    related_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    
    # Thời gian
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", backref="notifications")
    related_task = relationship("Task", backref="notifications")
    related_team = relationship("Team", backref="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.notification_type}')>"
    
    def mark_as_read(self):
        """Đánh dấu thông báo đã đọc"""
        self.is_read = True
        self.read_at = func.now()
    
    def mark_as_sent(self):
        """Đánh dấu thông báo đã gửi"""
        self.is_sent = True
        self.sent_at = func.now()
    
    def to_dict(self):
        """Chuyển đổi thành dict cho JSON response"""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.notification_type.value,
            "priority": self.priority.value,
            "is_read": self.is_read,
            "action_url": self.action_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }