from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.user import User
from ..models.invitation import Invitation
from ..schemas import InvitationResponse
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/invitations", tags=["Invitations"])

@router.get("/my", response_model=List[InvitationResponse])
def get_my_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách lời mời tham gia nhóm của user hiện tại
    """
    invitations = db.query(Invitation).filter(
        Invitation.email == current_user.email,
        Invitation.is_accepted == False
    ).all()
    return invitations
