"""
Tasks Router - API endpoints cho quản lý công việc
CRUD operations cho tasks với phân quyền team manager/member
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models.user import User
from ..models.task import Task, TaskStatus, TaskPriority
from ..models.team import Team, TeamMember
from ..schemas import (
    TaskCreate, TaskUpdate, TaskResponse, Message,
    TaskStatusEnum, TaskPriorityEnum
)
from ..middleware.auth import get_current_user
from ..services.email_service import email_service

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua"),
    limit: int = Query(100, ge=1, le=1000, description="Số lượng bản ghi tối đa"),
    status: Optional[TaskStatusEnum] = Query(None, description="Lọc theo trạng thái"),
    priority: Optional[TaskPriorityEnum] = Query(None, description="Lọc theo độ ưu tiên"),
    assignee_id: Optional[int] = Query(None, description="Lọc theo người được gán"),
    team_id: Optional[int] = Query(None, description="Lọc theo team"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách tasks
    Team member chỉ xem được tasks của mình hoặc tasks không được gán
    Team manager xem được tất cả tasks trong team
    
    Args:
        skip: Số lượng bản ghi bỏ qua
        limit: Số lượng bản ghi tối đa
        status: Lọc theo trạng thái
        priority: Lọc theo độ ưu tiên
        assignee_id: Lọc theo người được gán
        team_id: Lọc theo team
        current_user: User hiện tại
        db: Database session
        
    Returns:
        List[TaskResponse]: Danh sách tasks
    """
    query = db.query(Task).options(joinedload(Task.creator), joinedload(Task.assignee))
    
    # Phân quyền xem tasks
    if current_user.is_team_manager():
        # Team manager có thể xem tất cả tasks hoặc tasks trong teams mà họ quản lý
        manager_teams = db.query(Team.id).filter(Team.manager_id == current_user.id).subquery()
        query = query.filter(
            or_(
                Task.creator_id == current_user.id,  # Tasks họ tạo
                Task.assignee_id == current_user.id,  # Tasks được gán cho họ
                Task.team_id.in_(manager_teams),  # Tasks trong teams họ quản lý
                Task.team_id.is_(None)  # Tasks không thuộc team nào
            )
        )
    else:
        # Team member chỉ xem được tasks của mình
        query = query.filter(
            or_(
                Task.creator_id == current_user.id,  # Tasks họ tạo
                Task.assignee_id == current_user.id,  # Tasks được gán cho họ
                and_(Task.assignee_id.is_(None), Task.team_id.is_(None))  # Tasks chưa được gán
            )
        )
    
    # Áp dụng filters
    if status:
        query = query.filter(Task.status == TaskStatus(status.value))
    
    if priority:
        query = query.filter(Task.priority == TaskPriority(priority.value))
        
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
        
    if team_id:
        query = query.filter(Task.team_id == team_id)
    
    # Sắp xếp theo created_at desc
    query = query.order_by(Task.created_at.desc())
    
    # Phân trang
    tasks = query.offset(skip).limit(limit).all()
    
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin chi tiết một task
    
    Args:
        task_id: ID của task
        current_user: User hiện tại
        db: Database session
        
    Returns:
        TaskResponse: Thông tin task
        
    Raises:
        HTTPException: Nếu task không tồn tại hoặc không có quyền xem
    """
    task = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.team)
    ).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy task"
        )
    
    # Kiểm tra quyền xem task
    if not task.can_be_edited_by(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem task này"
        )
    
    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tạo task mới
    
    Args:
        task_data: Dữ liệu task mới
        current_user: User hiện tại
        db: Database session
        
    Returns:
        TaskResponse: Task vừa tạo
        
    Raises:
        HTTPException: Nếu assignee hoặc team không tồn tại
    """
    # Kiểm tra assignee có tồn tại không
    if task_data.assignee_id:
        assignee = db.query(User).filter(User.id == task_data.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng được gán task"
            )
        
        # Nếu có team_id, kiểm tra assignee có phải thành viên của team không
        if task_data.team_id:
            team_member = db.query(TeamMember).filter(
                TeamMember.team_id == task_data.team_id,
                TeamMember.user_id == task_data.assignee_id,
                TeamMember.is_active == True
            ).first()
            if not team_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Người dùng được gán phải là thành viên của nhóm"
                )
    
    # Kiểm tra team có tồn tại không
    if task_data.team_id:
        team = db.query(Team).filter(Team.id == task_data.team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy team"
            )
        
        # Kiểm tra quyền gán task cho team
        if not current_user.is_team_manager() and team.manager_id != current_user.id:
            # Kiểm tra user có phải member của team không
            is_member = db.query(TeamMember).filter(
                TeamMember.team_id == task_data.team_id,
                TeamMember.user_id == current_user.id,
                TeamMember.is_active == True
            ).first()
            
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền tạo task cho team này"
                )
    
    # Tạo task mới
    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=TaskPriority(task_data.priority.value),
        due_date=task_data.due_date,
        creator_id=current_user.id,
        assignee_id=task_data.assignee_id,
        team_id=task_data.team_id,
        status=TaskStatus.PENDING,
        start_date=datetime.utcnow()
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    # Gửi email thông báo nếu có assignee
    if task_data.assignee_id and task_data.assignee_id != current_user.id:
        assignee = db.query(User).filter(User.id == task_data.assignee_id).first()
        if assignee:
            due_date_str = task_data.due_date.strftime("%d/%m/%Y %H:%M") if task_data.due_date else None
            await email_service.send_task_assignment_email(
                assignee_email=assignee.email,
                assignee_name=assignee.full_name or assignee.username,
                task_title=new_task.title,
                assigner_name=current_user.full_name or current_user.email.split('@')[0],
                due_date=due_date_str
            )
    
    return new_task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cập nhật task
    
    Args:
        task_id: ID của task
        task_data: Dữ liệu cập nhật
        current_user: User hiện tại
        db: Database session
        
    Returns:
        TaskResponse: Task đã cập nhật
        
    Raises:
        HTTPException: Nếu task không tồn tại hoặc không có quyền chỉnh sửa
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy task"
        )
    
    # Kiểm tra quyền chỉnh sửa
    if not task.can_be_edited_by(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền chỉnh sửa task này"
        )
    
    # Cập nhật các trường
    update_data = task_data.model_dump(exclude_unset=True)
    print(f"Updating task {task_id} with data: {update_data}")
    
    for field, value in update_data.items():
        print(f"Setting {field} = {value}")
        if field == "status" and value:
            setattr(task, field, TaskStatus(value))
            # Cập nhật completed_at nếu status là completed
            if value == TaskStatusEnum.COMPLETED:
                task.completed_at = datetime.utcnow()
        elif field == "priority" and value:
            setattr(task, field, TaskPriority(value))
        elif field == "assignee_id" and value:
            # Kiểm tra assignee có tồn tại không
            assignee = db.query(User).filter(User.id == value).first()
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Không tìm thấy người dùng được gán task"
                )
            
            # Nếu task có team_id, kiểm tra assignee có phải thành viên của team không
            if task.team_id:
                from ..models.team import TeamMember
                team_member = db.query(TeamMember).filter(
                    TeamMember.team_id == task.team_id,
                    TeamMember.user_id == value,
                    TeamMember.is_active == True
                ).first()
                if not team_member:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Người dùng được gán phải là thành viên của nhóm"
                    )
            
            setattr(task, field, value)
        else:
            if value is not None:
                setattr(task, field, value)
    
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    print(f"Task {task_id} updated successfully. assignee_id = {task.assignee_id}")
    
    return task


@router.delete("/{task_id}", response_model=Message)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa task
    Chỉ creator hoặc team manager mới có thể xóa
    
    Args:
        task_id: ID của task
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công
        
    Raises:
        HTTPException: Nếu task không tồn tại hoặc không có quyền xóa
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy task"
        )
    
    # Chỉ creator hoặc team manager mới có thể xóa
    if task.creator_id != current_user.id and not current_user.is_team_manager():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người tạo task hoặc team manager mới có thể xóa task"
        )
    
    db.delete(task)
    db.commit()
    
    return Message(message="Task đã được xóa thành công")


@router.get("/my-tasks/", response_model=List[TaskResponse])
async def get_my_tasks(
    status: Optional[TaskStatusEnum] = Query(None, description="Lọc theo trạng thái"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách tasks của user hiện tại
    
    Args:
        status: Lọc theo trạng thái
        current_user: User hiện tại
        db: Database session
        
    Returns:
        List[TaskResponse]: Danh sách tasks của user
    """
    query = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee)
    ).filter(
        or_(
            Task.creator_id == current_user.id,
            Task.assignee_id == current_user.id
        )
    )
    
    if status:
        query = query.filter(Task.status == TaskStatus(status.value))
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    return tasks