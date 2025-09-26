"""
Notifications Router - API endpoints cho quản lý thông báo
CRUD operations cho notifications của user
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.user import User
from ..models.notification import Notification
from ..schemas import NotificationResponse, Message
from ..middleware.auth import get_current_user
from ..services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua"),
    limit: int = Query(20, ge=1, le=100, description="Số lượng bản ghi tối đa"),
    unread_only: bool = Query(False, description="Chỉ lấy thông báo chưa đọc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách thông báo của user hiện tại
    
    Args:
        skip: Số lượng bản ghi bỏ qua
        limit: Số lượng bản ghi tối đa
        unread_only: Chỉ lấy thông báo chưa đọc
        current_user: User hiện tại
        db: Database session
        
    Returns:
        List[NotificationResponse]: Danh sách thông báo
    """
    notifications = notification_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    
    return notifications


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy số lượng thông báo chưa đọc
    
    Args:
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Dict: Số lượng thông báo chưa đọc
    """
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return {"unread_count": count}


@router.put("/{notification_id}/read", response_model=Message)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Đánh dấu thông báo đã đọc
    
    Args:
        notification_id: ID của thông báo
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công
    """
    success = notification_service.mark_notification_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông báo hoặc thông báo đã được đọc"
        )
    
    return Message(message="Đã đánh dấu thông báo là đã đọc")


@router.put("/read-all", response_model=Message)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Đánh dấu tất cả thông báo đã đọc
    
    Args:
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công với số lượng đã cập nhật
    """
    count = notification_service.mark_all_as_read(
        db=db,
        user_id=current_user.id
    )
    
    return Message(message=f"Đã đánh dấu {count} thông báo là đã đọc")


@router.delete("/{notification_id}", response_model=Message)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa thông báo
    
    Args:
        notification_id: ID của thông báo
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông báo"
        )
    
    db.delete(notification)
    db.commit()
    
    return Message(message="Đã xóa thông báo thành công")