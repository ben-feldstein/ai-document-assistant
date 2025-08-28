"""
Mock AI Service for Development and Testing
Provides fake AI responses without requiring real API keys
"""

import random
import time
from typing import List, Dict, Any
import json

class MockAIService:
    """Mock AI service that simulates OpenAI API responses"""
    
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self.conversation_history = []
        
        # Mock responses for different types of questions
        self.mock_responses = {
            "document": [
                "Based on the document content, I can see that this appears to be a comprehensive analysis covering multiple key areas. The main points include strategic planning, resource allocation, and performance metrics.",
                "The document outlines several important considerations for project management. Key highlights include timeline constraints, budget requirements, and stakeholder expectations.",
                "From reviewing this document, I've identified several critical insights about organizational structure and operational procedures."
            ],
            "general": [
                "I'd be happy to help you with that question. Could you provide more context about what you're looking for?",
                "That's an interesting topic. Let me break down the key concepts and provide some insights.",
                "I understand your question. Here are some relevant points to consider based on the available information."
            ],
            "technical": [
                "From a technical perspective, this involves several key components including data processing, API integration, and system architecture considerations.",
                "The technical implementation requires careful attention to performance optimization, error handling, and scalability factors.",
                "This technical challenge can be approached through multiple methodologies, each with their own trade-offs and benefits."
            ]
        }
    
    def generate_chat_response(self, message: str, context: str = "", **kwargs) -> Dict[str, Any]:
        """Generate a mock chat response"""
        if not self.mock_mode:
            raise Exception("Mock service is disabled")
        
        # Simulate processing time
        time.sleep(random.uniform(0.5, 2.0))
        
        # Determine response type based on message content
        response_type = self._classify_message(message)
        response_text = random.choice(self.mock_responses[response_type])
        
        # Add some context if provided
        if context:
            response_text += f" Regarding the document content: {context[:100]}..."
        
        # Generate mock metadata
        mock_response = {
            "response": response_text,
            "model": "gpt-4-mock",
            "usage": {
                "prompt_tokens": random.randint(50, 200),
                "completion_tokens": random.randint(30, 150),
                "total_tokens": random.randint(80, 350)
            },
            "cached": False,
            "latency_ms": random.randint(500, 2000)
        }
        
        # Store in conversation history
        self.conversation_history.append({
            "user": message,
            "assistant": response_text,
            "timestamp": time.time()
        })
        
        return mock_response
    
    def generate_embeddings(self, text: str, **kwargs) -> List[float]:
        """Generate mock embeddings (random vectors)"""
        if not self.mock_mode:
            raise Exception("Mock service is disabled")
        
        # Generate random embedding vector (1536 dimensions like OpenAI)
        embedding = [random.uniform(-1, 1) for _ in range(1536)]
        
        # Normalize the vector
        magnitude = sum(x*x for x in embedding) ** 0.5
        normalized_embedding = [x/magnitude for x in embedding]
        
        return normalized_embedding
    
    def _classify_message(self, message: str) -> str:
        """Classify message type for appropriate mock response"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["document", "file", "content", "text"]):
            return "document"
        elif any(word in message_lower for word in ["technical", "code", "implementation", "architecture"]):
            return "technical"
        else:
            return "general"
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get stored conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

# Mock response templates for different scenarios
MOCK_RESPONSES = {
    "upload_success": {
        "message": "Document uploaded successfully",
        "document_id": 12345,
        "filename": "sample_document.pdf",
        "file_size": 1024000,
        "processing_time_ms": 1500
    },
    "chat_response": {
        "response": "This is a mock AI response for development purposes. The actual response would be generated by OpenAI's API.",
        "model": "gpt-4-mock",
        "usage": {"prompt_tokens": 150, "completion_tokens": 100, "total_tokens": 250},
        "cached": False,
        "latency_ms": 1200
    },
    "document_list": {
        "documents": [
            {
                "id": 1,
                "filename": "sample_report.pdf",
                "title": "Sample Report",
                "file_size": 2048000,
                "upload_date": "2024-01-15T10:30:00Z",
                "organization_id": 1
            },
            {
                "id": 2,
                "filename": "technical_specs.docx",
                "title": "Technical Specifications",
                "file_size": 1536000,
                "upload_date": "2024-01-14T14:20:00Z",
                "organization_id": 1
            }
        ],
        "total": 2
    }
}
