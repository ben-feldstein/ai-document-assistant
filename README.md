# AI Document Assistant

A production-ready, full-stack AI-powered document management and chat application that demonstrates enterprise-grade software architecture, scalable AI infrastructure, and modern DevOps practices.

## 🚀 Features

### Core Functionality
- **AI-Powered Document Chat**: Ask questions about uploaded documents and get intelligent responses
- **Multi-Format Document Support**: Upload and process PDFs, Word documents, text files, and Markdown
- **Smart Text Extraction**: Automatic text extraction from binary files using PyPDF2 and python-docx
- **Real-time Chat Interface**: Modern React-based chat UI with message history
- **Document Management**: Upload, preview, and organize documents with metadata tracking

### Technical Highlights
- **AI Infrastructure**: Production-ready AI pipeline with OpenAI integration and vector embeddings
- **Vector Search Engine**: Advanced semantic search using pgvector and PostgreSQL
- **Microservices Architecture**: Scalable Docker-based services with proper service discovery
- **Enterprise Security**: JWT authentication, role-based access control, and organization isolation
- **Real-time Processing**: WebSocket support for live chat interactions and document processing
- **Modern Frontend**: Responsive React/TypeScript UI with state management and real-time updates

## 🏗️ Architecture

### Backend (FastAPI + Python)
```
api/
├── routes/          # API endpoints (auth, chat, corpus, admin)
├── models/          # SQLAlchemy data models
├── services/        # Business logic and AI integration
└── utils/           # Helper functions and utilities
```

### Frontend (React + TypeScript)
```
modern-ui/
├── src/
│   ├── components/  # Reusable UI components
│   ├── pages/       # Main application pages
│   ├── contexts/    # React context providers
│   ├── lib/         # API client and utilities
│   └── hooks/       # Custom React hooks
```

### Infrastructure
```
infra/
├── docker-compose.yml    # Multi-service orchestration
├── Dockerfile.api        # Backend container
└── Dockerfile.worker     # Background processing
```

## 🛠️ Technology Stack

### Backend & AI Infrastructure
- **FastAPI**: High-performance async web framework with automatic API documentation
- **AI Pipeline**: OpenAI API integration with intelligent document processing and vector embeddings
- **Vector Database**: PostgreSQL + pgvector for production-grade semantic search and similarity matching
- **Document Processing**: PyPDF2 + python-docx for robust text extraction from multiple formats
- **Data Layer**: SQLAlchemy ORM with async support and connection pooling
- **Caching & Sessions**: Redis for high-performance caching and user session management
- **Security**: JWT-based authentication with refresh tokens and role-based access control

### Frontend
- **React 18**: Modern React with hooks and context
- **TypeScript**: Type-safe JavaScript development
- **Tailwind CSS**: Utility-first CSS framework
- **React Query**: Server state management
- **Vite**: Fast build tool and dev server
- **Lucide Icons**: Beautiful icon library

### DevOps & Infrastructure
- **Containerization**: Docker with multi-stage builds and optimized production images
- **Orchestration**: Docker Compose for local development and production deployment
- **Monitoring**: Prometheus metrics collection and Grafana dashboards
- **Database**: PostgreSQL with pgvector extension for vector operations
- **Caching**: Redis for session management and response caching
- **Reverse Proxy**: Nginx configuration for production load balancing and SSL termination
- **CI/CD**: GitHub Actions workflow for automated testing and deployment

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.12+ (for local development)

### Quick Start
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai-document-assistant
   ```

2. **Set up environment variables**
   ```bash
   cp env.template .env
   # Edit .env with your OpenAI API key and other settings
   ```

3. **Start the backend services**
   ```bash
   docker-compose -f infra/docker-compose.yml up -d
   ```

4. **Start the frontend**
   ```bash
   cd modern-ui
   npm install
   npm run dev
   ```

5. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📚 API Documentation

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/refresh` - Refresh JWT token

### Documents
- `GET /corpus/docs` - List documents
- `POST /corpus/upload` - Upload document
- `GET /corpus/doc/{id}/preview` - Preview document
- `GET /corpus/doc/{id}/download` - Download document
- `DELETE /corpus/doc/{id}` - Delete document

### Chat
- `POST /chat/` - Send chat message
- `GET /chat/history` - Get chat history
- `GET /chat/stats` - Get chat statistics

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: User roles (owner, admin, member)
- **Organization Isolation**: Users can only access their organization's data
- **Input Validation**: Comprehensive request validation using Pydantic
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Proper cross-origin resource sharing setup

## 🧪 Testing

```bash
# Backend tests
cd api
pytest

# Frontend tests
cd modern-ui
npm test
```

## 📊 Performance Features

- **Vector Embeddings**: Fast semantic search using pgvector
- **Redis Caching**: Response caching for improved performance
- **Connection Pooling**: Database connection optimization
- **Async Processing**: Non-blocking I/O operations
- **Background Workers**: Separate processing for heavy tasks

