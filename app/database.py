"""
Cấu hình cơ sở dữ liệu SQLite sử dụng SQLAlchemy
Quản lý kết nối và session database
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Tạo engine kết nối cơ sở dữ liệu
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # Chỉ cần thiết cho SQLite
)

# Tạo SessionLocal class để tạo session instances
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tạo Base class cho các models
Base = declarative_base()


def get_db():
    """
    Dependency để lấy database session
    Đảm bảo session được đóng sau mỗi request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()