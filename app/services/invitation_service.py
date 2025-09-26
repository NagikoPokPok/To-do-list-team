"""
Service xử lý logic lời mời thành viên nhóm
"""
import secrets
from sqlalchemy.orm import Session
from ..models.invitation import Invitation
from ..models.team import Team
from ..models.user import User
from ..schemas import InvitationCreate


def create_invitation(db: Session, invitation_in: InvitationCreate, invited_by: int) -> Invitation:
    # Xóa các lời mời cũ chưa accept cùng email và team_id
    db.query(Invitation).filter(
        Invitation.email == invitation_in.email,
        Invitation.team_id == invitation_in.team_id,
        Invitation.is_accepted == False
    ).delete()
    db.commit()

    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        email=invitation_in.email,
        team_id=invitation_in.team_id,
        invited_by=invited_by,
        token=token
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def get_invitation_by_token(db: Session, token: str) -> Invitation:
    return db.query(Invitation).filter(Invitation.token == token).first()


def accept_invitation(db: Session, token: str, user: User) -> bool:
    invitation = get_invitation_by_token(db, token)
    if not invitation or invitation.is_accepted:
        return False
    # Thêm user vào team
    from . import team_service
    team_service.add_member_to_team(db, invitation.team_id, user.id)
    invitation.is_accepted = True
    from datetime import datetime
    invitation.accepted_at = datetime.utcnow()
    db.commit()
    return True
