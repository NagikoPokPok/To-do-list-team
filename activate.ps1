# ============================================
# Todo App Virtual Environment Activation Script (PowerShell)
# ============================================
# Script để kích hoạt môi trường ảo và kiểm tra cài đặt

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    🚀 TODO APP ENVIRONMENT SETUP" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kiểm tra xem virtual environment có tồn tại không
if (!(Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment không tồn tại!" -ForegroundColor Red
    Write-Host "📝 Hãy chạy: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Nhấn Enter để thoát"
    exit 1
}

# Kích hoạt virtual environment
Write-Host "🔄 Kích hoạt virtual environment..." -ForegroundColor Green
try {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "✅ Virtual environment đã được kích hoạt!" -ForegroundColor Green
} catch {
    Write-Host "❌ Không thể kích hoạt virtual environment!" -ForegroundColor Red
    Write-Host "💡 Thử chạy: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Read-Host "Nhấn Enter để thoát"
    exit 1
}

# Kiểm tra Python version
Write-Host ""
Write-Host "📋 Thông tin Python:" -ForegroundColor Magenta
& python --version
Write-Host ""

# Kiểm tra các package chính
Write-Host "📦 Kiểm tra các package chính:" -ForegroundColor Magenta

$packages = @(
    @{ Name = "FastAPI"; Import = "fastapi"; Version = $true },
    @{ Name = "Uvicorn"; Import = "uvicorn"; Version = $true },
    @{ Name = "SQLAlchemy"; Import = "sqlalchemy"; Version = $true },
    @{ Name = "PyOTP"; Import = "pyotp"; Version = $false },
    @{ Name = "QRCode"; Import = "qrcode"; Version = $false },
    @{ Name = "Bcrypt"; Import = "bcrypt"; Version = $false },
    @{ Name = "Jinja2"; Import = "jinja2"; Version = $true }
)

foreach ($package in $packages) {
    try {
        if ($package.Version) {
            $result = & python -c "import $($package.Import); print('$($package.Name):', $($package.Import).__version__)" 2>$null
            Write-Host "✅ $result" -ForegroundColor Green
        } else {
            $null = & python -c "import $($package.Import)" 2>$null
            Write-Host "✅ $($package.Name): Installed" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ $($package.Name) chưa cài đặt" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎉 Môi trường đã sẵn sàng!" -ForegroundColor Yellow
Write-Host ""
Write-Host "📖 Các lệnh hữu ích:" -ForegroundColor Magenta
Write-Host "   python run_app.py --help      # Xem trợ giúp" -ForegroundColor White
Write-Host "   python run_app.py --setup     # Thiết lập database" -ForegroundColor White
Write-Host "   python run_app.py --test      # Chạy tests" -ForegroundColor White
Write-Host "   python run_app.py --reload    # Chạy ở chế độ development" -ForegroundColor White
Write-Host "   python run_app.py --prod      # Chạy ở chế độ production" -ForegroundColor White
Write-Host ""
Write-Host "🌐 URL ứng dụng: http://localhost:8000" -ForegroundColor Cyan
Write-Host "👤 Admin login: admin@todoapp.com / Admin123!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""