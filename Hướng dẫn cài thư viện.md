# Hướng dẫn cài đặt thư viện - Todo List Application

## Giới thiệu
Đây là hướng dẫn chi tiết để cài đặt và chạy ứng dụng Todo List được xây dựng bằng FastAPI với các tính năng:
- Xác thực 2 yếu tố (2FA) với Google Authenticator và OTP qua email
- Quản lý nhóm với phân quyền Team Manager và Team Member
- Giao diện responsive với màu chủ đạo đỏ tươi
- Cơ sở dữ liệu SQLite

## Yêu cầu hệ thống
- Python 3.8 hoặc cao hơn
- pip (Python package installer)
- Git (để clone repository)

## Bước 1: Chuẩn bị môi trường

<!-- ### 1.1. Tạo thư mục dự án
```bash
mkdir todo-list-app
cd todo-list-app
``` -->

### 1.2. Tạo virtual environment
```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Trên Windows:
venv\Scripts\activate

# Trên macOS/Linux:
source venv/bin/activate
```

### 1.3. Cập nhật pip
```bash
python -m pip install --upgrade pip
```

## Bước 2: Cài đặt thư viện

### 2.1. Cài đặt từ requirements.txt
```bash
pip install -r requirements.txt
```

## Bước 3: Cấu hình ứng dụng

### 3.1. Tạo file .env
Tạo file `.env` trong thư mục gốc của dự án với nội dung:

```env
# Cấu hình ứng dụng
APP_NAME="Todo List Application"
SECRET_KEY="your-super-secret-key-change-this-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cấu hình cơ sở dữ liệu SQLite
DATABASE_URL="sqlite:///./todo_app.db"

# Cấu hình Email (cho 2FA)
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
EMAIL_FROM="your-email@gmail.com"

# Cấu hình 2FA
TOTP_SECRET_KEY="your-totp-secret-key"

# Cấu hình môi trường
ENVIRONMENT="development"
DEBUG=True
```

### 3.2. Cấu hình Email (Gmail)
Để sử dụng Gmail cho việc gửi OTP:

1. Đăng nhập vào tài khoản Gmail
2. Bật xác thực 2 bước
3. Tạo App Password:
   - Vào Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Chọn "Mail" và thiết bị của bạn
   - Copy mật khẩu ứng dụng vào `SMTP_PASSWORD`

### 3.3. Tạo secret key mạnh
```python
import secrets
print(secrets.token_urlsafe(32))
```

## Bước 4: Chạy ứng dụng

### 4.1. Khởi tạo cơ sở dữ liệu
```bash
# Cơ sở dữ liệu sẽ được tạo tự động khi chạy ứng dung lần đầu
```

### 4.2. Chạy development server
```bash
# Chạy server
python main.py

# Hoặc sử dụng uvicorn trực tiếp
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4.3. Truy cập ứng dụng
- **Ứng dụng chính**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Bước 5: Tạo tài khoản đầu tiên

### 5.1. Đăng ký Team Manager
1. Truy cập http://localhost:8000/register
2. Điền thông tin và chọn role "Team Manager"
3. Đăng ký tài khoản

### 5.2. Bật 2FA (khuyến khích)
1. Đăng nhập vào tài khoản
2. Vào trang Profile
3. Bật 2FA và quét QR code bằng Google Authenticator

## Bước 6: Kiểm tra cài đặt

### 6.1. Chạy tests (nếu có)
```bash
pytest
```

### 6.2. Kiểm tra health endpoint
```bash
curl http://localhost:8000/health
```

## Troubleshooting - Xử lý lỗi thường gặp

### Lỗi import modules
```bash
# Đảm bảo virtual environment được kích hoạt
venv\Scripts\activate

# Cài đặt lại requirements
pip install -r requirements.txt
```

### Lỗi SQLite database
```bash
# Xóa database cũ và tạo lại
rm todo_app.db
python main.py
```

### Lỗi email configuration
- Kiểm tra SMTP settings trong .env
- Đảm bảo App Password được tạo đúng cách
- Kiểm tra firewall/antivirus không chặn SMTP

### Lỗi 2FA QR code
- Kiểm tra thư viện qrcode đã được cài đặt
- Đảm bảo TOTP_SECRET_KEY được cấu hình

## Deployment - Triển khai production

### 1. Sử dụng Gunicorn
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 2. Cấu hình Nginx (optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Cấu hình production
- Thay đổi SECRET_KEY
- Đặt DEBUG=False
- Sử dụng HTTPS
- Cấu hình proper database (PostgreSQL/MySQL)

## Cấu trúc dự án
```
todo_app/
├── app/
│   ├── __init__.py
│   ├── config.py              # Cấu hình ứng dụng
│   ├── database.py            # Kết nối database
│   ├── schemas.py             # Pydantic schemas
│   ├── models/                # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── task.py
│   │   └── team.py
│   ├── routers/               # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── tasks.py
│   │   └── teams.py
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   └── email_service.py
│   ├── middleware/            # Authentication middleware
│   │   ├── __init__.py
│   │   └── auth.py
│   └── utils/                 # Utilities
│       ├── __init__.py
│       └── auth.py
├── static/                    # Static files
│   ├── css/
│   │   └── main.css
│   └── js/
│       └── main.js
├── templates/                 # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── dashboard.html
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── .env                      # Environment variables
├── .gitignore               # Git ignore file
└── README.md                # Documentation
```

## Liên hệ và hỗ trợ
- Email: support@todoapp.com
- Documentation: Xem thêm trong README.md
- Issues: Tạo issue trên GitHub repository

## Cập nhật thư viện
```bash
# Kiểm tra phiên bản hiện tại
pip list

# Cập nhật thư viện
pip install --upgrade package_name

# Hoặc cập nhật tất cả
pip freeze > requirements.txt
pip install -r requirements.txt --upgrade
```