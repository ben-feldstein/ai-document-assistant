# 🎭 Mock Mode for Development and Testing

## Overview

Mock Mode allows you to develop and test the AI Document Assistant without requiring real API keys or external services. This makes development safer and GitHub pushes secure.

## 🚀 Quick Start

### 1. Setup Mock Environment
```bash
# Run the development setup script
./scripts/setup_dev.sh

# Or manually copy the mock environment
cp env.mock .env
```

### 2. Start Services
```bash
cd infra
docker-compose up -d
```

### 3. Start Frontend
```bash
cd modern-ui
npm run dev
```

## 🔧 Mock Mode Features

### AI Service Mocking
- **Chat Responses**: Generates realistic AI responses without OpenAI API calls
- **Embeddings**: Creates mock vector embeddings for testing
- **Response Metadata**: Simulates token usage, latency, and caching
- **Conversation History**: Maintains chat context for testing

### Document Processing Mocking
- **File Uploads**: Simulates document processing without real file handling
- **Text Extraction**: Provides mock content for different file types
- **Document Management**: Full CRUD operations with mock data
- **Search Functionality**: Mock semantic search capabilities

### Sample Data
The mock services include sample documents:
- Business reports (PDF)
- Technical specifications (Word)
- Project plans (Markdown)

## 🌍 Environment Variables

| Variable | Mock Value | Description |
|----------|------------|-------------|
| `MOCK_MODE` | `true` | Enable/disable mock mode |
| `MOCK_AI_RESPONSES` | `true` | Use mock AI responses |
| `MOCK_DOCUMENT_PROCESSING` | `true` | Use mock document processing |
| `OPENAI_API_KEY` | `sk-mock-...` | Mock API key (safe for GitHub) |
| `JWT_SECRET` | `mock-jwt-secret...` | Mock JWT secret (safe for GitHub) |

## 🔄 Switching Between Mock and Real

### Enable Mock Mode (Development)
```bash
export MOCK_MODE=true
export MOCK_AI_RESPONSES=true
export MOCK_DOCUMENT_PROCESSING=true
```

### Disable Mock Mode (Production)
```bash
export MOCK_MODE=false
export MOCK_AI_RESPONSES=false
export MOCK_DOCUMENT_PROCESSING=false
# Set real API keys in .env
```

## 🧪 Testing with Mock Mode

### Test AI Chat
```bash
# Mock responses will be generated automatically
curl -X POST "http://localhost:8000/chat/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "What can you tell me about the documents?"}'
```

### Test Document Upload
```bash
# Mock document processing will simulate file handling
curl -X POST "http://localhost:8000/corpus/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@sample.pdf"
```

## 🚨 Security Benefits

### Safe for GitHub
- ✅ No real API keys in code
- ✅ No real secrets in configuration
- ✅ Mock data for testing
- ✅ Safe environment variables

### Development Workflow
1. **Local Development**: Use mock mode with `env.mock`
2. **Testing**: Verify functionality without external dependencies
3. **GitHub Push**: Safe to commit mock configuration
4. **Production**: Switch to real services with real keys

## 🔍 Mock Service Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Frontend      │    │   Backend API    │    │   Mock Services  │
│                 │◄──►│                  │◄──►│                  │
│ - React UI      │    │ - FastAPI        │    │ - MockAIService  │
│ - Chat Interface│    │ - Chat Routes    │    │ - MockDocument   │
│ - Document Mgmt │    │ - Document Routes│    │ - Mock Responses │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

## 📝 Customizing Mock Responses

### AI Service Customization
Edit `api/services/mock_ai_service.py`:
```python
# Add new response types
self.mock_responses["custom"] = [
    "Custom mock response 1",
    "Custom mock response 2"
]

# Customize response generation
def generate_chat_response(self, message: str, **kwargs):
    # Your custom logic here
    pass
```

### Document Service Customization
Edit `api/services/mock_document_service.py`:
```python
# Add new document templates
MOCK_DOCUMENT_TEMPLATES["custom_doc"] = {
    "filename": "custom.txt",
    "title": "Custom Document",
    "content": "Custom content here",
    "file_type": "txt"
}
```

## 🎯 Best Practices

1. **Always use mock mode for development**
2. **Test with mock data before production**
3. **Keep mock responses realistic**
4. **Use environment variables for configuration**
5. **Never commit real API keys**
6. **Test both mock and real modes**

## 🚀 Next Steps

- [ ] Test mock mode functionality
- [ ] Customize mock responses for your use case
- [ ] Set up CI/CD with mock mode for testing
- [ ] Prepare production configuration
- [ ] Deploy with real services

---

**Mock Mode makes development safe, fast, and GitHub-friendly! 🎭✨**