## 🚀 Deployment

### Production Setup
1. **Environment Configuration**
   - Set production environment variables
   - Configure SSL certificates
   - Set up production database

2. **Docker Production**
   ```bash
   docker-compose -f infra/docker-compose.prod.yml up -d
   ```

3. **Nginx Configuration**
   - Reverse proxy setup
   - SSL termination
   - Static file serving

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Project Goals

This project demonstrates:
- **AI Infrastructure Engineering**: Production-ready AI pipeline with vector embeddings and semantic search
- **Enterprise Architecture**: Scalable microservices with proper service discovery and monitoring
- **Full-Stack Development**: Complete application from database to UI with modern patterns
- **DevOps Excellence**: Containerization, monitoring, CI/CD, and cloud-ready deployment
- **Security Best Practices**: Authentication, authorization, and data protection
- **Performance Optimization**: Caching, async processing, and database optimization
- **Code Quality**: Type safety, testing, and clean architecture patterns

## 🤖 AI Infrastructure Deep Dive

### Vector Embeddings & Semantic Search
- **Document Processing Pipeline**: Automatic text extraction from PDFs, Word docs, and other formats
- **Vector Generation**: OpenAI embeddings for semantic understanding of document content
- **Similarity Search**: pgvector-powered similarity matching for intelligent document retrieval
- **Context-Aware Chat**: AI responses based on document content and conversation history

### AI Integration Architecture
- **API Abstraction**: Clean separation between AI providers for easy switching
- **Response Caching**: Intelligent caching of AI responses to reduce API costs
- **Error Handling**: Robust error handling for AI service failures
- **Rate Limiting**: Built-in rate limiting to manage API usage and costs

### Performance & Scalability
- **Async Processing**: Non-blocking AI operations for better user experience
- **Background Workers**: Separate processing queues for heavy AI tasks
- **Connection Pooling**: Optimized database connections for vector operations
- **Memory Management**: Efficient handling of large documents and embeddings

## 🚀 Roadmap & Next Steps

### Phase 1: Cloud Deployment (Next 2-4 weeks)
- [ ] **AWS/Azure/GCP Deployment**: Production-ready cloud infrastructure
- [ ] **Auto-scaling**: Kubernetes or ECS deployment with auto-scaling
- [ ] **CDN Integration**: CloudFront/Cloud CDN for global performance
- [ ] **SSL & Domain**: Production domain with Let's Encrypt certificates
- [ ] **Backup Strategy**: Automated database backups and disaster recovery

### Phase 2: Self-Hosted LLM Integration (Next 1-2 months)
- [ ] **Local LLM Support**: Integration with Ollama, Llama2, or similar
- [ ] **Model Switching**: Easy toggle between OpenAI and self-hosted models
- [ ] **Custom Fine-tuning**: Domain-specific model training capabilities
- [ ] **Model Management**: UI for managing multiple AI models
- [ ] **Cost Optimization**: Hybrid approach using local models for basic tasks

### Phase 3: Advanced AI Features (Next 2-3 months)
- [ ] **Multi-Modal AI**: Image and document OCR capabilities
- [ ] **Advanced RAG**: Retrieval-Augmented Generation with better context
- [ ] **Conversation Memory**: Long-term conversation context and learning
- [ ] **AI Agents**: Autonomous document analysis and summarization
- [ ] **Custom Workflows**: User-defined AI processing pipelines

### Phase 4: Enterprise Features (Next 3-6 months)
- [ ] **Multi-Tenancy**: Advanced organization and user management
- [ ] **API Gateway**: Rate limiting, authentication, and usage analytics
- [ ] **Advanced Analytics**: AI usage metrics and cost optimization
- [ ] **Integration APIs**: Webhook support and third-party integrations
- [ ] **Compliance**: GDPR, SOC2, and enterprise security features

## 🌟 Why This Project Stands Out

### For Developers
- **Production-Ready Code**: Not just a demo - this is enterprise-grade software
- **Modern Stack**: Latest technologies and best practices throughout
- **Comprehensive Testing**: Full test suite with CI/CD integration
- **Clean Architecture**: Well-structured, maintainable codebase

### For Employers
- **AI Infrastructure Skills**: Demonstrates real-world AI/ML implementation
- **DevOps Expertise**: Shows ability to build and deploy complex systems
- **Full-Stack Capability**: End-to-end application development skills
- **Security Awareness**: Proper authentication, authorization, and data protection
- **Scalability Focus**: Architecture designed for growth and performance

---

**Built with modern web technologies and AI infrastructure best practices**

---

*This project demonstrates production-ready AI infrastructure, scalable architecture, and enterprise-grade development practices. Perfect for showcasing advanced technical skills to potential employers.*
