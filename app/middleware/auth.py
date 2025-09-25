"""
Authentication Middleware - Dependencies cho xác thực user
Kiểm tra JWT token và phân quyền truy cập
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.user import User
from ..utils.auth import verify_token
from ..schemas import TokenData

# Khởi tạo HTTPBearer để lấy token từ header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency để lấy thông tin user hiện tại từ JWT token
    
    Args:
        credentials: Authorization credentials từ header
        db: Database session
        
    Returns:
        User: Thông tin user hiện tại
        
    Raises:
        HTTPException: Nếu token không hợp lệ hoặc user không tồn tại
    """
    # Exception cho trường hợp token không hợp lệ
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify và decode token
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
            
        # Lấy user_id từ payload
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id)
        
    except Exception:
        raise credentials_exception
    
    # Tìm user trong database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
        
    # Kiểm tra user có active không
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency để lấy user active hiện tại
    
    Args:
        current_user: User từ get_current_user dependency
        
    Returns:
        User: User active hiện tại
        
    Raises:
        HTTPException: Nếu user không active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Tài khoản không hoạt động"
        )
    return current_user


async def get_current_team_manager(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency để kiểm tra user có phải team manager không
    
    Args:
        current_user: User hiện tại
        
    Returns:
        User: Team manager user
        
    Raises:
        HTTPException: Nếu user không phải team manager
    """
    if not current_user.is_team_manager():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập. Chỉ team manager mới có thể thực hiện hành động này."
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency để lấy user hiện tại (optional)
    Không raise exception nếu không có token
    
    Args:
        credentials: Authorization credentials (optional)
        db: Database session
        
    Returns:
        Optional[User]: User nếu có token hợp lệ, None nếu không
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            return None
            
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        
        user = db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
        
        return user
        
    except Exception:
        return None


def require_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency yêu cầu user đã được verify email
    
    Args:
        current_user: User hiện tại
        
    Returns:
        User: Verified user
        
    Raises:
        HTTPException: Nếu user chưa verify email
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn cần xác thực email trước khi sử dụng tính năng này"
        )
    return current_user


class PermissionChecker:
    """
    Class để kiểm tra các quyền phức tạp
    """
    
    def __init__(self, required_role: str = None):
        self.required_role = required_role
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """
        Kiểm tra role của user
        
        Args:
            current_user: User hiện tại
            
        Returns:
            User: User có quyền phù hợp
            
        Raises:
            HTTPException: Nếu user không có quyền
        """
        if self.required_role and current_user.role != self.required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bạn cần có quyền {self.required_role} để thực hiện hành động này"
            )
        return current_user


# Tạo các permission checker có sẵn
require_team_manager = PermissionChecker("team_manager")
require_team_member = PermissionChecker("team_member")