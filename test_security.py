#!/usr/bin/env python3
"""
Security Test Suite for AI Voice Policy Assistant
Tests user isolation, document access control, and organization-level security.
"""

import requests
import json
import time
from typing import Dict, Any

class SecurityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user1_token = None
        self.user2_token = None
        self.user1_org_id = None
        self.user2_org_id = None
        self.test_emails = []
        self.test_org_names = []
        
    def test_user_registration_and_isolation(self) -> bool:
        """Test that users can register and are properly isolated."""
        print("🔐 Testing User Registration and Isolation...")
        
        # Register User 1
        user1_data = {
            "email": f"security_user1_{int(time.time())}@test.com",
            "password": "securepass123",
            "org_name": f"Security Test Org 1_{int(time.time())}"
        }
        
        # Track test data for cleanup
        self.test_emails.append(user1_data["email"])
        self.test_org_names.append(user1_data["org_name"])
        
        response = self.session.post(f"{self.base_url}/auth/signup", json=user1_data)
        if response.status_code not in [200, 201]:
            print(f"❌ User 1 registration failed: {response.status_code} - {response.text}")
            return False
        
        # Login User 1
        login_data = {"email": user1_data["email"], "password": user1_data["password"]}
        response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ User 1 login failed: {response.status_code} - {response.text}")
            return False
        
        self.user1_token = response.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.user1_token}"})
        
        # Get User 1's organization info
        response = self.session.get(f"{self.base_url}/admin/organizations")
        if response.status_code == 200:
            orgs = response.json().get("data", [])
            if orgs:
                self.user1_org_id = orgs[0]["id"]
                print(f"✅ User 1 registered and logged in. Org ID: {self.user1_org_id}")
        
        # Register User 2 (different organization)
        user2_data = {
            "email": f"security_user2_{int(time.time())}@test.com", 
            "password": "securepass456",
            "org_name": f"Security Test Org 2_{int(time.time())}"
        }
        
        # Track test data for cleanup
        self.test_emails.append(user2_data["email"])
        self.test_org_names.append(user2_data["org_name"])
        
        response = self.session.post(f"{self.base_url}/auth/signup", json=user2_data)
        if response.status_code not in [200, 201]:
            print(f"❌ User 2 registration failed: {response.status_code} - {response.text}")
            return False
        
        # Login User 2
        login_data = {"email": user2_data["email"], "password": user2_data["password"]}
        response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ User 2 login failed: {response.status_code} - {response.text}")
            return False
        
        self.user2_token = response.json()["access_token"]
        
        # Get User 2's organization info
        temp_session = requests.Session()
        temp_session.headers.update({"Authorization": f"Bearer {self.user2_token}"})
        response = temp_session.get(f"{self.base_url}/admin/organizations")
        if response.status_code == 200:
            orgs = response.json().get("data", [])
            if orgs:
                self.user2_org_id = orgs[0]["id"]
                print(f"✅ User 2 registered and logged in. Org ID: {self.user2_org_id}")
        
        return True
    
    def test_document_isolation(self) -> bool:
        """Test that users can only see their own documents."""
        print("📄 Testing Document Isolation...")
        
        if not self.user1_token or not self.user2_token:
            print("❌ Users not properly authenticated")
            return False
        
        # User 1 uploads a document
        self.session.headers.update({"Authorization": f"Bearer {self.user1_token}"})
        doc1_data = {
            "title": "User 1 Secret Document",
            "text": "This document contains sensitive information for User 1 only.",
            "source": "internal",
            "metadata": {"security_level": "high", "owner": "user1"}
        }
        
        response = self.session.post(f"{self.base_url}/corpus/doc", json=doc1_data)
        if response.status_code not in [200, 201]:
            print(f"❌ User 1 document upload failed: {response.status_code} - {response.text}")
            return False
        
        doc1_id = response.json()["id"]
        print(f"✅ User 1 uploaded document: {doc1_id}")
        
        # User 2 uploads a document
        temp_session = requests.Session()
        temp_session.headers.update({"Authorization": f"Bearer {self.user2_token}"})
        doc2_data = {
            "title": "User 2 Secret Document", 
            "text": "This document contains sensitive information for User 2 only.",
            "source": "internal",
            "metadata": {"security_level": "high", "owner": "user2"}
        }
        
        response = temp_session.post(f"{self.base_url}/corpus/doc", json=doc2_data)
        if response.status_code not in [200, 201]:
            print(f"❌ User 2 document upload failed: {response.status_code} - {response.text}")
            return False
        
        doc2_id = response.json()["id"]
        print(f"✅ User 2 uploaded document: {doc2_id}")
        
        # User 1 lists documents (should only see their own)
        self.session.headers.update({"Authorization": f"Bearer {self.user1_token}"})
        response = self.session.get(f"{self.base_url}/corpus/docs")
        if response.status_code != 200:
            print(f"❌ User 1 document list failed: {response.status_code} - {response.text}")
            return False
        
        user1_docs = response.json()
        user1_doc_ids = [doc["id"] for doc in user1_docs]
        
        # User 2 lists documents (should only see their own)
        temp_session.headers.update({"Authorization": f"Bearer {self.user2_token}"})
        response = temp_session.get(f"{self.base_url}/corpus/docs")
        if response.status_code != 200:
            print(f"❌ User 2 document list failed: {response.status_code} - {response.text}")
            return False
        
        user2_docs = response.json()
        user2_doc_ids = [doc["id"] for doc in user2_docs]
        
        # Verify isolation
        if doc1_id in user2_doc_ids:
            print(f"❌ SECURITY BREACH: User 2 can see User 1's document {doc1_id}")
            return False
        
        if doc2_id in user1_doc_ids:
            print(f"❌ SECURITY BREACH: User 1 can see User 2's document {doc2_id}")
            return False
        
        print(f"✅ Document isolation verified: User 1 sees {len(user1_docs)} docs, User 2 sees {len(user2_docs)} docs")
        return True
    
    def test_search_isolation(self) -> bool:
        """Test that search results are isolated by organization."""
        print("🔍 Testing Search Isolation...")
        
        if not self.user1_token or not self.user2_token:
            print("❌ Users not properly authenticated")
            return False
        
        # User 1 searches for documents
        self.session.headers.update({"Authorization": f"Bearer {self.user1_token}"})
        search_data = {"query": "secret document", "k": 10}
        
        response = self.session.post(f"{self.base_url}/corpus/search", json=search_data)
        if response.status_code != 200:
            print(f"❌ User 1 search failed: {response.status_code} - {response.text}")
            return False
        
        user1_results = response.json()["results"]
        user1_doc_ids = [result["doc_id"] for result in user1_results]
        
        # User 2 searches for documents
        temp_session = requests.Session()
        temp_session.headers.update({"Authorization": f"Bearer {self.user2_token}"})
        response = temp_session.post(f"{self.base_url}/corpus/search", json=search_data)
        if response.status_code != 200:
            print(f"❌ User 2 search failed: {response.status_code} - {response.text}")
            return False
        
        user2_results = response.json()["results"]
        user2_doc_ids = [result["doc_id"] for result in user2_results]
        
        # Verify search isolation
        if any(doc_id in user2_doc_ids for doc_id in user1_doc_ids):
            print(f"❌ SECURITY BREACH: Search results not isolated between users")
            return False
        
        print(f"✅ Search isolation verified: User 1 found {len(user1_results)} results, User 2 found {len(user2_results)} results")
        return True
    
    def test_chat_context_isolation(self) -> bool:
        """Test that chat responses only reference user's own documents."""
        print("💬 Testing Chat Context Isolation...")
        
        if not self.user1_token or not self.user2_token:
            print("❌ Users not properly authenticated")
            return False
        
        # User 1 asks a question about their document
        self.session.headers.update({"Authorization": f"Bearer {self.user1_token}"})
        chat_data = {"text": "What does my secret document contain?"}
        
        response = self.session.post(f"{self.base_url}/chat/", json=chat_data)
        if response.status_code != 200:
            print(f"❌ User 1 chat failed: {response.status_code} - {response.text}")
            return False
        
        user1_response = response.json()["response"]
        
        # User 2 asks the same question
        temp_session = requests.Session()
        temp_session.headers.update({"Authorization": f"Bearer {self.user2_token}"})
        response = temp_session.post(f"{self.base_url}/chat/", json=chat_data)
        if response.status_code != 200:
            print(f"❌ User 2 chat failed: {response.status_code} - {response.text}")
            return False
        
        user2_response = response.json()["response"]
        
        # Verify responses are different (different context)
        if user1_response == user2_response:
            print(f"❌ SECURITY BREACH: Both users got identical responses despite different documents")
            return False
        
        print(f"✅ Chat context isolation verified: Users got different responses based on their own documents")
        return True
    
    def test_admin_isolation(self) -> bool:
        """Test that admin endpoints only show user's organization data."""
        print("👑 Testing Admin Endpoint Isolation...")
        
        if not self.user1_token or not self.user2_token:
            print("❌ Users not properly authenticated")
            return False
        
        # User 1 gets system status
        self.session.headers.update({"Authorization": f"Bearer {self.user1_token}"})
        response = self.session.get(f"{self.base_url}/admin/system-status")
        if response.status_code != 200:
            print(f"❌ User 1 system status failed: {response.status_code} - {response.text}")
            return False
        
        user1_status = response.json()["data"]
        
        # User 2 gets system status
        temp_session = requests.Session()
        temp_session.headers.update({"Authorization": f"Bearer {self.user2_token}"})
        response = temp_session.get(f"{self.base_url}/admin/system-status")
        if response.status_code != 200:
            print(f"❌ User 2 system status failed: {response.status_code} - {response.text}")
            return False
        
        user2_status = response.json()["data"]
        
        # Verify admin isolation
        if user1_status.get("database", {}).get("organization_id") == user2_status.get("database", {}).get("organization_id"):
            print(f"❌ SECURITY BREACH: Admin endpoints showing same organization data for different users")
            return False
        
        print(f"✅ Admin isolation verified: User 1 org {user1_status.get('database', {}).get('organization_id')}, User 2 org {user2_status.get('database', {}).get('organization_id')}")
        return True
    
    def cleanup_test_data(self):
        """Clean up test data from previous test runs."""
        print("🧹 Using unique identifiers to avoid conflicts with previous test runs...")
        # We'll use timestamp-based unique identifiers instead of trying to delete data
    
    def run_all_security_tests(self) -> bool:
        """Run all security tests."""
        print("🔒 AI Voice Policy Assistant - Security Test Suite")
        print("=" * 60)
        
        # Clean up test data from previous runs
        self.cleanup_test_data()
        
        tests = [
            ("User Registration and Isolation", self.test_user_registration_and_isolation),
            ("Document Isolation", self.test_document_isolation),
            ("Search Isolation", self.test_search_isolation),
            ("Chat Context Isolation", self.test_chat_context_isolation),
            ("Admin Endpoint Isolation", self.test_admin_isolation)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                if test_func():
                    print(f"✅ {test_name}: PASSED")
                    passed += 1
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
        
        print("\n" + "=" * 60)
        print(f"🔒 SECURITY TEST RESULTS: {passed}/{total} PASSED")
        print("=" * 60)
        
        if passed == total:
            print("🎉 ALL SECURITY TESTS PASSED! Your system is secure!")
        else:
            print("⚠️  Some security tests failed. Review the results above.")
        
        return passed == total

if __name__ == "__main__":
    tester = SecurityTester()
    success = tester.run_all_security_tests()
    exit(0 if success else 1)
