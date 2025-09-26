"""
Teams Router - API endpoints cho quản lý teams
CRUD operations cho teams và team members với phân quyền
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional

from ..database import get_db
from ..models.user import User
from ..models.team import Team, TeamMember
from ..schemas import (
    TeamCreate, TeamUpdate, TeamResponse, UserResponse, Message, TeamJoinRequest
)
from ..middleware.auth import get_current_user

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
    # Lấy teams mà user là manager
    managed_teams = db.query(Team).filter(
        Team.manager_id == current_user.id,
        Team.is_active == True
    )
    
    # Lấy teams mà user là member
    member_team_ids = db.query(TeamMember.team_id).filter(
        TeamMember.user_id == current_user.id,
        TeamMember.is_active == True
    ).subquery()
    
    joined_teams = db.query(Team).filter(
        Team.id.in_(member_team_ids),
        Team.is_active == True
    )
    
    # Kết hợp cả hai danh sách
    teams = managed_teams.union(joined_teams).offset(skip).limit(limit).all()
    
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
    
    # User có thể xem nếu là manager của team
    if team.manager_id == current_user.id:
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tạo team mới
    Mọi user đều có thể tạo team
    
    Args:
        team_data: Dữ liệu team mới
        current_user: User hiện tại
        db: Database session
        
    Returns:
        TeamResponse: Team vừa tạo
    """

    # Tạo team mới với invite code
    new_team = Team(
        name=team_data.name,
        description=team_data.description,
        max_members=team_data.max_members,
        manager_id=current_user.id,
        is_active=True
    )

    # Tạo invite code
    new_team.generate_invite_code()

    db.add(new_team)
    db.commit()
    db.refresh(new_team)

    # Thêm manager vào TeamMember
    manager_member = TeamMember(
        team_id=new_team.id,
        user_id=current_user.id,
        role="manager",
        is_active=True
    )
    db.add(manager_member)
    db.commit()

    new_team.member_count = 1
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


from ..schemas import TeamMemberResponse

@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách members của team, trả về cả role
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy team"
        )
    # Kiểm tra quyền xem team: chỉ cần là thành viên đang hoạt động hoặc là manager_id
    is_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id,
        TeamMember.is_active == True
    ).first()
    if not (team.manager_id == current_user.id or is_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem team này"
        )
    team.member_count = team.get_member_count()

    members = db.query(User, TeamMember).join(
        TeamMember, User.id == TeamMember.user_id
    ).filter(
        TeamMember.team_id == team_id,
        TeamMember.is_active == True
    ).all()
    result = []
    for user, member in members:
        user_dict = user.__dict__.copy()
        user_dict['role'] = member.role
        user_dict['joined_at'] = member.joined_at
        result.append(TeamMemberResponse(**user_dict))
    return result


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
    # member.left_at = db.func.now()
    member.left_at = func.now()
    db.commit()
    
    return Message(message="Đã xóa member khỏi team thành công")


@router.post("/join", response_model=Message)
async def join_team_by_invite(
    join_request: TeamJoinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tham gia team bằng invite code
    
    Args:
        join_request: Request chứa invite code
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Message: Thông báo thành công
    """
    # Tìm team bằng invite code
    team = db.query(Team).filter(
        Team.invite_code == join_request.invite_code,
        Team.is_active == True,
        Team.invite_link_active == True
    ).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liên kết tham gia không hợp lệ hoặc đã hết hạn"
        )
    
    # Kiểm tra user đã là member chưa
    existing_member = db.query(TeamMember).filter(
        TeamMember.team_id == team.id,
        TeamMember.user_id == current_user.id,
        TeamMember.is_active == True
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn đã là thành viên của team này"
        )
    
    # Kiểm tra số lượng member
    if not team.can_add_member():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team này đã đạt số lượng thành viên tối đa"
        )
    
    # Thêm member mới
    new_member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role="member",
        is_active=True
    )
    
    db.add(new_member)
    db.commit()
    
    return Message(message=f"Đã tham gia team '{team.name}' thành công")


@router.get("/{team_id}/invite-link")
async def get_team_invite_link(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy link mời tham gia team
    Chỉ manager của team mới có thể lấy link
    
    Args:
        team_id: ID của team
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Dict: Invite link và code
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy team"
        )
    
    # Chỉ manager mới có thể lấy invite link
    if team.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ manager của team mới có thể lấy link mời"
        )
    
    # Tạo invite code nếu chưa có
    if not team.invite_code:
        team.generate_invite_code()
        db.commit()
    
    return {
        "invite_code": team.invite_code,
        "invite_link": team.get_invite_link(),
        "is_active": team.invite_link_active
    }


@router.put("/{team_id}/invite-link/toggle")
async def toggle_invite_link(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bật/tắt invite link
    
    Args:
        team_id: ID của team
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Dict: Trạng thái mới của invite link
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy team"
        )
    
    # Chỉ manager mới có thể toggle invite link
    if team.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ manager của team mới có thể thay đổi trạng thái invite link"
        )
    
    # Toggle trạng thái
    team.invite_link_active = not team.invite_link_active
    db.commit()
    
    status_text = "kích hoạt" if team.invite_link_active else "vô hiệu hóa"
    return {
        "message": f"Đã {status_text} invite link",
        "is_active": team.invite_link_active
    }


@router.put("/{team_id}/invite-link/regenerate")
async def regenerate_invite_code(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tạo lại invite code mới
    
    Args:
        team_id: ID của team
        current_user: User hiện tại
        db: Database session
        
    Returns:
        Dict: Invite code và link mới
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy team"
        )
    
    # Chỉ manager mới có thể regenerate invite code
    if team.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ manager của team mới có thể tạo lại invite code"
        )
    
    # Tạo invite code mới
    team.generate_invite_code()
    db.commit()
    
    return {
        "message": "Đã tạo lại invite code mới",
        "invite_code": team.invite_code,
        "invite_link": team.get_invite_link(),
        "is_active": team.invite_link_active
    }