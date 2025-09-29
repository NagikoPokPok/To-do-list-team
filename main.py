"""
Todo List Application
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from app.config import settings
from app.database import Base, engine, ensure_schema
from app.models import *  # noqa: F401,F403 (đảm bảo load models)

# Đảm bảo schema đã được cập nhật cho database hiện có
try:
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    print("✅ Database initialized")
except Exception as e:
    print(f"❌ Database init error: {e}")

# FastAPI app
app = FastAPI(
    title="VTeam",
    description="Simple Todo List Application with OTP Email Authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router
from app.routers.teams import router as teams_router
from app.routers.invitations import router as invitations_router
from app.routers.invitations_user import router as invitations_user_router
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(teams_router)
app.include_router(invitations_router)
app.include_router(invitations_user_router)
print("✅ Routers loaded (auth, tasks, teams, invitations)")

# Route handlers
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": "VTeam"
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "app_name": "VTeam"
    })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page"""
    return templates.TemplateResponse("register.html", {
        "request": request,
        "app_name": "VTeam"
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "app_name": "VTeam"
    })

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Profile page"""
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "app_name": "VTeam"
    })

@app.get("/teams", response_class=HTMLResponse)
async def teams_page(request: Request):
    """Teams page"""
    return templates.TemplateResponse("teams.html", {
        "request": request,
        "app_name": "VTeam"
    })

@app.get("/join-team", response_class=HTMLResponse)
async def join_team_page(request: Request):
    """Join team page"""
    return templates.TemplateResponse("join-team.html", {
        "request": request,
        "app_name": "VTeam"
    })

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """Tasks page"""
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "app_name": "VTeam"
    })

@app.get("/teams/{team_id}", response_class=HTMLResponse)
async def team_detail_page(request: Request, team_id: int):
    """Team detail page with member invitation form"""
    return templates.TemplateResponse("team-detail.html", {
        "request": request,
        "app_name": "VTeam",
        "team_id": team_id
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "todo_list_clean",
        "database": "sqlite",
        "features": [
            "email_registration_with_otp",
            "password_login",
            "password_reset_with_otp",
            "jwt_authentication"
        ]
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 page"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>404 - Page Not Found</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6 text-center">
                    <div class="card">
                        <div class="card-body">
                            <h1>404</h1>
                            <h3>Page Not Found</h3>
                            <p>The page you're looking for doesn't exist.</p>
                            <a href="/" class="btn btn-primary">Go Home</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, status_code=404)

@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    """Custom 500 page"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>500 - Server Error</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6 text-center">
                    <div class="card">
                        <div class="card-body">
                            <h1>500</h1>
                            <h3>Server Error</h3>
                            <p>Something went wrong on our end.</p>
                            <a href="/" class="btn btn-primary">Go Home</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, status_code=500)

if __name__ == "__main__":
    print("Starting Todo List Application...")
    print("Features: OTP Email Registration, Simple Authentication")
    print("URLs:")
    print("App: http://127.0.0.1:8000")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
