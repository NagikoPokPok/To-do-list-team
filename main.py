"""
Main FastAPI Application - Todo List với 2FA và quản lý teams
Ứng dụng quản lý công việc với xác thực 2 yếu tố và phân quyền team manager/member
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import os

from app.config import settings
from app.database import engine, Base
from app.routers import auth, tasks, teams

# Tạo tất cả tables trong database
Base.metadata.create_all(bind=engine)

# Khởi tạo FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Ứng dụng Todo List với FastAPI, SQLite và 2FA",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cấu hình templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Trang chủ ứng dụng Todo List
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": settings.app_name
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Trang đăng nhập
    """
    return templates.TemplateResponse("login.html", {
        "request": request,
        "app_name": settings.app_name
    })


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Trang đăng ký
    """
    return templates.TemplateResponse("register.html", {
        "request": request,
        "app_name": settings.app_name
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Trang dashboard chính
    """
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "app_name": settings.app_name
    })


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """
    Trang quản lý tasks
    """
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "app_name": settings.app_name
    })


@app.get("/teams", response_class=HTMLResponse)
async def teams_page(request: Request):
    """
    Trang quản lý teams
    """
    return templates.TemplateResponse("teams.html", {
        "request": request,
        "app_name": settings.app_name
    })


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """
    Trang profile và cài đặt 2FA
    """
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "app_name": settings.app_name
    })


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.environment
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """
    Custom 404 handler
    """
    return templates.TemplateResponse("404.html", {
        "request": request,
        "app_name": settings.app_name
    }, status_code=404)


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """
    Custom 500 handler
    """
    return templates.TemplateResponse("500.html", {
        "request": request,
        "app_name": settings.app_name
    }, status_code=500)


if __name__ == "__main__":
    # Chạy ứng dụng với uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )