#!/usr/bin/env python3
"""
Todo App Testing Script
========================

Script để kiểm tra tính năng của ứng dụng Todo List FastAPI
với 2FA authentication, team management và responsive UI.

Chạy script này để kiểm tra:
- Database connection và models
- Authentication system
- 2FA functionality
- Team management
- Task CRUD operations
- Email service
- API endpoints

Author: Todo App Team
Created: 2024
"""

import os
import sys
import asyncio
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

try:
    import uvicorn
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    # Import our app modules
    from app.main import app
    from app.database import get_db, engine
    from app.models.user import User
    from app.models.team import Team
    from app.models.task import Task
    from app.services.auth_service import AuthService
    from app.services.email_service import EmailService
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📦 Please install required packages using: pip install -r requirements.txt")
    sys.exit(1)

class TodoAppTester:
    """Lớp kiểm tra tổng thể ứng dụng Todo"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.base_url = "http://localhost:8000"
        self.test_user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
        self.test_team_data = {
            "name": "Test Team",
            "description": "Team for testing purposes",
            "is_private": False,
            "max_members": 10
        }
        self.test_task_data = {
            "title": "Test Task",
            "description": "Task for testing purposes",
            "priority": "medium",
            "status": "pending"
        }
        self.auth_token = None
        self.user_id = None
        self.team_id = None
        self.task_id = None
        
    def print_header(self, title):
        """In header cho từng phần kiểm tra"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_step(self, step, description):
        """In từng bước kiểm tra"""
        print(f"\n{step}. {description}")
        print("-" * 40)
    
    def print_result(self, success, message):
        """In kết quả kiểm tra"""
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        
    async def test_database_connection(self):
        """Kiểm tra kết nối database"""
        self.print_header("KIỂM TRA DATABASE")
        
        try:
            # Test database connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                self.print_result(True, "Database connection successful")
                
            # Test models
            db = next(get_db())
            user_count = db.query(User).count()
            team_count = db.query(Team).count()
            task_count = db.query(Task).count()
            
            print(f"📊 Database Statistics:")
            print(f"   - Users: {user_count}")
            print(f"   - Teams: {team_count}")
            print(f"   - Tasks: {task_count}")
            
            self.print_result(True, "Database models working correctly")
            
        except Exception as e:
            self.print_result(False, f"Database error: {str(e)}")
            return False
            
        return True
    
    def test_user_registration(self):
        """Kiểm tra đăng ký người dùng"""
        self.print_step(1, "Testing User Registration")
        
        try:
            response = self.client.post("/auth/register", json=self.test_user_data)
            
            if response.status_code == 201:
                data = response.json()
                self.user_id = data.get("id")
                self.print_result(True, f"User registered successfully (ID: {self.user_id})")
                return True
            elif response.status_code == 400 and "already exists" in response.json().get("detail", ""):
                self.print_result(True, "User already exists (expected for repeated tests)")
                return True
            else:
                self.print_result(False, f"Registration failed: {response.json()}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Registration error: {str(e)}")
            return False
    
    def test_user_login(self):
        """Kiểm tra đăng nhập người dùng"""
        self.print_step(2, "Testing User Login")
        
        try:
            login_data = {
                "username": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
            
            response = self.client.post("/auth/login", data=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.print_result(True, "Login successful")
                
                # Test authentication header
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                me_response = self.client.get("/auth/me", headers=headers)
                
                if me_response.status_code == 200:
                    user_data = me_response.json()
                    self.user_id = user_data.get("id")
                    self.print_result(True, f"Authentication working (User: {user_data.get('username')})")
                    return True
                else:
                    self.print_result(False, "Authentication header test failed")
                    return False
                    
            else:
                self.print_result(False, f"Login failed: {response.json()}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Login error: {str(e)}")
            return False
    
    def test_2fa_setup(self):
        """Kiểm tra thiết lập 2FA"""
        self.print_step(3, "Testing 2FA Setup")
        
        if not self.auth_token:
            self.print_result(False, "No authentication token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test 2FA enable endpoint
            response = self.client.post("/auth/2fa/enable", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "qr_code" in data and "backup_codes" in data:
                    self.print_result(True, "2FA setup endpoint working")
                    self.print_result(True, f"Generated {len(data['backup_codes'])} backup codes")
                    return True
                else:
                    self.print_result(False, "2FA response missing required data")
                    return False
            else:
                self.print_result(False, f"2FA enable failed: {response.json()}")
                return False
                
        except Exception as e:
            self.print_result(False, f"2FA error: {str(e)}")
            return False
    
    def test_team_operations(self):
        """Kiểm tra các thao tác với team"""
        self.print_step(4, "Testing Team Operations")
        
        if not self.auth_token:
            self.print_result(False, "No authentication token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test create team
            response = self.client.post("/teams/", json=self.test_team_data, headers=headers)
            
            if response.status_code == 201:
                team_data = response.json()
                self.team_id = team_data.get("id")
                self.print_result(True, f"Team created successfully (ID: {self.team_id})")
            else:
                self.print_result(False, f"Team creation failed: {response.json()}")
                return False
            
            # Test get teams
            response = self.client.get("/teams/", headers=headers)
            if response.status_code == 200:
                teams = response.json()
                self.print_result(True, f"Retrieved {len(teams)} teams")
            else:
                self.print_result(False, "Failed to get teams")
                return False
            
            # Test get team members
            if self.team_id:
                response = self.client.get(f"/teams/{self.team_id}/members", headers=headers)
                if response.status_code == 200:
                    members = response.json()
                    self.print_result(True, f"Team has {len(members)} members")
                else:
                    self.print_result(False, "Failed to get team members")
            
            return True
            
        except Exception as e:
            self.print_result(False, f"Team operations error: {str(e)}")
            return False
    
    def test_task_operations(self):
        """Kiểm tra các thao tác với task"""
        self.print_step(5, "Testing Task Operations")
        
        if not self.auth_token:
            self.print_result(False, "No authentication token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Add team_id to task data if available
            task_data = self.test_task_data.copy()
            if self.team_id:
                task_data["team_id"] = self.team_id
            
            # Test create task
            response = self.client.post("/tasks/", json=task_data, headers=headers)
            
            if response.status_code == 201:
                task_response = response.json()
                self.task_id = task_response.get("id")
                self.print_result(True, f"Task created successfully (ID: {self.task_id})")
            else:
                self.print_result(False, f"Task creation failed: {response.json()}")
                return False
            
            # Test get tasks
            response = self.client.get("/tasks/", headers=headers)
            if response.status_code == 200:
                tasks = response.json()
                self.print_result(True, f"Retrieved {len(tasks)} tasks")
            else:
                self.print_result(False, "Failed to get tasks")
                return False
            
            # Test update task
            if self.task_id:
                update_data = {"status": "in_progress", "priority": "high"}
                response = self.client.put(f"/tasks/{self.task_id}", json=update_data, headers=headers)
                if response.status_code == 200:
                    self.print_result(True, "Task updated successfully")
                else:
                    self.print_result(False, "Failed to update task")
            
            return True
            
        except Exception as e:
            self.print_result(False, f"Task operations error: {str(e)}")
            return False
    
    def test_api_endpoints(self):
        """Kiểm tra các API endpoints chính"""
        self.print_step(6, "Testing API Endpoints")
        
        endpoints_to_test = [
            ("GET", "/", 200),
            ("GET", "/health", 200),
            ("GET", "/login", 200),
            ("GET", "/register", 200),
            ("GET", "/dashboard", 200),  # Should redirect if not authenticated
        ]
        
        success_count = 0
        total_count = len(endpoints_to_test)
        
        for method, endpoint, expected_status in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.client.get(endpoint)
                elif method == "POST":
                    response = self.client.post(endpoint)
                else:
                    continue
                
                if response.status_code == expected_status or response.status_code in [200, 302]:
                    self.print_result(True, f"{method} {endpoint} - Status: {response.status_code}")
                    success_count += 1
                else:
                    self.print_result(False, f"{method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}")
            
            except Exception as e:
                self.print_result(False, f"{method} {endpoint} - Error: {str(e)}")
        
        self.print_result(success_count == total_count, f"API Endpoints: {success_count}/{total_count} passed")
        return success_count == total_count
    
    def test_email_service(self):
        """Kiểm tra email service"""
        self.print_step(7, "Testing Email Service")
        
        try:
            # Test email service initialization
            email_service = EmailService()
            self.print_result(True, "Email service initialized")
            
            # Note: We won't actually send emails in tests
            # But we can test the email formatting
            welcome_content = email_service._format_welcome_email("Test User", "test@example.com")
            if "Test User" in welcome_content and "test@example.com" in welcome_content:
                self.print_result(True, "Email formatting working")
            else:
                self.print_result(False, "Email formatting failed")
                return False
            
            return True
            
        except Exception as e:
            self.print_result(False, f"Email service error: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Dọn dẹp dữ liệu test"""
        self.print_step(8, "Cleaning Up Test Data")
        
        if not self.auth_token:
            self.print_result(False, "No authentication token for cleanup")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Delete test task
            if self.task_id:
                response = self.client.delete(f"/tasks/{self.task_id}", headers=headers)
                if response.status_code == 204:
                    self.print_result(True, "Test task deleted")
                else:
                    self.print_result(False, f"Failed to delete task: {response.status_code}")
            
            # Delete test team
            if self.team_id:
                response = self.client.delete(f"/teams/{self.team_id}", headers=headers)
                if response.status_code == 204:
                    self.print_result(True, "Test team deleted")
                else:
                    self.print_result(False, f"Failed to delete team: {response.status_code}")
            
            # Note: User deletion not implemented for safety
            self.print_result(True, "Cleanup completed (user kept for future tests)")
            
        except Exception as e:
            self.print_result(False, f"Cleanup error: {str(e)}")
    
    async def run_all_tests(self):
        """Chạy tất cả các test"""
        print("🚀 Starting Todo App Tests")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        test_results = []
        
        # Database tests
        test_results.append(await self.test_database_connection())
        
        # Authentication tests
        self.print_header("KIỂM TRA AUTHENTICATION")
        test_results.append(self.test_user_registration())
        test_results.append(self.test_user_login())
        test_results.append(self.test_2fa_setup())
        
        # Feature tests
        self.print_header("KIỂM TRA FEATURES")
        test_results.append(self.test_team_operations())
        test_results.append(self.test_task_operations())
        
        # API tests
        self.print_header("KIỂM TRA API ENDPOINTS")
        test_results.append(self.test_api_endpoints())
        
        # Service tests
        self.print_header("KIỂM TRA SERVICES")
        test_results.append(self.test_email_service())
        
        # Cleanup
        self.print_header("DỌN DẸP")
        self.cleanup_test_data()
        
        # Summary
        self.print_header("TÓM TẮT KẾT QUẢ")
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📊 Test Results:")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {total_tests - passed_tests}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"\n🎉 Great! Your Todo App is working well!")
            print(f"💡 You can now run: python -m uvicorn app.main:app --reload")
        else:
            print(f"\n⚠️  Some tests failed. Please check the errors above.")
            print(f"🔧 Fix the issues and run tests again.")
        
        return success_rate >= 80

def main():
    """Hàm chính để chạy tests"""
    print("Todo App Test Suite")
    print("==================")
    
    # Check if we're in the right directory
    if not os.path.exists("app") or not os.path.exists("requirements.txt"):
        print("❌ Please run this script from the todo_app directory")
        print("📁 Current directory should contain 'app' folder and 'requirements.txt'")
        sys.exit(1)
    
    # Run tests
    tester = TodoAppTester()
    
    try:
        success = asyncio.run(tester.run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()