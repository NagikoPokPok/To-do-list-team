"""
Cấu hình chính cho ứng dụng Todo List
Sử dụng Pydantic Settings để quản lý cấu hình môi trường
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Lớp cấu hình chính cho ứng dụng"""
    
    # Cấu hình ứng dụng cơ bản
    app_name: str = "Todo List Application"
    app_url: str = "http://localhost:8000"
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Cấu hình cơ sở dữ liệu
    database_url: str = "sqlite:///./todo_app.db"
    
    # Cấu hình Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    
    # Cấu hình 2FA
    totp_secret_key: str = "your-totp-secret-key"
    
    # Cấu hình môi trường
    environment: str = "development"
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


# Tạo instance cấu hình toàn cục
settings = Settings()