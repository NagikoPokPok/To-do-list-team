"""
API endpoints cho lời mời thành viên nhóm
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..schemas import InvitationCreate, InvitationResponse, Message
from ..services import invitation_service
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/invitations", tags=["Invitations"])

@router.post("/invite", response_model=InvitationResponse)
def invite_member(
    invitation_in: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Gửi lời mời thành viên vào nhóm qua email
    """
    invitation = invitation_service.create_invitation(db, invitation_in, invited_by=current_user.id)
    return invitation

@router.get("/accept/{token}", response_model=Message)
def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Thành viên chấp nhận lời mời tham gia nhóm
    """
    ok = invitation_service.accept_invitation(db, token, current_user)
    if not ok:
        raise HTTPException(status_code=400, detail="Lời mời không hợp lệ hoặc đã được sử dụng.")
    return Message(message="Tham gia nhóm thành công!")
