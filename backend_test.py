#!/usr/bin/env python3
"""
Spark Core 2.0 - Auth Module Backend Testing
Tests all authentication endpoints and functionality
"""
import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class SparkAuthTester:
    def __init__(self, base_url: str = "https://question-hub-160.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # Test data
        self.test_user = {
            "naam": "Willem",
            "sleutelwoord": "Appelsap",
            "user_id": "user-001"
        }
        self.masterkey = "SAMEN"
        
        # Test counters
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        print("🚀 Spark Core 2.0 Auth Module Tester")
        print(f"📡 Backend URL: {self.base_url}")
        print("=" * 60)

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            self.failed_tests.append({"name": name, "details": details})
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
        print()

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                return False, {}, 0
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return response.status_code < 400, response_data, response.status_code
            
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_api_root(self):
        """Test GET /api - Module overview"""
        success, data, status = self.make_request('GET', '/api')
        
        if success and status == 200:
            if 'modules' in data and 'auth' in data.get('modules', {}):
                auth_module = data['modules']['auth']
                if auth_module.get('status') == 'active':
                    self.log_test("API Root - Module Overview", True, 
                                f"Auth module active with {len(auth_module.get('endpoints', []))} endpoints")
                else:
                    self.log_test("API Root - Module Overview", False, 
                                f"Auth module status: {auth_module.get('status')}")
            else:
                self.log_test("API Root - Module Overview", False, "Auth module not found in response")
        else:
            self.log_test("API Root - Module Overview", False, 
                        f"Status: {status}, Response: {data}")

    def test_login_with_password(self):
        """Test POST /api/auth/login with naam + sleutelwoord"""
        login_data = {
            "naam": self.test_user["naam"],
            "sleutelwoord": self.test_user["sleutelwoord"]
        }
        
        success, data, status = self.make_request('POST', '/api/auth/login', login_data)
        
        if success and status == 200:
            if data.get('success') and data.get('user'):
                user = data['user']
                if user.get('id') == self.test_user["user_id"]:
                    self.log_test("Login with Password", True, 
                                f"User: {user.get('naam')} (ID: {user.get('id')})")
                    return user
                else:
                    self.log_test("Login with Password", False, 
                                f"Wrong user ID: {user.get('id')}")
            else:
                self.log_test("Login with Password", False, 
                            f"Login failed: {data.get('message')}")
        else:
            self.log_test("Login with Password", False, 
                        f"Status: {status}, Response: {data}")
        return None

    def test_login_with_masterkey(self):
        """Test POST /api/auth/login with masterkey"""
        login_data = {
            "naam": self.test_user["naam"],
            "sleutelwoord": "",
            "masterkey": self.masterkey
        }
        
        success, data, status = self.make_request('POST', '/api/auth/login', login_data)
        
        if success and status == 200:
            if data.get('success') and data.get('is_masterkey'):
                user = data['user']
                self.log_test("Login with Masterkey", True, 
                            f"Masterkey access for: {user.get('naam')}")
                return user
            else:
                self.log_test("Login with Masterkey", False, 
                            f"Masterkey login failed: {data.get('message')}")
        else:
            self.log_test("Login with Masterkey", False, 
                        f"Status: {status}, Response: {data}")
        return None

    def test_get_all_users(self):
        """Test GET /api/auth/users"""
        success, data, status = self.make_request('GET', '/api/auth/users')
        
        if success and status == 200:
            if 'users' in data and 'count' in data:
                user_count = data['count']
                users = data['users']
                
                # Check if Willem is in the list
                willem_found = any(u.get('naam') in ['Willem', 'De Willem'] for u in users)
                
                if willem_found and user_count > 0:
                    self.log_test("Get All Users", True, 
                                f"Found {user_count} users, Willem included")
                else:
                    self.log_test("Get All Users", False, 
                                f"Willem not found in {user_count} users")
            else:
                self.log_test("Get All Users", False, "Invalid response format")
        else:
            self.log_test("Get All Users", False, 
                        f"Status: {status}, Response: {data}")

    def test_get_specific_user(self):
        """Test GET /api/auth/users/{user_id}"""
        user_id = self.test_user["user_id"]
        success, data, status = self.make_request('GET', f'/api/auth/users/{user_id}')
        
        if success and status == 200:
            if data.get('id') == user_id and data.get('naam'):
                self.log_test("Get Specific User", True, 
                            f"Retrieved user: {data.get('naam')} (Gradatie: {data.get('gradatie')})")
            else:
                self.log_test("Get Specific User", False, "User data incomplete")
        else:
            self.log_test("Get Specific User", False, 
                        f"Status: {status}, Response: {data}")

    def test_session_heartbeat(self):
        """Test POST /api/auth/session/heartbeat"""
        user_id = self.test_user["user_id"]
        success, data, status = self.make_request('POST', '/api/auth/session/heartbeat', 
                                                params={"user_id": user_id})
        
        if success and status == 200:
            if data.get('status') == 'active' and data.get('user_id') == user_id:
                self.log_test("Session Heartbeat", True, 
                            f"Session active, expires in: {data.get('expires_in')}s")
            else:
                self.log_test("Session Heartbeat", False, 
                            f"Unexpected session status: {data.get('status')}")
        else:
            self.log_test("Session Heartbeat", False, 
                        f"Status: {status}, Response: {data}")

    def test_session_validate(self):
        """Test GET /api/auth/session/validate"""
        user_id = self.test_user["user_id"]
        success, data, status = self.make_request('GET', '/api/auth/session/validate', 
                                                params={"user_id": user_id})
        
        if success and status == 200:
            if data.get('valid') and data.get('user'):
                user = data['user']
                self.log_test("Session Validate", True, 
                            f"Session valid for: {user.get('naam')}")
            else:
                self.log_test("Session Validate", False, 
                            f"Session invalid: {data.get('message')}")
        else:
            self.log_test("Session Validate", False, 
                        f"Status: {status}, Response: {data}")

    def test_get_gradaties(self):
        """Test GET /api/auth/gradaties"""
        success, data, status = self.make_request('GET', '/api/auth/gradaties')
        
        if success and status == 200:
            if 'gradaties' in data:
                gradaties = data['gradaties']
                if len(gradaties) > 0:
                    self.log_test("Get Gradaties", True, 
                                f"Found {len(gradaties)} gradatie levels")
                else:
                    self.log_test("Get Gradaties", False, "No gradaties found")
            else:
                self.log_test("Get Gradaties", False, "Invalid response format")
        else:
            self.log_test("Get Gradaties", False, 
                        f"Status: {status}, Response: {data}")

    def test_create_user(self):
        """Test POST /api/auth/users - Create new user"""
        timestamp = datetime.now().strftime("%H%M%S")
        new_user_data = {
            "naam": f"TestUser{timestamp}",
            "volledige_naam": f"Test User {timestamp}",
            "sleutelwoord": f"TestPass{timestamp}"
        }
        
        success, data, status = self.make_request('POST', '/api/auth/users', new_user_data)
        
        if success and status == 200:
            if data.get('success') and data.get('user'):
                user = data['user']
                self.log_test("Create User", True, 
                            f"Created user: {user.get('naam')} (ID: {user.get('id')})")
                return user.get('id')
            else:
                self.log_test("Create User", False, 
                            f"User creation failed: {data}")
        else:
            self.log_test("Create User", False, 
                        f"Status: {status}, Response: {data}")
        return None

    def test_update_user(self, user_id: str):
        """Test PUT /api/auth/users/{user_id} - Update user"""
        if not user_id:
            self.log_test("Update User", False, "No user ID provided")
            return
        
        update_data = {
            "volledige_naam": "Updated Test User",
            "xp": 100
        }
        
        success, data, status = self.make_request('PUT', f'/api/auth/users/{user_id}', update_data)
        
        if success and status == 200:
            if data.get('success'):
                self.log_test("Update User", True, "User updated successfully")
            else:
                self.log_test("Update User", False, "Update failed")
        else:
            self.log_test("Update User", False, 
                        f"Status: {status}, Response: {data}")

    def test_update_gradatie(self):
        """Test PUT /api/auth/users/{user_id}/gradatie - Update gradatie"""
        user_id = self.test_user["user_id"]
        
        # Try to update gradatie (should work for Willem as gradatie 1)
        params = {"gradatie": 2, "reden": "Test gradatie update"}
        success, data, status = self.make_request('PUT', f'/api/auth/users/{user_id}/gradatie', 
                                                params=params)
        
        if success and status == 200:
            if data.get('success'):
                self.log_test("Update Gradatie", True, "Gradatie updated successfully")
                
                # Revert back to original gradatie
                revert_params = {"gradatie": 1, "reden": "Revert test change"}
                self.make_request('PUT', f'/api/auth/users/{user_id}/gradatie', 
                                params=revert_params)
            else:
                self.log_test("Update Gradatie", False, "Gradatie update failed")
        else:
            self.log_test("Update Gradatie", False, 
                        f"Status: {status}, Response: {data}")

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        invalid_login = {
            "naam": "NonExistentUser",
            "sleutelwoord": "WrongPassword"
        }
        
        success, data, status = self.make_request('POST', '/api/auth/login', invalid_login)
        
        if success and status == 200:
            if not data.get('success'):
                self.log_test("Invalid Login Handling", True, 
                            f"Correctly rejected: {data.get('message')}")
            else:
                self.log_test("Invalid Login Handling", False, 
                            "Invalid login was accepted")
        else:
            self.log_test("Invalid Login Handling", False, 
                        f"Unexpected status: {status}")

    def run_all_tests(self):
        """Run all authentication tests"""
        print("🧪 Starting Spark Auth Module Tests\n")
        
        # Basic API tests
        self.test_api_root()
        
        # Authentication tests
        self.test_login_with_password()
        self.test_login_with_masterkey()
        self.test_invalid_login()
        
        # User management tests
        self.test_get_all_users()
        self.test_get_specific_user()
        
        # Session management tests
        self.test_session_heartbeat()
        self.test_session_validate()
        
        # Gradatie system tests
        self.test_get_gradaties()
        self.test_update_gradatie()
        
        # User CRUD tests
        new_user_id = self.test_create_user()
        if new_user_id:
            self.test_update_user(new_user_id)
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests Failed: {len(self.failed_tests)}/{self.tests_run}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print("\n🚨 FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}")
                if test['details']:
                    print(f"   Details: {test['details']}")
        
        print("\n" + "=" * 60)
        
        return len(self.failed_tests) == 0

def main():
    """Main test runner"""
    tester = SparkAuthTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())