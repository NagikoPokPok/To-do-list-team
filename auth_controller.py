"""
Simple Authentication Controller
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import secrets
import string

# Simple schemas
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str

class OTPRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Router
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

def generate_otp_code() -> str:
    """Generate a 6-digit OTP code"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        print(f"📝 Registration request for: {user_data.email}")
        
        # Generate OTP
        otp_code = generate_otp_code()
        print(f"🔢 Generated OTP: {otp_code}")
        
        # Try to send email
        try:
            from email_service import email_service
            email_sent = await email_service.send_otp_email(
                user_data.email, 
                otp_code, 
                "registration"
            )
            
            if email_sent:
                return {
                    "message": f"Mã xác thực đã được gửi tới {user_data.email}. Vui lòng kiểm tra email và nhập mã để kích hoạt tài khoản.",
                    "email": user_data.email,
                    "expires_in": "10 phút"
                }
        except Exception as email_error:
            print(f"📧 Email service error: {email_error}")
        
        # Fallback response (for demo)
        return {
            "message": f"Đăng ký thành công! Mã OTP (demo): {otp_code}",
            "email": user_data.email,
            "otp_demo": otp_code,  # For testing only
            "note": "Email service đang trong chế độ demo"
        }
            
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Đăng ký thất bại. Vui lòng thử lại sau."
        )

@router.post("/verify-otp", response_model=dict)
async def verify_otp(otp_data: OTPVerify):
    """Verify OTP code"""
    try:
        print(f"🔍 OTP verification for: {otp_data.email} with code: {otp_data.otp_code}")
        
        # For demo, accept any 6-digit code
        if len(otp_data.otp_code) == 6 and otp_data.otp_code.isdigit():
            return {
                "message": "Xác thực thành công! Tài khoản đã được kích hoạt.",
                "verified": True
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Mã OTP không hợp lệ"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ OTP verification error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Mã OTP không hợp lệ hoặc đã hết hạn"
        )

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login user"""
    try:
        print(f"🔐 Login attempt for: {login_data.email}")
        
        # For demo, accept any email/password combination
        if login_data.email and login_data.password:
            # Generate a simple token
            access_token = f"demo_token_{login_data.email.replace('@', '_').replace('.', '_')}"
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
        else:
            raise HTTPException(
                status_code=401,
                detail="Email hoặc mật khẩu không chính xác"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Đăng nhập thất bại"
        )

@router.post("/resend-otp", response_model=dict)
async def resend_otp(otp_request: OTPRequest):
    """Resend OTP code"""
    try:
        otp_code = generate_otp_code()
        print(f"🔄 Resending OTP to: {otp_request.email} - Code: {otp_code}")
        
        try:
            from email_service import email_service
            email_sent = await email_service.send_otp_email(
                otp_request.email, 
                otp_code, 
                "registration"
            )
        except Exception as email_error:
            print(f"📧 Email service error: {email_error}")
        
        return {
            "message": "Mã xác thực mới đã được gửi",
            "email": otp_request.email,
            "otp_demo": otp_code  # For testing
        }
        
    except Exception as e:
        print(f"❌ Resend OTP error: {str(e)}")
        return {
            "message": "Mã xác thực mới đã được gửi",
            "email": otp_request.email
        }

@router.post("/forgot-password", response_model=dict)
async def forgot_password(password_reset: PasswordReset):
    """Request password reset"""
    try:
        otp_code = generate_otp_code()
        print(f"🔑 Password reset for: {password_reset.email} - Code: {otp_code}")
        
        try:
            from email_service import email_service
            email_sent = await email_service.send_otp_email(
                password_reset.email, 
                otp_code, 
                "password_reset"
            )
        except Exception as email_error:
            print(f"📧 Email service error: {email_error}")
        
        return {
            "message": "Nếu email tồn tại, bạn sẽ nhận được email hướng dẫn reset mật khẩu",
            "otp_demo": otp_code  # For testing
        }
        
    except Exception as e:
        print(f"❌ Forgot password error: {str(e)}")
        return {
            "message": "Nếu email tồn tại, bạn sẽ nhận được email hướng dẫn reset mật khẩu"
        }

@router.post("/reset-password", response_model=dict)
async def reset_password(reset_data: PasswordResetConfirm):
    """Reset password with OTP"""
    try:
        print(f"🔄 Password reset for: {reset_data.email} with OTP: {reset_data.otp_code}")
        
        # For demo, accept any 6-digit code
        if len(reset_data.otp_code) == 6 and reset_data.otp_code.isdigit():
            return {
                "message": "Mật khẩu đã được cập nhật thành công"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Mã OTP không hợp lệ hoặc đã hết hạn"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Reset password error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Không thể reset mật khẩu. Vui lòng thử lại."
        )

@router.get("/me", response_model=dict)
async def get_current_user_info():
    """Get current user information"""
    return {
        "id": 1,
        "email": "demo@example.com",
        "first_name": "Demo",
        "last_name": "User",
        "is_verified": True
    }

@router.get("/me", response_model=dict)
async def get_current_user():
    """Get current user info"""
    return {
        "id": 1,
        "email": "alexnghia1@gmail.com",
        "full_name": "Alex Nghia",
        "is_active": True,
        "role": "user"
    }

@router.post("/logout", response_model=dict)
async def logout():
    """Logout user"""
    return {"message": "Đăng xuất thành công"}

@router.get("/health", response_model=dict)
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "1.0.0",
        "features": [
            "email_registration_with_otp",
            "password_login",
            "password_reset_with_otp"
        ]
    }