"""
Service cho Team - Thêm thành viên vào team
"""
from sqlalchemy.orm import Session
from ..models.team import TeamMember

def add_member_to_team(db: Session, team_id: int, user_id: int, role: str = "member"):
    member = TeamMember(team_id=team_id, user_id=user_id, role=role, is_active=True)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member
