"""
API endpoints cho lời mời thành viên nhóm
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..models import Invitation  # Import Invitation model from models package
from ..schemas import InvitationCreate, InvitationResponse, Message
from ..services import invitation_service
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/invitations", tags=["Invitations"])

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

@router.delete("/{invitation_id}", response_model=Message)
def cancel_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Hủy lời mời (chỉ người tạo mới có thể hủy)
    """
    invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Lời mời không tồn tại.")
    
    if invitation.invited_by != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền hủy lời mời này.")
    
    if invitation.is_accepted:
        raise HTTPException(status_code=400, detail="Không thể hủy lời mời đã được chấp nhận.")
    
    db.delete(invitation)
    db.commit()
    return Message(message="Hủy lời mời thành công!")
