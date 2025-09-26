"""
Model Invitation - Lưu trữ lời mời tham gia nhóm
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(64), unique=True, index=True)
    is_accepted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))

    team = relationship("Team")
    inviter = relationship("User")

    def __repr__(self):
        return f"<Invitation(email={self.email}, team_id={self.team_id}, invited_by={self.invited_by})>"
