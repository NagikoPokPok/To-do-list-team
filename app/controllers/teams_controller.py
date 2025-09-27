"""
Teams API Controller - Quản lý nhóm làm việc
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Schemas
class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Team(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    owner_id: int
    member_count: int

class TeamMember(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    joined_at: datetime

# Router
router = APIRouter(prefix="/api/v1/teams", tags=["Teams"])

# Mock data
MOCK_TEAMS = [
    {
        "id": 1,
        "name": "Development Team",
        "description": "Nhóm phát triển sản phẩm chính",
        "created_at": "2025-09-20T10:00:00",
        "updated_at": "2025-09-26T10:00:00",
        "owner_id": 1,
        "member_count": 3
    },
    {
        "id": 2,
        "name": "Marketing Team",
        "description": "Nhóm marketing và truyền thông",
        "created_at": "2025-09-22T14:30:00",
        "updated_at": "2025-09-25T16:45:00",
        "owner_id": 1,
        "member_count": 2
    }
]

MOCK_MEMBERS = [
    {
        "id": 1,
        "email": "alexnghia1@gmail.com",
        "full_name": "Alex Nghia",
        "role": "owner",
        "joined_at": "2025-09-20T10:00:00",
        "team_id": 1
    },
    {
        "id": 2,
        "email": "member1@gmail.com",
        "full_name": "Member One",
        "role": "member",
        "joined_at": "2025-09-21T09:15:00",
        "team_id": 1
    },
    {
        "id": 3,
        "email": "member2@gmail.com",
        "full_name": "Member Two",
        "role": "member",
        "joined_at": "2025-09-22T11:30:00",
        "team_id": 1
    }
]

@router.get("/", response_model=dict)
async def get_teams(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of teams"""
    print(f"👥 Getting teams: limit={limit}, offset={offset}")
    
    teams = MOCK_TEAMS.copy()
    
    # Apply pagination
    total = len(teams)
    teams = teams[offset:offset + limit]
    
    return {
        "teams": teams,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.post("/", response_model=dict)
async def create_team(team_data: TeamCreate):
    """Create a new team"""
    print(f"👥 Creating team: {team_data.name}")
    
    new_team = {
        "id": len(MOCK_TEAMS) + 1,
        "name": team_data.name,
        "description": team_data.description,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "owner_id": 1,
        "member_count": 1
    }
    
    MOCK_TEAMS.append(new_team)
    
    # Add owner as member
    new_member = {
        "id": len(MOCK_MEMBERS) + 1,
        "email": "alexnghia1@gmail.com",
        "full_name": "Alex Nghia",
        "role": "owner",
        "joined_at": datetime.now().isoformat(),
        "team_id": new_team["id"]
    }
    MOCK_MEMBERS.append(new_member)
    
    return {
        "message": "Team tạo thành công",
        "team": new_team
    }

@router.get("/{team_id}", response_model=dict)
async def get_team(team_id: int):
    """Get team by ID"""
    print(f"🔍 Getting team: {team_id}")
    
    team = next((team for team in MOCK_TEAMS if team["id"] == team_id), None)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team không tìm thấy")
    
    return team

@router.put("/{team_id}", response_model=dict)
async def update_team(team_id: int, team_data: TeamUpdate):
    """Update team"""
    print(f"✏️ Updating team: {team_id}")
    
    team = next((team for team in MOCK_TEAMS if team["id"] == team_id), None)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team không tìm thấy")
    
    # Update fields
    if team_data.name is not None:
        team["name"] = team_data.name
    if team_data.description is not None:
        team["description"] = team_data.description
    
    team["updated_at"] = datetime.now().isoformat()
    
    return {
        "message": "Team cập nhật thành công",
        "team": team
    }

@router.get("/{team_id}/members", response_model=dict)
async def get_team_members(team_id: int):
    """Get team members"""
    print(f"👤 Getting members for team: {team_id}")
    
    team = next((team for team in MOCK_TEAMS if team["id"] == team_id), None)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team không tìm thấy")
    
    members = [member for member in MOCK_MEMBERS if member.get("team_id") == team_id]
    
    return {
        "team_id": team_id,
        "members": members,
        "total": len(members)
    }

@router.post("/{team_id}/invite", response_model=dict)
async def invite_member(team_id: int, email: str):
    """Invite member to team"""
    print(f"📧 Inviting {email} to team: {team_id}")
    
    team = next((team for team in MOCK_TEAMS if team["id"] == team_id), None)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team không tìm thấy")
    
    # Check if already member
    existing_member = next((member for member in MOCK_MEMBERS 
                          if member["email"] == email and member.get("team_id") == team_id), None)
    
    if existing_member:
        raise HTTPException(status_code=400, detail="User đã là thành viên của team")
    
    return {
        "message": f"Lời mời đã được gửi đến {email}",
        "team_id": team_id,
        "invited_email": email
    }

@router.delete("/{team_id}", response_model=dict)
async def delete_team(team_id: int):
    """Delete team"""
    print(f"🗑️ Deleting team: {team_id}")
    
    team_index = next((i for i, team in enumerate(MOCK_TEAMS) if team["id"] == team_id), None)
    
    if team_index is None:
        raise HTTPException(status_code=404, detail="Team không tìm thấy")
    
    deleted_team = MOCK_TEAMS.pop(team_index)
    
    # Remove all members
    global MOCK_MEMBERS
    MOCK_MEMBERS = [member for member in MOCK_MEMBERS if member.get("team_id") != team_id]
    
    return {
        "message": "Team xóa thành công",
        "team": deleted_team
    }

@router.get("/health", response_model=dict)
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "teams",
        "version": "1.0.0",
        "total_teams": len(MOCK_TEAMS)
    }