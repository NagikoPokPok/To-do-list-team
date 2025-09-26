"""
Cấu hình chính cho ứng dụng Todo List
Sử dụng Pydantic Settings để quản lý cấu hình môi trường
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Lớp cấu hình chính cho ứng dụng"""
    
    # Cấu hình ứng dụng cơ bản
    app_name: str = "Todo List Clean"
    app_url: str = "http://localhost:8000"
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Aliases cho tương thích
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Cấu hình cơ sở dữ liệu
    database_url: str = "sqlite:///./todo_app.db"
    
    # Cấu hình Email từ .env
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    
    # Aliases cho tương thích với email service
    SMTP_HOST: str = "smtp.gmail.com"
    FROM_EMAIL: Optional[str] = None
    FROM_NAME: str = "Todo List Team"
    
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