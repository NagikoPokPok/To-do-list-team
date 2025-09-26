"""
Notification Service - Quản lý tạo và gửi thông báo
Hỗ trợ thông báo real-time và email
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..models.notification import Notification, NotificationTypeEnum, NotificationPriorityEnum
from ..models.user import User
from ..models.task import Task
from ..models.team import Team
from ..services.email_service import email_service


class NotificationService:
    """Service để quản lý notifications"""
    
    def __init__(self):
        pass
    
    async def create_notification(
        self,
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationTypeEnum,
        priority: NotificationPriorityEnum = NotificationPriorityEnum.NORMAL,
        action_url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        related_task_id: Optional[int] = None,
        related_team_id: Optional[int] = None,
        send_email: bool = True
    ) -> Notification:
        """
        Tạo notification mới
        
        Args:
            db: Database session
            user_id: ID của user nhận thông báo
            title: Tiêu đề thông báo
            message: Nội dung thông báo
            notification_type: Loại thông báo
            priority: Mức độ ưu tiên
            action_url: URL để thực hiện hành động
            data: Dữ liệu bổ sung (dict)
            related_task_id: ID task liên quan
            related_team_id: ID team liên quan
            send_email: Có gửi email không
            
        Returns:
            Notification: Thông báo đã tạo
        """
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            data=json.dumps(data) if data else None,
            related_task_id=related_task_id,
            related_team_id=related_team_id
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Gửi email nếu yêu cầu
        if send_email and priority in [NotificationPriorityEnum.HIGH, NotificationPriorityEnum.URGENT]:
            await self._send_email_notification(db, notification)
        
        return notification
    
    async def create_task_assigned_notification(
        self,
        db: Session,
        task: Task,
        assignee: User,
        assigner: User
    ) -> Optional[Notification]:
        """
        Tạo thông báo khi task được giao
        
        Args:
            db: Database session
            task: Task được giao
            assignee: User được giao task
            assigner: User giao task
            
        Returns:
            Notification: Thông báo đã tạo
        """
        if assignee.id == assigner.id:
            return None  # Không tạo thông báo nếu tự giao cho mình
        
        title = f"Bạn được giao task mới: {task.title}"
        message = f"Task '{task.title}' đã được giao cho bạn bởi {assigner.full_name or assigner.username}"
        
        priority = NotificationPriorityEnum.HIGH if task.priority == "urgent" else NotificationPriorityEnum.NORMAL
        
        return await self.create_notification(
            db=db,
            user_id=assignee.id,
            title=title,
            message=message,
            notification_type=NotificationTypeEnum.TASK_ASSIGNED,
            priority=priority,
            action_url=f"/tasks/{task.id}",
            related_task_id=task.id,
            related_team_id=task.team_id
        )
    
    async def create_task_updated_notification(
        self,
        db: Session,
        task: Task,
        updated_by: User,
        changes: Dict[str, Any]
    ) -> List[Notification]:
        """
        Tạo thông báo khi task được cập nhật
        
        Args:
            db: Database session
            task: Task được cập nhật
            updated_by: User cập nhật
            changes: Các thay đổi
            
        Returns:
            List[Notification]: Danh sách thông báo đã tạo
        """
        notifications = []
        
        # Thông báo cho assignee (nếu không phải người cập nhật)
        if task.assignee and task.assignee.id != updated_by.id:
            title = f"Task '{task.title}' đã được cập nhật"
            message = f"Task được cập nhật bởi {updated_by.full_name or updated_by.username}"
            
            notification = await self.create_notification(
                db=db,
                user_id=task.assignee.id,
                title=title,
                message=message,
                notification_type=NotificationTypeEnum.TASK_UPDATED,
                priority=NotificationPriorityEnum.NORMAL,
                action_url=f"/tasks/{task.id}",
                data=changes,
                related_task_id=task.id,
                related_team_id=task.team_id
            )
            notifications.append(notification)
        
        # Thông báo cho creator (nếu không phải người cập nhật và không phải assignee)
        if (task.creator and 
            task.creator.id != updated_by.id and 
            task.creator.id != (task.assignee.id if task.assignee else None)):
            
            title = f"Task '{task.title}' đã được cập nhật"
            message = f"Task do bạn tạo đã được cập nhật bởi {updated_by.full_name or updated_by.username}"
            
            notification = await self.create_notification(
                db=db,
                user_id=task.creator.id,
                title=title,
                message=message,
                notification_type=NotificationTypeEnum.TASK_UPDATED,
                priority=NotificationPriorityEnum.NORMAL,
                action_url=f"/tasks/{task.id}",
                data=changes,
                related_task_id=task.id,
                related_team_id=task.team_id
            )
            notifications.append(notification)
        
        return notifications
    
    async def create_task_completed_notification(
        self,
        db: Session,
        task: Task,
        completed_by: User
    ) -> List[Notification]:
        """
        Tạo thông báo khi task hoàn thành
        
        Args:
            db: Database session
            task: Task hoàn thành
            completed_by: User hoàn thành task
            
        Returns:
            List[Notification]: Danh sách thông báo đã tạo
        """
        notifications = []
        
        # Thông báo cho creator (nếu không phải người hoàn thành)
        if task.creator and task.creator.id != completed_by.id:
            title = f"Task '{task.title}' đã hoàn thành"
            message = f"Task do bạn tạo đã được hoàn thành bởi {completed_by.full_name or completed_by.username}"
            
            notification = await self.create_notification(
                db=db,
                user_id=task.creator.id,
                title=title,
                message=message,
                notification_type=NotificationTypeEnum.TASK_COMPLETED,
                priority=NotificationPriorityEnum.NORMAL,
                action_url=f"/tasks/{task.id}",
                related_task_id=task.id,
                related_team_id=task.team_id
            )
            notifications.append(notification)
        
        return notifications
    
    async def create_team_joined_notification(
        self,
        db: Session,
        team: Team,
        new_member: User
    ) -> Optional[Notification]:
        """
        Tạo thông báo khi có thành viên mới tham gia team
        
        Args:
            db: Database session
            team: Team được tham gia
            new_member: Thành viên mới
            
        Returns:
            Notification: Thông báo cho manager
        """
        manager = db.query(User).filter(User.id == team.manager_id).first()
        if not manager or manager.id == new_member.id:
            return None
        
        title = f"Thành viên mới tham gia team '{team.name}'"
        message = f"{new_member.full_name or new_member.username} đã tham gia team của bạn"
        
        return await self.create_notification(
            db=db,
            user_id=manager.id,
            title=title,
            message=message,
            notification_type=NotificationTypeEnum.TEAM_JOINED,
            priority=NotificationPriorityEnum.NORMAL,
            action_url=f"/teams/{team.id}",
            related_team_id=team.id
        )
    
    async def create_overdue_notifications(
        self,
        db: Session,
        overdue_tasks: List[Task]
    ) -> List[Notification]:
        """
        Tạo thông báo cho các task quá hạn
        
        Args:
            db: Database session
            overdue_tasks: Danh sách task quá hạn
            
        Returns:
            List[Notification]: Danh sách thông báo đã tạo
        """
        notifications = []
        
        for task in overdue_tasks:
            if task.assignee:
                title = f"Task quá hạn: {task.title}"
                message = f"Task '{task.title}' đã quá hạn. Hạn chót: {task.due_date.strftime('%d/%m/%Y %H:%M')}"
                
                notification = await self.create_notification(
                    db=db,
                    user_id=task.assignee.id,
                    title=title,
                    message=message,
                    notification_type=NotificationTypeEnum.TASK_OVERDUE,
                    priority=NotificationPriorityEnum.URGENT,
                    action_url=f"/tasks/{task.id}",
                    related_task_id=task.id,
                    related_team_id=task.team_id,
                    send_email=True
                )
                notifications.append(notification)
        
        return notifications
    
    def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Notification]:
        """
        Lấy danh sách thông báo của user
        
        Args:
            db: Database session
            user_id: ID của user
            skip: Số lượng bỏ qua
            limit: Số lượng tối đa
            unread_only: Chỉ lấy thông báo chưa đọc
            
        Returns:
            List[Notification]: Danh sách thông báo
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    def mark_notification_as_read(
        self,
        db: Session,
        notification_id: int,
        user_id: int
    ) -> bool:
        """
        Đánh dấu thông báo đã đọc
        
        Args:
            db: Database session
            notification_id: ID thông báo
            user_id: ID user (để kiểm tra quyền)
            
        Returns:
            bool: True nếu thành công
        """
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification and not notification.is_read:
            notification.mark_as_read()
            db.commit()
            return True
        
        return False
    
    def mark_all_as_read(
        self,
        db: Session,
        user_id: int
    ) -> int:
        """
        Đánh dấu tất cả thông báo đã đọc
        
        Args:
            db: Database session
            user_id: ID user
            
        Returns:
            int: Số lượng thông báo đã cập nhật
        """
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        
        db.commit()
        return count
    
    async def _send_email_notification(
        self,
        db: Session,
        notification: Notification
    ):
        """
        Gửi email thông báo
        
        Args:
            db: Database session
            notification: Thông báo cần gửi
        """
        try:
            user = db.query(User).filter(User.id == notification.user_id).first()
            if user and user.email:
                await email_service.send_notification_email(
                    email=user.email,
                    username=user.username,
                    title=notification.title,
                    message=notification.message,
                    action_url=notification.action_url
                )
                
                notification.mark_as_sent()
                db.commit()
        except Exception as e:
            print(f"Error sending notification email: {e}")


# Singleton instance
notification_service = NotificationService()