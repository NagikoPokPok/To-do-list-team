
"""
Schemas - Định nghĩa Pydantic models cho request/response
Validation và serialization dữ liệu API
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums cho các trạng thái
class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationTypeEnum(str, Enum):
    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_OVERDUE = "task_overdue"
    TEAM_INVITE = "team_invite"
    TEAM_JOINED = "team_joined"
    TEAM_LEFT = "team_left"
    COMMENT_ADDED = "comment_added"


class NotificationPriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# User Schemas
class UserBase(BaseModel):
    """Schema cơ bản cho User"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserResponse(UserBase):
    """Schema response cho User"""
    id: int
    is_active: bool
    is_verified: bool
    is_2fa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    """Schema để tạo User mới"""
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Schema để đăng nhập"""
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class OTPVerify(BaseModel):
    """Schema để xác thực OTP"""
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)


class OTPRequest(BaseModel):
    """Schema để yêu cầu gửi lại OTP"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema để yêu cầu reset mật khẩu"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema để xác nhận reset mật khẩu"""
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6)



class TeamMemberResponse(UserBase):
    """Schema response cho thành viên nhóm, bao gồm thông tin user và role"""
    id: int
    is_active: bool
    is_verified: bool
    is_2fa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    role: str
    joined_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema để cập nhật thông tin User"""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None


# Task Schemas
class TaskBase(BaseModel):
    """Schema cơ bản cho Task"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: TaskPriorityEnum = TaskPriorityEnum.MEDIUM
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Schema để tạo Task mới"""
    assignee_id: Optional[int] = None
    team_id: Optional[int] = None


class TaskUpdate(BaseModel):
    """Schema để cập nhật Task"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    priority: Optional[TaskPriorityEnum] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None


class TaskResponse(TaskBase):
    """Schema response cho Task"""
    id: int
    status: TaskStatusEnum
    creator_id: int
    assignee_id: Optional[int] = None
    team_id: Optional[int] = None
    start_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Team Schemas
class TeamBase(BaseModel):
    """Schema cơ bản cho Team"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    max_members: int = Field(default=50, ge=1, le=200)


class TeamCreate(TeamBase):
    """Schema để tạo Team mới"""
    pass


class TeamUpdate(BaseModel):
    """Schema để cập nhật Team"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    max_members: Optional[int] = Field(None, ge=1, le=200)


class TeamResponse(TeamBase):
    """Schema response cho Team"""
    id: int
    manager_id: int
    is_active: bool
    invite_code: Optional[str] = None
    invite_link_active: bool = True
    created_at: datetime
    member_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class TeamJoinRequest(BaseModel):
    """Schema để tham gia team bằng invite code"""
    invite_code: str = Field(..., min_length=16, max_length=16)


# Authentication Schemas
class Token(BaseModel):
    """Schema cho access token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Schema cho dữ liệu token"""
    user_id: Optional[int] = None
    email: Optional[str] = None


class Enable2FA(BaseModel):
    """Schema để bật 2FA"""
    totp_code: str = Field(..., min_length=6, max_length=6)


class Verify2FA(BaseModel):
    """Schema để xác thực 2FA"""
    totp_code: str = Field(..., min_length=6, max_length=6)


# Notification Schemas
class NotificationResponse(BaseModel):
    """Schema response cho Notification"""
    id: int
    title: str
    message: str
    notification_type: NotificationTypeEnum
    priority: NotificationPriorityEnum
    is_read: bool
    action_url: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class NotificationCreate(BaseModel):
    """Schema để tạo Notification"""
    title: str = Field(..., max_length=255)
    message: str
    notification_type: NotificationTypeEnum
    priority: NotificationPriorityEnum = NotificationPriorityEnum.NORMAL
    action_url: Optional[str] = None
    related_task_id: Optional[int] = None
    related_team_id: Optional[int] = None


# Email OTP Schemas
class EmailOTPRequest(BaseModel):
    """Schema để yêu cầu OTP qua email"""
    email: EmailStr


# Invitation Schemas
class InvitationCreate(BaseModel):
    email: EmailStr
    team_id: int

class InvitationResponse(BaseModel):
    id: int
    email: EmailStr
    team_id: int
    invited_by: int
    token: str
    is_accepted: bool
    created_at: datetime
    accepted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmailOTPVerify(BaseModel):
    """Schema để xác thực OTP email"""
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)


# Response Messages
class Message(BaseModel):
    """Schema cho thông báo"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Schema cho lỗi"""
    detail: str
    error_code: Optional[str] = None