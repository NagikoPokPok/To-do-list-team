"""
Test Registration Flow
======================

Test script để kiểm tra flow đăng ký người dùng mới với OTP verification
"""

import asyncio
import aiohttp
import json
from datetime import datetime


class RegistrationTester:
    """Class test registration flow"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def test_registration_flow(self):
        """Test complete registration flow"""
        print("🧪 Testing Registration Flow")
        print("=" * 50)
        
        # Test data
        test_user = {
            "email": "testuser@example.com",
            "username": "testuser123",
            "password": "testpassword123",
            "full_name": "Test User",
            "phone_number": "+84123456789"
        }
        
        # Step 1: Register new user
        print("\n📝 Step 1: Registering new user...")
        register_response = await self.register_user(test_user)
        
        if register_response["success"]:
            print("✅ Registration successful!")
            print(f"   Message: {register_response['message']}")
        else:
            print("❌ Registration failed!")
            print(f"   Error: {register_response['error']}")
            return
        
        # Step 2: Test health check
        print("\n🏥 Step 2: Testing auth health check...")
        health_response = await self.test_health_check()
        
        if health_response["success"]:
            print("✅ Health check passed!")
            print(f"   Features: {', '.join(health_response['data']['features'])}")
        else:
            print("❌ Health check failed!")
        
        # Step 3: Simulate OTP verification (manual step)
        print("\n📧 Step 3: OTP Verification")
        print("⚠️  Manual step required:")
        print("   1. Check the email sent to:", test_user["email"])
        print("   2. Copy the 6-digit OTP code")
        print("   3. Use POST /api/v1/auth/verify-email with:")
        print(f"      {{ \"email\": \"{test_user['email']}\", \"otp_code\": \"XXXXXX\" }}")
        
        # Step 4: Test resend OTP
        print("\n🔄 Step 4: Testing resend OTP...")
        resend_response = await self.resend_otp(test_user["email"])
        
        if resend_response["success"]:
            print("✅ Resend OTP successful!")
            print(f"   Message: {resend_response['message']}")
        else:
            print("❌ Resend OTP failed!")
            print(f"   Error: {resend_response['error']}")
        
        print("\n✨ Registration flow test completed!")
        print("📋 Next steps:")
        print("   1. Verify email with OTP code")
        print("   2. Test login functionality")
        print("   3. Test 2FA setup (optional)")
    
    async def register_user(self, user_data: dict) -> dict:
        """Test user registration"""
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 201:
                    data = await response.json()
                    return {
                        "success": True,
                        "message": data.get("message", "Registration successful")
                    }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "error": error_data.get("detail", f"HTTP {response.status}")
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }
    
    async def resend_otp(self, email: str) -> dict:
        """Test resend OTP"""
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/resend-registration-otp",
                json={"email": email},
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "message": data.get("message", "OTP resent successfully")
                    }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "error": error_data.get("detail", f"HTTP {response.status}")
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }
    
    async def test_health_check(self) -> dict:
        """Test auth health check"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/auth/health"
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "data": data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }


async def main():
    """Main test function"""
    print("🚀 Starting Authentication Module Test")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async with RegistrationTester() as tester:
        await tester.test_registration_flow()


if __name__ == "__main__":
    # Chạy test
    asyncio.run(main())