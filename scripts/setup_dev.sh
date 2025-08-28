#!/bin/bash

# Development Setup Script
# Sets up the project for local development with mock services

echo "🚀 Setting up AI Document Assistant for development..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] && [ ! -f "infra/docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create mock environment file
echo "📝 Creating mock environment file..."
if [ ! -f ".env" ]; then
    cp env.mock .env
    echo "✅ Created .env from env.mock"
else
    echo "⚠️  .env already exists, skipping..."
fi

# Set mock mode environment variables
export MOCK_MODE=true
export MOCK_AI_RESPONSES=true
export MOCK_DOCUMENT_PROCESSING=true

echo "🔧 Environment configured for mock mode:"
echo "   MOCK_MODE=true"
echo "   MOCK_AI_RESPONSES=true"
echo "   MOCK_DOCUMENT_PROCESSING=true"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "🐳 Starting services with mock configuration..."
cd infra
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎉 Development setup complete!"
echo ""
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🗄️  Database: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo ""
echo "🔒 Mock Mode: ENABLED"
echo "   - No real API keys required"
echo "   - Mock AI responses"
echo "   - Mock document processing"
echo "   - Safe for GitHub pushing"
echo ""
echo "💡 To start the frontend:"
echo "   cd modern-ui && npm run dev"
echo ""
echo "🔄 To disable mock mode, edit .env and set:"
echo "   MOCK_MODE=false"
echo "   MOCK_AI_RESPONSES=false"
echo "   MOCK_DOCUMENT_PROCESSING=false"
