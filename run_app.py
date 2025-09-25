#!/usr/bin/env python3
"""
Todo App Launcher
=================

Script khởi chạy ứng dụng Todo List FastAPI với các tùy chọn cấu hình.

Usage:
    python run_app.py [options]

Options:
    --host HOST     Host address (default: 127.0.0.1)
    --port PORT     Port number (default: 8000)
    --reload        Enable auto-reload for development
    --debug         Enable debug mode
    --test          Run tests before starting server
    --setup         Setup database and create sample data
    --prod          Production mode (disable debug, auto-reload)

Examples:
    python run_app.py                    # Start with default settings
    python run_app.py --reload --debug   # Development mode
    python run_app.py --prod             # Production mode
    python run_app.py --test             # Run tests first
    python run_app.py --setup            # Setup database

Author: Todo App Team
Created: 2024
"""

import os
import sys
import argparse
import asyncio
import webbrowser
from pathlib import Path
from datetime import datetime

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

try:
    import uvicorn
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    # Import our app modules
    from main import app
    from app.database import engine, SessionLocal
    from app.models import Base
    from app.models.user import User
    from app.models.team import Team
    from app.models.task import Task, TaskStatus, TaskPriority
    from app.services.auth_service import AuthService
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📦 Please install required packages using:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

class TodoAppLauncher:
    """Lớp khởi chạy ứng dụng Todo"""
    
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 8000
        self.reload = False
        self.debug = False
        self.production = False
        
    def print_banner(self):
        """In banner ứng dụng"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🚀 TODO LIST APPLICATION                  ║
║                                                              ║
║  FastAPI + SQLite + Bootstrap 5 + 2FA Authentication        ║
║  Team Management + Task Tracking + Responsive UI            ║
║                                                              ║
║  Developed with ❤️  by Todo App Team                         ║
║  Version: 1.0.0 | Python 3.12+ | FastAPI 0.104.1           ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def check_requirements(self):
        """Kiểm tra các yêu cầu hệ thống"""
        print("🔍 Checking system requirements...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            print("❌ Python 3.8+ is required")
            return False
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check required files
        required_files = [
            "main.py",
            "app/models/user.py",
            "app/models/team.py", 
            "app/models/task.py",
            "requirements.txt",
            "static/css/main.css",
            "templates/base.html"
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                print(f"❌ Missing required file: {file_path}")
                return False
        print("✅ All required files present")
        
        # Check database
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            print("💡 Try running with --setup to initialize database")
            return False
        
        return True
    
    async def setup_database(self):
        """Thiết lập database và dữ liệu mẫu"""
        print("🔧 Setting up database...")
        
        try:
            # Create all tables
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created")
            
            # Create sample data
            await self.create_sample_data()
            print("✅ Sample data created")
            
            return True
            
        except Exception as e:
            print(f"❌ Database setup failed: {str(e)}")
            return False
    
    async def create_sample_data(self):
        """Tạo dữ liệu mẫu"""
        print("📝 Creating sample data...")
        
        db = SessionLocal()
        try:
            # Check if admin user exists
            admin_user = db.query(User).filter(User.email == "admin@todoapp.com").first()
            
            if not admin_user:
                # Create admin user
                auth_service = AuthService()
                hashed_password = auth_service.get_password_hash("Admin123!")
                
                admin_user = User(
                    username="admin",
                    email="admin@todoapp.com",
                    full_name="Administrator",
                    hashed_password=hashed_password,
                    role="team_manager",
                    is_active=True
                )
                
                db.add(admin_user)
                db.commit()
                db.refresh(admin_user)
                print("✅ Admin user created (admin@todoapp.com / Admin123!)")
            
            # Check if sample team exists
            sample_team = db.query(Team).filter(Team.name == "Sample Team").first()
            
            if not sample_team:
                sample_team = Team(
                    name="Sample Team",
                    description="This is a sample team for demonstration purposes",
                    manager_id=admin_user.id,
                    max_members=10
                )
                
                db.add(sample_team)
                db.commit()
                db.refresh(sample_team)
                print("✅ Sample team created")
            
            # Check if sample tasks exist
            sample_task_count = db.query(Task).filter(Task.title.like("Sample Task%")).count()
            
            if sample_task_count == 0:
                sample_tasks = [
                    Task(
                        title="Sample Task 1: Setup Development Environment",
                        description="Install Python, FastAPI, and required dependencies",
                        priority=TaskPriority.HIGH,
                        status=TaskStatus.COMPLETED,
                        creator_id=admin_user.id,
                        team_id=sample_team.id
                    ),
                    Task(
                        title="Sample Task 2: Implement User Authentication",
                        description="Create login, register, and 2FA functionality",
                        priority=TaskPriority.HIGH,
                        status=TaskStatus.COMPLETED,
                        creator_id=admin_user.id,
                        team_id=sample_team.id
                    ),
                    Task(
                        title="Sample Task 3: Design User Interface",
                        description="Create responsive UI with Bootstrap 5 and bright red theme",
                        priority=TaskPriority.MEDIUM,
                        status=TaskStatus.IN_PROGRESS,
                        creator_id=admin_user.id,
                        team_id=sample_team.id
                    ),
                    Task(
                        title="Sample Task 4: Test Application",
                        description="Write and run comprehensive tests for all features",
                        priority=TaskPriority.MEDIUM,
                        status=TaskStatus.PENDING,
                        creator_id=admin_user.id,
                        team_id=sample_team.id
                    ),
                    Task(
                        title="Sample Task 5: Deploy to Production",
                        description="Deploy application to production server",
                        priority=TaskPriority.LOW,
                        status=TaskStatus.PENDING,
                        creator_id=admin_user.id,
                        team_id=sample_team.id
                    )
                ]
                
                for task in sample_tasks:
                    db.add(task)
                
                db.commit()
                print(f"✅ {len(sample_tasks)} sample tasks created")
        
        finally:
            db.close()
    
    async def run_tests(self):
        """Chạy tests"""
        print("🧪 Running application tests...")
        
        try:
            from test_app import TodoAppTester
            tester = TodoAppTester()
            success = await tester.run_all_tests()
            
            if success:
                print("✅ All tests passed!")
                return True
            else:
                print("❌ Some tests failed!")
                return False
                
        except ImportError:
            print("⚠️  Test module not found, skipping tests")
            return True
        except Exception as e:
            print(f"❌ Test error: {str(e)}")
            return False
    
    def start_server(self):
        """Khởi động server"""
        print(f"🚀 Starting Todo App server...")
        print(f"📡 Host: {self.host}")
        print(f"🔌 Port: {self.port}")
        print(f"🔄 Reload: {'Enabled' if self.reload else 'Disabled'}")
        print(f"🐛 Debug: {'Enabled' if self.debug else 'Disabled'}")
        print(f"🏭 Production: {'Yes' if self.production else 'No'}")
        
        # Server URL
        server_url = f"http://{self.host}:{self.port}"
        
        print(f"\n{'='*60}")
        print(f"🌐 Server will be available at: {server_url}")
        print(f"📊 API Documentation: {server_url}/docs")
        print(f"🔍 Interactive API: {server_url}/redoc")
        print(f"📋 Admin Login: admin@todoapp.com / Admin123!")
        print(f"{'='*60}")
        
        # Open browser in development mode
        if not self.production and self.host in ['127.0.0.1', 'localhost']:
            try:
                webbrowser.open(server_url)
                print("🌐 Opening browser...")
            except:
                print("⚠️  Could not open browser automatically")
        
        # Configure uvicorn settings
        config = uvicorn.Config(
            app="main:app",
            host=self.host,
            port=self.port,
            reload=self.reload,
            log_level="debug" if self.debug else "info",
            access_log=not self.production
        )
        
        server = uvicorn.Server(config)
        
        try:
            print(f"\n⏰ Server started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("Press Ctrl+C to stop the server\n")
            
            server.run()
            
        except KeyboardInterrupt:
            print(f"\n⏹️  Server stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("👋 Thank you for using Todo App!")
        
        except Exception as e:
            print(f"\n💥 Server error: {str(e)}")
            sys.exit(1)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Todo List FastAPI Application Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Start with default settings
  %(prog)s --host 0.0.0.0 --port 80 Start on all interfaces, port 80
  %(prog)s --reload --debug         Development mode with auto-reload
  %(prog)s --prod                   Production mode
  %(prog)s --test                   Run tests before starting
  %(prog)s --setup                  Setup database and sample data
        """)
    
    parser.add_argument("--host", 
                       default="127.0.0.1",
                       help="Host address (default: 127.0.0.1)")
    
    parser.add_argument("--port", 
                       type=int, 
                       default=8000,
                       help="Port number (default: 8000)")
    
    parser.add_argument("--reload", 
                       action="store_true",
                       help="Enable auto-reload for development")
    
    parser.add_argument("--debug", 
                       action="store_true",
                       help="Enable debug mode")
    
    parser.add_argument("--test", 
                       action="store_true",
                       help="Run tests before starting server")
    
    parser.add_argument("--setup", 
                       action="store_true",
                       help="Setup database and create sample data")
    
    parser.add_argument("--prod", 
                       action="store_true",
                       help="Production mode (disable debug, auto-reload)")
    
    return parser.parse_args()

async def main():
    """Hàm chính"""
    args = parse_arguments()
    launcher = TodoAppLauncher()
    
    # Display banner
    launcher.print_banner()
    
    # Configure launcher
    launcher.host = args.host
    launcher.port = args.port
    launcher.reload = args.reload and not args.prod
    launcher.debug = args.debug and not args.prod
    launcher.production = args.prod
    
    # Check requirements
    if not launcher.check_requirements():
        print("\n❌ System requirements not met!")
        sys.exit(1)
    
    # Setup database if requested
    if args.setup:
        if not await launcher.setup_database():
            print("\n❌ Database setup failed!")
            sys.exit(1)
        print("\n✅ Database setup completed!")
    
    # Run tests if requested
    if args.test:
        if not await launcher.run_tests():
            print("\n❌ Tests failed!")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
    
    # Start server
    launcher.start_server()

if __name__ == "__main__":
    try:
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we get here, we're in a running loop, so create a new task
            task = loop.create_task(main())
            loop.run_until_complete(task)
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)