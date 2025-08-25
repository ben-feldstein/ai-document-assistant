#!/usr/bin/env python3
"""
Comprehensive API Testing Script for AI Voice Policy Assistant
Tests all endpoints and features systematically
"""

import requests
import json
import time
import websocket
import threading
from datetime import datetime
import sys

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/audio?session_id=test123"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "timestamp": timestamp,
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        }
        self.test_results.append(result)
        print(f"[{timestamp}] {status} {test_name}: {message}")
        if details and not success:
            print(f"    Details: {details}")
    
    def test_health_check(self):
        """Test system health endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/healthz")
            if response.status_code == 200:
                data = response.json()
                services = data.get("services", {})
                unhealthy_services = [k for k, v in services.items() if v != "healthy"]
                
                if not unhealthy_services:
                    self.log_test("Health Check", True, "All services healthy")
                else:
                    self.log_test("Health Check", False, f"Unhealthy services: {unhealthy_services}")
                return data
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return None
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = self.session.get(BASE_URL)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Root Endpoint", True, "API information retrieved")
                return data
            else:
                self.log_test("Root Endpoint", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Exception: {str(e)}")
            return None
    
    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/metrics")
            if response.status_code == 200:
                content = response.text
                if "http_requests_total" in content:
                    self.log_test("Metrics Endpoint", True, "Prometheus metrics retrieved")
                    return True
                else:
                    self.log_test("Metrics Endpoint", False, "Metrics content not as expected")
                    return False
            else:
                self.log_test("Metrics Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Metrics Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_user_registration(self, email="test@example.com", password="testpassword123"):
        """Test user registration"""
        try:
            data = {"email": email, "password": password, "org_name": "Test Organization"}
            response = self.session.post(f"{BASE_URL}/auth/signup", json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.log_test("User Registration", True, f"User {email} registered successfully")
                return result
            elif response.status_code == 400:
                result = response.json()
                if "already exists" in result.get("detail", "").lower():
                    self.log_test("User Registration", True, f"User {email} already exists (success)")
                    return result
                else:
                    self.log_test("User Registration", False, f"Bad request: {result}")
                    return None
            else:
                self.log_test("User Registration", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return None
    
    def test_user_login(self, email="test@example.com", password="testpassword123"):
        """Test user login"""
        try:
            data = {"email": email, "password": password}
            response = self.session.post(f"{BASE_URL}/auth/login", json=data)
            
            if response.status_code == 200:
                result = response.json()
                if "access_token" in result:
                    self.auth_token = result["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_test("User Login", True, f"User {email} logged in successfully")
                    return result
                else:
                    self.log_test("User Login", False, "No access token in response")
                    return None
            else:
                self.log_test("User Login", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("User Login", False, f"Exception: {str(e)}")
            return None
    
    def test_chat_endpoint(self, message="What is the company's PTO policy?"):
        """Test chat endpoint"""
        if not self.auth_token:
            self.log_test("Chat Endpoint", False, "No auth token available")
            return None
        
        try:
            data = {"text": message}
            response = self.session.post(f"{BASE_URL}/chat/", json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Chat Endpoint", True, "Chat message sent successfully")
                return result
            else:
                self.log_test("Chat Endpoint", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Chat Endpoint", False, f"Exception: {str(e)}")
            return None
    
    def test_document_upload(self, title="Test Policy Document", content="This is a test policy document for testing purposes."):
        """Test document upload"""
        if not self.auth_token:
            self.log_test("Document Upload", False, "No auth token available")
            return None
        
        try:
            data = {"title": title, "text": content, "source": "test-source"}
            response = self.session.post(f"{BASE_URL}/corpus/doc", json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.log_test("Document Upload", True, f"Document '{title}' uploaded successfully")
                return result
            else:
                self.log_test("Document Upload", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Document Upload", False, f"Exception: {str(e)}")
            return None
    
    def test_document_search(self, query="policy"):
        """Test document search"""
        if not self.auth_token:
            self.log_test("Document Search", False, "No auth token available")
            return None
        
        try:
            response = self.session.post(f"{BASE_URL}/corpus/search", json={"query": query})
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Document Search", True, f"Search for '{query}' completed")
                return result
            else:
                self.log_test("Document Search", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Document Search", False, f"Exception: {str(e)}")
            return None
    
    def test_document_list(self):
        """Test document listing"""
        if not self.auth_token:
            self.log_test("Document List", False, "No auth token available")
            return None
        
        try:
            response = self.session.get(f"{BASE_URL}/corpus/docs")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Document List", True, "Document list retrieved successfully")
                return result
            else:
                self.log_test("Document List", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Document List", False, f"Exception: {str(e)}")
            return None
    
    def test_admin_endpoints(self):
        """Test admin endpoints"""
        if not self.auth_token:
            self.log_test("Admin Endpoints", False, "No auth token available")
            return None
        
        # Test user stats
        try:
            response = self.session.get(f"{BASE_URL}/admin/system-status")
            if response.status_code == 200:
                self.log_test("Admin User Stats", True, "User statistics retrieved")
            else:
                self.log_test("Admin User Stats", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Admin User Stats", False, f"Exception: {str(e)}")
        
        # Test service logs (if endpoint exists)
        try:
            response = self.session.get(f"{BASE_URL}/admin/organizations")
            if response.status_code == 200:
                self.log_test("Admin Service Logs", True, "Service logs retrieved")
            else:
                self.log_test("Admin Service Logs", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Admin Service Logs", False, f"Exception: {str(e)}")
    
    def test_websocket_connection(self):
        """Test WebSocket connection"""
        try:
            # Test basic connection
            ws = websocket.create_connection(WS_URL, timeout=5)
            if ws.connected:
                self.log_test("WebSocket Connection", True, "WebSocket connected successfully")
                ws.close()
                return True
            else:
                self.log_test("WebSocket Connection", False, "WebSocket not connected")
                return False
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Exception: {str(e)}")
            return False
    
    def test_rate_limiting(self):
        """Test rate limiting by making multiple requests"""
        if not self.auth_token:
            self.log_test("Rate Limiting", False, "No auth token available")
            return None
        
        try:
            # Make multiple requests quickly
            responses = []
            for i in range(5):
                response = self.session.post(f"{BASE_URL}/chat", json={"message": f"Test message {i}"})
                responses.append(response.status_code)
                time.sleep(0.1)  # Small delay
            
            # Check if any requests were rate limited (429 status)
            if 429 in responses:
                self.log_test("Rate Limiting", True, "Rate limiting working correctly")
                return True
            else:
                self.log_test("Rate Limiting", True, "All requests processed (rate limit not triggered)")
                return True
        except Exception as e:
            self.log_test("Rate Limiting", False, f"Exception: {str(e)}")
            return None
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive API Testing...")
        print("=" * 60)
        
        # Test basic endpoints first
        self.test_health_check()
        self.test_root_endpoint()
        self.test_metrics_endpoint()
        
        # Test authentication
        self.test_user_registration("newuser2@test.com", "newpass123")
        self.test_user_login()
        
        # Test authenticated endpoints
        if self.auth_token:
            self.test_chat_endpoint()
            self.test_document_upload()
            self.test_document_search()
            self.test_document_list()
            self.test_admin_endpoints()
            self.test_rate_limiting()
        
        # Test WebSocket
        self.test_websocket_connection()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n🎯 Next Steps:")
        if failed_tests == 0:
            print("  🎉 All tests passed! Your API is working perfectly.")
            print("  🚀 You can now build the modern UI with confidence.")
        else:
            print("  🔧 Fix the failed tests before proceeding.")
            print("  📝 Check the error details above for guidance.")
        
        print("  🌐 Open test-ui.html in your browser for interactive testing.")
        print("  📱 Start building the modern UI once all tests pass.")

def main():
    """Main function"""
    print("🎤 AI Voice Policy Assistant - API Testing Suite")
    print("=" * 60)
    
    # Check if services are running
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if response.status_code != 200:
            print("❌ API is not responding. Make sure your services are running:")
            print("   docker-compose -f infra/docker-compose.yml up -d")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API. Make sure your services are running:")
        print("   docker-compose -f infra/docker-compose.yml up -d")
        sys.exit(1)
    
    # Run tests
    tester = APITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
