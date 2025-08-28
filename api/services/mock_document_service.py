"""
Mock Document Processing Service for Development and Testing
Simulates document processing without requiring real file uploads
"""

import random
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta

class MockDocumentService:
    """Mock document service for development and testing"""
    
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self.documents = []
        self.document_counter = 1
        
        # Initialize with some mock documents
        self._initialize_mock_documents()
    
    def _initialize_mock_documents(self):
        """Initialize with sample mock documents"""
        sample_docs = [
            {
                "filename": "sample_report.pdf",
                "title": "Sample Business Report",
                "file_size": 2048000,
                "content": "This is a comprehensive business report covering Q4 performance metrics, strategic initiatives, and future planning considerations.",
                "file_type": "pdf"
            },
            {
                "filename": "technical_specs.docx",
                "title": "Technical Specifications Document",
                "file_size": 1536000,
                "content": "Technical specifications for the new system architecture including database design, API endpoints, and deployment procedures.",
                "file_type": "docx"
            },
            {
                "filename": "project_plan.md",
                "title": "Project Implementation Plan",
                "file_size": 512000,
                "content": "Detailed project plan with timelines, milestones, resource allocation, and risk assessment.",
                "file_type": "md"
            }
        ]
        
        for doc in sample_docs:
            self.documents.append({
                "id": self.document_counter,
                "filename": doc["filename"],
                "title": doc["title"],
                "file_size": doc["file_size"],
                "content": doc["content"],
                "file_type": doc["file_type"],
                "upload_date": datetime.now() - timedelta(days=random.randint(1, 30)),
                "organization_id": 1,
                "user_id": 1,
                "status": "processed"
            })
            self.document_counter += 1
    
    def upload_document(self, filename: str, file_content: bytes = None, **kwargs) -> Dict[str, Any]:
        """Mock document upload"""
        if not self.mock_mode:
            raise Exception("Mock service is disabled")
        
        # Simulate processing time
        time.sleep(random.uniform(1.0, 3.0))
        
        # Generate mock document data
        file_size = random.randint(100000, 5000000)
        file_type = filename.split('.')[-1] if '.' in filename else 'txt'
        
        # Mock content based on file type
        content_templates = {
            "pdf": "This is a mock PDF document content for development purposes. It contains sample text that would normally be extracted from a real PDF file.",
            "docx": "Mock Word document content. This simulates the text that would be extracted from a real .docx file during processing.",
            "txt": "Plain text document content for testing. This represents the extracted text from a simple text file.",
            "md": "# Mock Markdown Document\n\nThis is a sample markdown file with various formatting elements for testing purposes."
        }
        
        content = content_templates.get(file_type, "Mock document content for development and testing.")
        
        # Create new document
        new_doc = {
            "id": self.document_counter,
            "filename": filename,
            "title": filename.replace(f".{file_type}", "").replace("_", " ").title(),
            "file_size": file_size,
            "content": content,
            "file_type": file_type,
            "upload_date": datetime.now(),
            "organization_id": kwargs.get("organization_id", 1),
            "user_id": kwargs.get("user_id", 1),
            "status": "processed"
        }
        
        self.documents.append(new_doc)
        self.document_counter += 1
        
        return {
            "message": "Document uploaded successfully",
            "document_id": new_doc["id"],
            "filename": filename,
            "file_size": file_size,
            "processing_time_ms": random.randint(1000, 3000)
        }
    
    def get_documents(self, organization_id: int = 1, **kwargs) -> Dict[str, Any]:
        """Get mock documents"""
        if not self.mock_mode:
            raise Exception("Mock service is disabled")
        
        # Filter by organization
        org_docs = [doc for doc in self.documents if doc["organization_id"] == organization_id]
        
        return {
            "documents": org_docs,
            "total": len(org_docs)
        }
    
    def get_document(self, document_id: int, **kwargs) -> Dict[str, Any]:
        """Get specific mock document"""
        if not self.mock_mode:
            raise Exception("Mock service is disabled")
        
        doc = next((d for d in self.documents if d["id"] == document_id), None)
        if not doc:
            raise Exception("Document not found")
        
        return doc
    
    def delete_document(self, document_id: int, **kwargs) -> Dict[str, Any]:
        """Delete mock document"""
        if not self.mock_mode:
            raise Exception("Mock service is disabled")
        
        doc = next((d for d in self.documents if d["id"] == document_id), None)
        if not doc:
            raise Exception("Document not found")
        
        self.documents.remove(doc)
        
        return {
            "message": "Document deleted successfully",
            "document_id": document_id
        }
    
    def search_documents(self, query: str, organization_id: int = 1, **kwargs) -> List[Dict[str, Any]]:
        """Mock document search"""
        if not self.mock_mode:
            raise Exception("Mock service is disabled")
        
        # Simple mock search
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            if doc["organization_id"] == organization_id:
                if (query_lower in doc["title"].lower() or 
                    query_lower in doc["content"].lower() or
                    query_lower in doc["filename"].lower()):
                    results.append(doc)
        
        return results
    
    def get_document_stats(self, organization_id: int = 1) -> Dict[str, Any]:
        """Get mock document statistics"""
        if not self.mock_mode:
            raise Exception("Mock service is disabled")
        
        org_docs = [doc for doc in self.documents if doc["organization_id"] == organization_id]
        
        total_size = sum(doc["file_size"] for doc in org_docs)
        file_types = {}
        
        for doc in org_docs:
            file_type = doc["file_type"]
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        return {
            "total_documents": len(org_docs),
            "total_size_bytes": total_size,
            "file_type_distribution": file_types,
            "average_file_size": total_size // len(org_docs) if org_docs else 0
        }

# Mock document templates for testing
MOCK_DOCUMENT_TEMPLATES = {
    "business_report": {
        "filename": "business_report_2024.pdf",
        "title": "Business Report 2024",
        "content": "Annual business report covering financial performance, strategic initiatives, and market analysis.",
        "file_type": "pdf"
    },
    "technical_doc": {
        "filename": "system_architecture.docx",
        "title": "System Architecture Documentation",
        "content": "Comprehensive documentation of system architecture including database design, API specifications, and deployment procedures.",
        "file_type": "docx"
    },
    "project_plan": {
        "filename": "project_roadmap.md",
        "title": "Project Roadmap",
        "content": "# Project Roadmap\n\n## Phase 1: Foundation\n- Database setup\n- API development\n\n## Phase 2: Features\n- User interface\n- Testing\n\n## Phase 3: Deployment\n- Production setup\n- Monitoring",
        "file_type": "md"
    }
}
