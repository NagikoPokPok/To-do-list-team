# Todo List Application với FastAPI và 2FA

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-Database-orange.svg)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Ứng dụng quản lý công việc (Todo List) hiện đại được xây dựng bằng FastAPI với tính năng bảo mật 2FA và quản lý nhóm thông minh.

## 🌟 Tính năng chính

### 🔐 Bảo mật cao cấp
- **Xác thực 2 yếu tố (2FA)** với Google Authenticator
- **OTP qua email** làm phương án dự phòng
- **JWT tokens** với thời gian hết hạn
- **Mã hóa password** bằng bcrypt
- **Backup codes** cho 2FA

### 👥 Quản lý nhóm
- **Team Manager**: Tạo nhóm, mời thành viên, quản lý tất cả công việc
- **Team Member**: Tham gia nhóm, quản lý công việc cá nhân
- **Phân quyền rõ ràng** theo vai trò
- **Gán công việc** cho thành viên trong nhóm

### ✅ Quản lý công việc
- **CRUD operations** đầy đủ cho tasks
- **4 mức độ ưu tiên**: Thấp, Trung bình, Cao, Khẩn cấp
- **Trạng thái công việc**: Đang chờ, Đang thực hiện, Hoàn thành, Đã hủy
- **Hạn hoàn thành** và thông báo quá hạn
- **Lọc và tìm kiếm** nâng cao

### 🎨 Giao diện người dùng
- **Responsive design** hoạt động trên mọi thiết bị
- **Màu chủ đạo đỏ tươi** với các màu bổ trợ hài hòa
- **Bootstrap 5** cho UI components
- **Font Awesome** icons
- **Animations** mượt mà

### 📧 Thông báo email
- **Email chào mừng** khi đăng ký
- **OTP verification** cho 2FA
- **Thông báo gán công việc** mới
- **SMTP support** với Gmail

## 🚀 Demo

### Tài khoản demo
```
Team Manager:
- Email: manager@demo.com  
- Password: demo123

Team Member:
- Email: member@demo.com
- Password: demo123
```

### Screenshots
- **Trang chủ**: Giao diện hiện đại với thông tin tính năng
- **Dashboard**: Thống kê và quản lý công việc trực quan  
- **2FA Setup**: Thiết lập bảo mật dễ dàng
- **Team Management**: Quản lý nhóm và thành viên

## 🛠️ Công nghệ sử dụng

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: SQL toolkit và ORM
- **SQLite**: Lightweight database
- **Pydantic**: Data validation
- **JWT**: Token-based authentication
- **bcrypt**: Password hashing
- **pyotp**: TOTP implementation

### Frontend  
- **Jinja2**: Template engine
- **Bootstrap 5**: CSS framework
- **Font Awesome**: Icon library
- **Vanilla JavaScript**: Frontend logic

### Security & 2FA
- **Google Authenticator** compatible
- **QR Code generation** for easy setup
- **Email OTP** backup method
- **Secure session management**

## 📋 Yêu cầu hệ thống

- Python 3.8+
- pip package manager
- Gmail account (cho email features)
- Modern web browser

## ⚡ Cài đặt nhanh

### 1. Clone repository
```bash
git clone https://github.com/your-username/todo-list-fastapi.git
cd todo-list-fastapi
```

### 2. Tạo virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình environment
```bash
cp .env.example .env
# Chỉnh sửa .env với thông tin của bạn
```

### 5. Chạy ứng dụng
```bash
python main.py
```

### 6. Truy cập ứng dụng
- **App**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📖 Hướng dẫn chi tiết

Xem file [Hướng dẫn cài thư viện.md](Hướng%20dẫn%20cài%20thư%20viện.md) để có hướng dẫn chi tiết về:
- Cài đặt từng bước
- Cấu hình email Gmail
- Thiết lập 2FA
- Deployment production
- Troubleshooting

## 🏗️ Cấu trúc dự án

