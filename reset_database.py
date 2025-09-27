"""
Script để reset database - xóa tất cả user để test đăng ký
"""

import sqlite3
import os

def reset_database():
    """Xóa tất cả user để test đăng ký"""

    db_path = "todo_app.db"

    if not os.path.exists(db_path):
        print("Database không tồn tại!")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Đếm số user hiện tại
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"🔍 Tìm thấy {count} user trong database")

        if count == 0:
            print("✅ Database đã trống!")
            return

        # Xóa tất cả user
        cursor.execute("DELETE FROM users")
        print(f"🗑️ Đã xóa {count} user")

        # Reset auto-increment
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
        print("🔄 Đã reset auto-increment")

        conn.commit()
        print("✅ Database đã được reset thành công!")

    except Exception as e:
        print(f"❌ Lỗi khi reset database: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Bắt đầu reset database...")
    reset_database()
    print("✅ Hoàn thành!")