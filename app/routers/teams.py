"""
Teams Router - API endpoints cho quản lý teams
CRUD operations cho teams và team members với phân quyền
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from ..database import get_db
from ..models.user import User
from ..models.team import Team, TeamMember
from ..schemas import (
    TeamCreate, TeamUpdate, TeamResponse, UserResponse, Message
)
from ..middleware.auth import get_current_user, get_current_team_manager

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/", response_model=List[TeamResponse])
async def get_teams(
    skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua"),
    limit: int = Query(100, ge=1, le=1000, description="Số lượng bản ghi tối đa"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách teams
    Team manager xem được tất cả teams họ quản lý
    Team member xem được teams họ tham gia
    
    Args:
        skip: Số lượng bản ghi bỏ qua
        limit: Số lượng bản ghi tối đa  
        current_user: User hiện tại
        db: Database session
        
    Returns:
        List[TeamResponse]: Danh sách teams
    """
    if current_user.is_team_manager():
        # Team manager xem tất cả teams họ quản lý
        teams = db.query(Team).filter(
            Team.manager_id == current_user.id,
            Team.is_active == True
        ).offset(skip).limit(limit).all()
    else:
        # Team member xem teams họ tham gia
        team_ids = db.query(TeamMember.team_id).filter(
            TeamMember.user_id == current_user.id,
            TeamMember.is_active == True
        ).subquery()
        
        teams = db.query(Team).filter(
            Team.id.in_(team_ids),
            Team.is_active == True
        ).offset(skip).limit(limit).all()
    
    # Thêm member_count cho mỗi team
    for team in teams:
        team.member_count = team.get_member_count()
    
    return teams


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin chi tiết team
    
    Args:
        team_id: ID của team
        current_user: User hiện tại
        db: Database session
        
    Returns:
        TeamResponse: Thông tin team
        
    Raises:
        HTTPException: Nếu team không tồn tại hoặc không có quyền xem
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy team"
        )
    
    # Kiểm tra quyền xem team
    can_view = False
    
    if current_user.is_team_manager() and team.manager_id == current_user.id:
        can_view = True
    else:
        # Kiểm tra user có phải member của team không
        is_member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.is_active == True
        ).first()
        if is_member:
            can_view = True
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem team này"
        )
    
    team.member_count = team.get_member_count()
    return team


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_team_manager),
    db: Session = Depends(get_db)
):
    """
    Tạo team mới
    Chỉ team manager mới có thể tạo team
    
    Args:
        team_data: Dữ liệu team mới
        current_user: User hiện tại (phải là team manager)
        db: Database session
        
    Returns:
        TeamResponse: Team vừa tạo
    """
    # Tạo team mới
    new_team = Team(
        name=team_data.name,
        description=team_data.description,
        max_members=team_data.max_members,
        manager_id=current_user.id,
        is_active=True
    )
    
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    
    new_team.member_count = 0
    return new_team


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cập nhật thông tin team
    Chỉ manager của team mới có thể cập nhật
    
    Args:
        team_id: ID của team
        team_data: Dữ liệu cập nhật
        current_user: User hiện tại
        db: Database session
        
    Returns:
        TeamResponse: Team đã cập nhật
        
    Raises:
        HTTPException: Nếu team không tồn tại hoặc không có quyền chỉnh sửa
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy team"
        )
    
    # Chỉ manager của team mới có thể cập nhật
    if team.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ manager của team mới có thể cập nhật thông tin team"
        )
    
    # Cập nhật các trường
    update_data = team_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if value is not None:
            setattr(team, field, value)
    
    db.commit()
    db.refresh(team)
    
    team.member_count = team.get_member_count()
    return team


@router.delete("/{team_id}", response_model=Message)
async def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa team (soft delete)
    Chỉ manager của team mới có thể xóa
    
    Args:
        team_id: ID của team
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công
        
    Raises:
        HTTPException: Nếu team không tồn tại hoặc không có quyền xóa
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy team"
        )
    
    # Chỉ manager của team mới có thể xóa
    if team.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ manager của team mới có thể xóa team"
        )
    
    # Soft delete
    team.is_active = False
    db.commit()
    
    return Message(message="Team đã được xóa thành công")


@router.get("/{team_id}/members", response_model=List[UserResponse])
async def get_team_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách members của team
    
    Args:
        team_id: ID của team
        current_user: User hiện tại
        db: Database session
        
    Returns:
        List[UserResponse]: Danh sách members
        
    Raises:
        HTTPException: Nếu team không tồn tại hoặc không có quyền xem
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy team"
        )
    
    # Kiểm tra quyền xem members
    can_view = False
    
    if current_user.is_team_manager() and team.manager_id == current_user.id:
        can_view = True
    else:
        # Kiểm tra user có phải member của team không
        is_member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.is_active == True
        ).first()
        if is_member:
            can_view = True
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem danh sách members của team này"
        )
    
    # Lấy danh sách members
    members = db.query(User).join(
        TeamMember, User.id == TeamMember.user_id
    ).filter(
        TeamMember.team_id == team_id,
        TeamMember.is_active == True
    ).all()
    
    return members


@router.post("/{team_id}/members/{user_id}", response_model=Message)
async def add_team_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Thêm member vào team
    Chỉ manager của team mới có thể thêm member
    
    Args:
        team_id: ID của team
        user_id: ID của user cần thêm
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công
        
    Raises:
        HTTPException: Nếu không có quyền hoặc dữ liệu không hợp lệ
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy team"
        )
    
    # Chỉ manager của team mới có thể thêm member
    if team.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ manager của team mới có thể thêm member"
        )
    
    # Kiểm tra user tồn tại
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy user"
        )
    
    # Kiểm tra team có thể thêm member không
    if not team.can_add_member():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team đã đạt số lượng member tối đa"
        )
    
    # Kiểm tra user đã là member chưa
    existing_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
        TeamMember.is_active == True
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User đã là member của team này"
        )
    
    # Thêm member mới
    new_member = TeamMember(
        team_id=team_id,
        user_id=user_id,
        role="member",
        is_active=True
    )
    
    db.add(new_member)
    db.commit()
    
    return Message(message="Đã thêm member vào team thành công")


@router.delete("/{team_id}/members/{user_id}", response_model=Message)
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa member khỏi team
    Manager có thể xóa bất kỳ member nào, member có thể tự xóa mình
    
    Args:
        team_id: ID của team
        user_id: ID của user cần xóa
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công
        
    Raises:
        HTTPException: Nếu không có quyền hoặc dữ liệu không hợp lệ
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy team"
        )
    
    # Kiểm tra quyền xóa member
    can_remove = False
    
    if team.manager_id == current_user.id:
        # Manager có thể xóa bất kỳ member nào
        can_remove = True
    elif current_user.id == user_id:
        # User có thể tự xóa mình khỏi team
        can_remove = True
    
    if not can_remove:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa member này khỏi team"
        )
    
    # Tìm member relationship
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
        TeamMember.is_active == True
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User không phải là member của team này"
        )
    
    # Không cho phép manager tự xóa mình nếu là manager duy nhất
    if user_id == team.manager_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manager không thể tự xóa mình khỏi team. Vui lòng chuyển quyền quản lý trước."
        )
    
    # Xóa member (soft delete)
    member.is_active = False
    member.left_at = db.func.now()
    db.commit()
    
    return Message(message="Đã xóa member khỏi team thành công")