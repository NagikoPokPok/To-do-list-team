"""
Cấu hình cơ sở dữ liệu SQLite sử dụng SQLAlchemy
Quản lý kết nối và session database
"""

from sqlalchemy import create_engine, inspect, text
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


def ensure_schema():
    """Đảm bảo schema mới nhất cho cơ sở dữ liệu hiện có"""
    inspector = inspect(engine)

    if "teams" in inspector.get_table_names():
        existing_columns = {col["name"] for col in inspector.get_columns("teams")}

        statements = []
        if "invite_code" not in existing_columns:
            statements.append("ALTER TABLE teams ADD COLUMN invite_code VARCHAR(100)")
        if "invite_link_active" not in existing_columns:
            statements.append("ALTER TABLE teams ADD COLUMN invite_link_active BOOLEAN DEFAULT 1")

        if statements:
            with engine.begin() as connection:
                for statement in statements:
                    connection.execute(text(statement))

        if "invite_code" not in existing_columns:
            from .models.team import Team  # Avoid circular import

            session = SessionLocal()
            try:
                for team in session.query(Team).filter(Team.invite_code.is_(None)).all():
                    team.generate_invite_code()
                session.commit()
            finally:
                session.close()