```
todo_app/
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── routers/         # API endpoints  
│   ├── services/        # Business logic
│   ├── middleware/      # Authentication
│   ├── utils/          # Helper functions
│   ├── config.py       # App configuration
│   ├── database.py     # Database setup
│   └── schemas.py      # Pydantic schemas
├── static/             # CSS, JS, images
├── templates/          # HTML templates
├── main.py            # Application entry point
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

## 🔧 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Đăng ký tài khoản
- `POST /api/v1/auth/login` - Đăng nhập
- `POST /api/v1/auth/enable-2fa` - Bật 2FA
- `POST /api/v1/auth/verify-2fa` - Xác thực 2FA
- `GET /api/v1/auth/me` - Lấy thông tin user

### Tasks
- `GET /api/v1/tasks/` - Lấy danh sách tasks
- `POST /api/v1/tasks/` - Tạo task mới
- `GET /api/v1/tasks/{id}` - Lấy chi tiết task
- `PUT /api/v1/tasks/{id}` - Cập nhật task
- `DELETE /api/v1/tasks/{id}` - Xóa task

### Teams
- `GET /api/v1/teams/` - Lấy danh sách teams
- `POST /api/v1/teams/` - Tạo team mới
- `GET /api/v1/teams/{id}` - Lấy chi tiết team
- `POST /api/v1/teams/{id}/members/{user_id}` - Thêm member
- `DELETE /api/v1/teams/{id}/members/{user_id}` - Xóa member

## 🔒 Bảo mật

### Các biện pháp bảo mật được áp dụng:
- ✅ Password hashing với bcrypt
- ✅ JWT tokens với expiration
- ✅ 2FA với TOTP/Google Authenticator  
- ✅ Email OTP backup
- ✅ Input validation với Pydantic
- ✅ SQL injection protection với SQLAlchemy
- ✅ CORS configuration
- ✅ Rate limiting (có thể thêm)

### Thiết lập 2FA:
1. Đăng nhập vào tài khoản
2. Vào trang Profile/Settings
3. Nhấn "Bật 2FA"
4. Quét QR code bằng Google Authenticator
5. Nhập mã 6 số để xác thực
6. Lưu backup codes an toàn

## 🌍 Tương thích

- ✅ Windows 10/11
- ✅ macOS 10.15+
- ✅ Ubuntu 18.04+
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile responsive

## 🚀 Deployment

### Docker (Recommended)
```bash
# Build image
docker build -t todo-app .

# Run container
docker run -p 8000:8000 todo-app
```

### Traditional Deployment
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Environment Variables for Production
```env
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-super-secure-secret-key
DATABASE_URL=postgresql://user:pass@host:port/dbname
SMTP_USERNAME=your-production-email
SMTP_PASSWORD=your-app-password
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py
```

## 📈 Performance

- **Response time**: < 100ms cho các API calls
- **Database queries**: Optimized với SQLAlchemy
- **Caching**: Redis có thể được thêm vào
- **File serving**: Static files được serve hiệu quả

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📝 License

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm thông tin.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Amazing Python framework
- [Bootstrap](https://getbootstrap.com/) - UI components
- [Font Awesome](https://fontawesome.com/) - Beautiful icons
- [Google Authenticator](https://support.google.com/accounts/answer/1066447) - 2FA standard

## 📞 Liên hệ

- **Author**: Todo List Team
- **Email**: support@todoapp.com
- **GitHub**: [@your-username](https://github.com/your-username)
- **Website**: https://todo-app-demo.com

## 🔗 Tham khảo và tài liệu

### Các dự án GitHub tương tự:
1. **FastAPI Todo App**: https://github.com/tiangolo/fastapi/tree/master/docs/en/docs/tutorial
2. **FastAPI Users**: https://github.com/fastapi-users/fastapi-users
3. **FastAPI Security**: https://github.com/jacobsvante/fastapi-security
4. **SQLAlchemy Tutorial**: https://docs.sqlalchemy.org/en/14/tutorial/

### Documentation:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [JWT Documentation](https://pyjwt.readthedocs.io/)

### 2FA Resources:
- [Google Authenticator](https://support.google.com/accounts/answer/1066447)
- [TOTP RFC 6238](https://tools.ietf.org/html/rfc6238)
- [pyotp Documentation](https://pyotp.readthedocs.io/)

---

⭐ **Nếu bạn thấy dự án này hữu ích, hãy cho một star nhé!** ⭐