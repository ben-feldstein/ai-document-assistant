#!/usr/bin/env python3
"""
Comprehensive Security Test with Substantial Documents
Tests user isolation with real, searchable content.
"""

import requests
import json
import time

class SecurityManualTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user1_token = None
        self.user2_token = None
        self.user1_org_id = None
        self.user2_org_id = None
        
    def test_comprehensive_security(self):
        """Run comprehensive security test with substantial documents."""
        print("🔒 Comprehensive Security Test with Substantial Documents")
        print("=" * 70)
        
        # Step 1: Create and authenticate users
        if not self._setup_users():
            return False
        
        # Step 2: Upload substantial, distinct documents
        if not self._upload_documents():
            return False
        
        # Step 3: Test document isolation
        if not self._test_document_isolation():
            return False
        
        # Step 4: Test search isolation
        if not self._test_search_isolation():
            return False
        
        # Step 5: Test chat context isolation
        if not self._test_chat_isolation():
            return False
        
        print("\n" + "=" * 70)
        print("🎉 ALL SECURITY TESTS PASSED! Your system is enterprise-ready!")
        print("=" * 70)
        return True
    
    def _setup_users(self):
        """Create and authenticate two users in different organizations."""
        print("\n👥 Step 1: Setting up users...")
        
        # Create unique identifiers
        timestamp = int(time.time())
        
        # User 1 - Healthcare Organization
        user1_data = {
            "email": f"healthcare_admin_{timestamp}@test.com",
            "password": "securepass123",
            "org_name": f"Healthcare Corp {timestamp}"
        }
        
        # User 2 - Tech Organization  
        user2_data = {
            "email": f"tech_admin_{timestamp}@test.com",
            "password": "securepass456",
            "org_name": f"Tech Solutions {timestamp}"
        }
        
        # Register and login users
        for i, (user_data, user_name) in enumerate([(user1_data, "Healthcare Admin"), (user2_data, "Tech Admin")]):
            print(f"\n  Creating {user_name}...")
            
            # Register
            response = self.session.post(f"{self.base_url}/auth/signup", json=user_data)
            if response.status_code not in [200, 201]:
                print(f"    ❌ Registration failed: {response.status_code}")
                return False
            
            # Login
            login_data = {"email": user_data["email"], "password": user_data["password"]}
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code != 200:
                print(f"    ❌ Login failed: {response.status_code}")
                return False
            
            token = response.json()["access_token"]
            
            if i == 0:
                self.user1_token = token
                print(f"    ✅ {user_name} created and logged in")
            else:
                self.user2_token = token
                print(f"    ✅ {user_name} created and logged in")
        
        return True
    
    def _upload_documents(self):
        """Upload substantial, distinct documents for each user."""
        print("\n📄 Step 2: Uploading substantial documents...")
        
        # Healthcare Admin Document
        healthcare_doc = {
            "title": "Healthcare Organization Policy Manual",
            "text": """This comprehensive healthcare organization policy manual contains detailed guidelines for medical staff, patient care protocols, and administrative procedures. It covers HIPAA compliance requirements, patient privacy protection measures, medical record management standards, emergency response procedures, infection control protocols, and staff training requirements. The manual includes specific policies for handling sensitive patient information, maintaining medical equipment, and ensuring quality care delivery. This document is confidential and contains proprietary healthcare information that must be protected according to federal regulations.""",
            "source": "internal",
            "metadata": {"department": "administration", "security_level": "high", "category": "healthcare"}
        }
        
        # Tech Admin Document
        tech_doc = {
            "title": "Software Development Standards and Procedures",
            "text": """This comprehensive software development standards document outlines our organization's coding practices, deployment procedures, and quality assurance protocols. It includes detailed API design guidelines, database schema standards, security implementation requirements, testing methodologies, and DevOps best practices. The document covers microservices architecture patterns, containerization strategies, CI/CD pipeline configurations, monitoring and alerting systems, and incident response procedures. This is proprietary technical information that contains trade secrets and competitive advantages that must be protected from unauthorized access.""",
            "source": "internal", 
            "metadata": {"department": "engineering", "security_level": "high", "category": "technology"}
        }
        
        # Upload Healthcare Document
        print("\n  Uploading Healthcare Policy Manual...")
        self.session.headers.update({"Authorization": f"Bearer {self.user1_token}"})
        response = self.session.post(f"{self.base_url}/corpus/doc", json=healthcare_doc)
        if response.status_code not in [200, 201]:
            print(f"    ❌ Healthcare document upload failed: {response.status_code}")
            return False
        print(f"    ✅ Healthcare document uploaded (ID: {response.json()['id']})")
        
        # Upload Tech Document
        print("\n  Uploading Tech Development Standards...")
        self.session.headers.update({"Authorization": f"Bearer {self.user2_token}"})
        response = self.session.post(f"{self.base_url}/corpus/doc", json=tech_doc)
        if response.status_code not in [200, 201]:
            print(f"    ❌ Tech document upload failed: {response.status_code}")
            return False
        print(f"    ✅ Tech document uploaded (ID: {response.json()['id']})")
        
        # Wait for processing
        print("\n  ⏳ Waiting for document processing...")
        time.sleep(3)
        
        return True
    
    def _test_document_isolation(self):
        """Test that users can only see their own documents."""
        print("\n🔒 Step 3: Testing document isolation...")
        
        # User 1 lists documents
        print("\n  Healthcare Admin listing documents...")
        self.session.headers.update({"Authorization": f"Bearer {self.user1_token}"})
        response = self.session.get(f"{self.base_url}/corpus/docs")
        if response.status_code != 200:
            print(f"    ❌ Healthcare Admin document list failed: {response.status_code}")
            return False
        
        user1_docs = response.json()
        user1_titles = [doc["title"] for doc in user1_docs]
        print(f"    ✅ Healthcare Admin sees {len(user1_docs)} documents")
        print(f"    📋 Document titles: {user1_titles}")
        
        # User 2 lists documents
        print("\n  Tech Admin listing documents...")
        self.session.headers.update({"Authorization": f"Bearer {self.user2_token}"})
        response = self.session.get(f"{self.base_url}/corpus/docs")
        if response.status_code != 200:
            print(f"    ❌ Tech Admin document list failed: {response.status_code}")
            return False
        
        user2_docs = response.json()
        user2_titles = [doc["title"] for doc in user2_docs]
        print(f"    ✅ Tech Admin sees {len(user2_docs)} documents")
        print(f"    📋 Document titles: {user2_titles}")
        
        # Verify isolation
        if any("Healthcare" in title for title in user2_titles):
            print("    ❌ SECURITY BREACH: Tech Admin can see Healthcare documents!")
            return False
        
        if any("Software Development" in title for title in user1_titles):
            print("    ❌ SECURITY BREACH: Healthcare Admin can see Tech documents!")
            return False
        
        print("    ✅ Document isolation verified - users only see their own documents")
        return True
    
    def _test_search_isolation(self):
        """Test that search results are isolated by organization."""
        print("\n🔍 Step 4: Testing search isolation...")
        
        # Test search terms that should only match one organization's documents
        search_tests = [
            ("HIPAA compliance", "healthcare"),
            ("microservices architecture", "technology"),
            ("patient privacy", "healthcare"),
            ("CI/CD pipeline", "technology")
        ]
        
        for search_term, expected_org in search_tests:
            print(f"\n  Testing search: '{search_term}' (should find {expected_org} docs)")
            
            # Healthcare Admin search
            self.session.headers.update({"Authorization": f"Bearer {self.user1_token}"})
            response = self.session.post(f"{self.base_url}/corpus/search", json={"query": search_term, "k": 5})
            if response.status_code != 200:
                print(f"    ❌ Healthcare Admin search failed: {response.status_code}")
                return False
            
            user1_results = response.json()["results"]
            user1_titles = [result["title"] for result in user1_results]
            
            # Tech Admin search
            self.session.headers.update({"Authorization": f"Bearer {self.user2_token}"})
            response = self.session.post(f"{self.base_url}/corpus/search", json={"query": search_term, "k": 5})
            if response.status_code != 200:
                print(f"    ❌ Tech Admin search failed: {response.status_code}")
                return False
            
            user2_results = response.json()["results"]
            user2_titles = [result["title"] for result in user2_results]
            
            # Verify search isolation
            if expected_org == "healthcare":
                if not any("Healthcare" in title for title in user1_titles):
                    print(f"    ❌ Healthcare Admin didn't find expected healthcare document for '{search_term}'")
                    return False
                if any("Healthcare" in title for title in user2_titles):
                    print(f"    ❌ SECURITY BREACH: Tech Admin found healthcare document for '{search_term}'")
                    return False
            else:  # technology
                if not any("Software Development" in title for title in user2_titles):
                    print(f"    ❌ Tech Admin didn't find expected tech document for '{search_term}'")
                    return False
                if any("Software Development" in title for title in user1_titles):
                    print(f"    ❌ SECURITY BREACH: Healthcare Admin found tech document for '{search_term}'")
                    return False
            
            print(f"    ✅ Search isolation verified for '{search_term}'")
        
        return True
    
    def _test_chat_isolation(self):
        """Test that chat responses are isolated by organization."""
        print("\n💬 Step 5: Testing chat context isolation...")
        
        # Test questions that should get different responses based on user's documents
        test_questions = [
            "What are our organization's main policies and procedures?",
            "What security measures do we have in place?",
            "What are our quality standards and protocols?"
        ]
        
        for question in test_questions:
            print(f"\n  Testing question: '{question}'")
            
            # Healthcare Admin asks question
            self.session.headers.update({"Authorization": f"Bearer {self.user1_token}"})
            response = self.session.post(f"{self.base_url}/chat/", json={"text": question})
            if response.status_code != 200:
                print(f"    ❌ Healthcare Admin chat failed: {response.status_code}")
                return False
            
            user1_response = response.json()["response"]
            print(f"    🏥 Healthcare Admin response: {user1_response[:100]}...")
            
            # Tech Admin asks same question
            self.session.headers.update({"Authorization": f"Bearer {self.user2_token}"})
            response = self.session.post(f"{self.base_url}/chat/", json={"text": question})
            if response.status_code != 200:
                print(f"    ❌ Tech Admin chat failed: {response.status_code}")
                return False
            
            user2_response = response.json()["response"]
            print(f"    💻 Tech Admin response: {user2_response[:100]}...")
            
            # Verify responses are different
            if user1_response == user2_response:
                print(f"    ❌ SECURITY BREACH: Both users got identical responses for '{question}'")
                return False
            
            # Verify responses reference appropriate content
            if "healthcare" in question.lower() or "medical" in question.lower():
                if "HIPAA" not in user1_response and "patient" not in user1_response:
                    print(f"    ❌ Healthcare Admin response doesn't reference healthcare content")
                    return False
            elif "tech" in question.lower() or "software" in question.lower():
                if "microservices" not in user2_response and "CI/CD" not in user2_response:
                    print(f"    ❌ Tech Admin response doesn't reference tech content")
                    return False
            
            print(f"    ✅ Chat isolation verified for '{question}'")
        
        return True

def main():
    tester = SecurityManualTester()
    success = tester.test_comprehensive_security()
    
    if success:
        print("\n🎯 Manual Testing Instructions:")
        print("1. Open test-ui.html in your browser")
        print("2. Login as Healthcare Admin with the credentials shown above")
        print("3. Upload a healthcare-related document")
        print("4. Search for 'HIPAA compliance' or 'patient privacy'")
        print("5. Ask chat: 'What are our healthcare policies?'")
        print("6. Repeat with Tech Admin and tech-related content")
        print("7. Verify that each user only sees their own documents and gets different responses")
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
