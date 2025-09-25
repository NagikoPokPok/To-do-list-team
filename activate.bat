@echo off
REM ============================================
REM Todo App Virtual Environment Activation Script
REM ============================================
REM Script để kích hoạt môi trường ảo và kiểm tra cài đặt

echo.
echo ========================================
echo    🚀 TODO APP ENVIRONMENT SETUP
echo ========================================
echo.

REM Kiểm tra xem virtual environment có tồn tại không
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment không tồn tại!
    echo 📝 Hãy chạy: python -m venv venv
    pause
    exit /b 1
)

REM Kích hoạt virtual environment
echo 🔄 Kích hoạt virtual environment...
call venv\Scripts\activate.bat

REM Kiểm tra Python version
echo.
echo 📋 Thông tin Python:
python --version
echo.

REM Kiểm tra các package chính
echo 📦 Kiểm tra các package chính:
python -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)" 2>nul || echo "❌ FastAPI chưa cài đặt"
python -c "import uvicorn; print('✅ Uvicorn:', uvicorn.__version__)" 2>nul || echo "❌ Uvicorn chưa cài đặt"
python -c "import sqlalchemy; print('✅ SQLAlchemy:', sqlalchemy.__version__)" 2>nul || echo "❌ SQLAlchemy chưa cài đặt"
python -c "import pyotp; print('✅ PyOTP: Installed')" 2>nul || echo "❌ PyOTP chưa cài đặt"

echo.
echo ========================================
echo 🎉 Môi trường đã sẵn sàng!
echo.
echo 📖 Các lệnh hữu ích:
echo    python run_app.py --help      # Xem trợ giúp
echo    python run_app.py --setup     # Thiết lập database
echo    python run_app.py --test      # Chạy tests
echo    python run_app.py --reload    # Chạy ở chế độ development
echo    python run_app.py --prod      # Chạy ở chế độ production
echo.
echo 🌐 URL ứng dụng: http://localhost:8000
echo 👤 Admin login: admin@todoapp.com / Admin123!
echo ========================================
echo.