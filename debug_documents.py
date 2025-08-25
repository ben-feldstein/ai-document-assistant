#!/usr/bin/env python3
"""
Debug script to troubleshoot document processing and search issues.
"""

import requests
import json
import time

class DocumentDebugger:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        
    def login(self, email: str, password: str) -> bool:
        """Login and get token."""
        login_data = {"email": email, "password": password}
        response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print(f"✅ Logged in as {email}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def upload_test_document(self, title: str, text: str, source: str = "internal") -> bool:
        """Upload a test document."""
        doc_data = {
            "title": title,
            "text": text,
            "source": source,
            "metadata": {"test": True, "timestamp": time.time()}
        }
        
        response = self.session.post(f"{self.base_url}/corpus/doc", json=doc_data)
        
        if response.status_code in [200, 201]:
            doc_id = response.json()["id"]
            print(f"✅ Document uploaded: {title} (ID: {doc_id})")
            return True
        else:
            print(f"❌ Document upload failed: {response.status_code} - {response.text}")
            return False
    
    def search_documents(self, query: str) -> bool:
        """Search for documents."""
        search_data = {"query": query, "k": 10}
        
        response = self.session.post(f"{self.base_url}/corpus/search", json=search_data)
        
        if response.status_code == 200:
            results = response.json()["results"]
            print(f"✅ Search successful for '{query}': {len(results)} results")
            
            for i, result in enumerate(results[:3]):  # Show first 3 results
                print(f"  Result {i+1}: {result.get('title', 'No title')}")
                print(f"    Snippet: {result.get('snippet', 'No snippet')[:100]}...")
                print(f"    Score: {result.get('score', 'No score')}")
                print()
            return True
        else:
            print(f"❌ Search failed: {response.status_code} - {response.text}")
            return False
    
    def list_documents(self) -> bool:
        """List all documents."""
        response = self.session.get(f"{self.base_url}/corpus/docs")
        
        if response.status_code == 200:
            docs = response.json()
            print(f"✅ Document list: {len(docs)} documents")
            
            for doc in docs:
                print(f"  - {doc.get('title', 'No title')} (ID: {doc.get('id', 'No ID')})")
                print(f"    Text: {doc.get('text', 'No text')[:50]}...")
                print()
            return True
        else:
            print(f"❌ Document list failed: {response.status_code} - {response.text}")
            return False
    
    def test_chat(self, question: str) -> bool:
        """Test chat functionality."""
        chat_data = {"text": question}
        
        response = self.session.post(f"{self.base_url}/chat/", json=chat_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat successful")
            print(f"  Question: {question}")
            print(f"  Response: {result.get('response', 'No response')[:200]}...")
            print(f"  Sources: {len(result.get('sources', []))} sources")
            return True
        else:
            print(f"❌ Chat failed: {response.status_code} - {response.text}")
            return False

def main():
    debugger = DocumentDebugger()
    
    print("🔍 Document Processing Debug Tool")
    print("=" * 50)
    
    # Test with a known user (from test_api.py)
    if not debugger.login("test@example.com", "testpassword123"):
        print("❌ Cannot proceed without login")
        return
    
    print("\n📄 Testing Document Operations...")
    
    # List existing documents
    print("\n1. Listing existing documents:")
    debugger.list_documents()
    
    # Upload a substantial test document
    print("\n2. Uploading substantial test document:")
    test_doc = {
        "title": "Comprehensive Company Policy Handbook",
        "text": """This comprehensive company policy handbook contains detailed information about our organization's policies and procedures. It covers employee conduct guidelines, workplace safety protocols, data security policies, company benefits, remote work policies, expense reimbursement procedures, professional development opportunities, and much more. This document is confidential and contains proprietary information specific to our company. It should not be shared with external parties or competitors. The handbook is regularly updated to reflect current best practices and legal requirements.""",
        "source": "internal"
    }
    debugger.upload_test_document(**test_doc)
    
    # Wait a moment for processing
    print("\n⏳ Waiting for document processing...")
    time.sleep(2)
    
    # List documents again
    print("\n3. Listing documents after upload:")
    debugger.list_documents()
    
    # Test search with specific terms
    print("\n4. Testing search functionality:")
    search_queries = [
        "company policy handbook",
        "employee conduct guidelines", 
        "workplace safety protocols",
        "data security policies"
    ]
    
    for query in search_queries:
        print(f"\nSearching for: '{query}'")
        debugger.search_documents(query)
    
    # Test chat functionality
    print("\n5. Testing chat functionality:")
    chat_questions = [
        "What does the company policy handbook contain?",
        "What are the employee conduct guidelines?",
        "What safety protocols are mentioned?"
    ]
    
    for question in chat_questions:
        print(f"\nAsking: '{question}'")
        debugger.test_chat(question)

if __name__ == "__main__":
    main()
