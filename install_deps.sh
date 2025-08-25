#!/bin/bash

# AI Voice Policy Assistant - Python Dependencies Installer
# This script sets up Python virtual environment and installs dependencies

set -e

echo "🐍 AI Voice Policy Assistant - Python Dependencies Setup"
echo "========================================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this script from the ai-document-assistant directory"
    exit 1
fi

# Check Python version
print_status "Checking Python version..."
if ! python3 --version >/dev/null 2>&1; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "✓ Found Python $PYTHON_VERSION"

# Check if Python version is compatible
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "❌ Python $PYTHON_VERSION is not compatible. Need Python 3.11+"
    exit 1
fi

# Handle Python 3.12 specific issues
if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -eq 12 ]; then
    print_warning "Python 3.12 detected. Using compatible requirements..."
    if [ -f "requirements-py312.txt" ]; then
        print_status "Using Python 3.12 specific requirements..."
        REQ_FILE="requirements-py312.txt"
    else
        print_warning "Python 3.12 specific requirements not found, using standard requirements..."
        REQ_FILE="requirements.txt"
    fi
else
    REQ_FILE="requirements.txt"
fi

# Remove existing virtual environment if it exists
if [ -d "venv" ]; then
    print_status "Removing existing virtual environment..."
    rm -rf venv
fi

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
print_success "Virtual environment created"

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install essential build tools first
print_status "Installing essential build tools..."
pip install --upgrade pip setuptools wheel

# Install numpy first (to avoid compatibility issues)
print_status "Installing numpy first for compatibility..."
pip install "numpy>=1.26.0"

# Install core dependencies first (avoiding problematic ones)
print_status "Installing core dependencies first..."
pip install fastapi uvicorn[standard] websockets python-multipart
pip install sqlmodel sqlalchemy python-dotenv
pip install redis aioredis
pip install httpx openai
pip install sentence-transformers
pip install openai-whisper
pip install opentelemetry-api opentelemetry-sdk
pip install prometheus-client
pip install pybreaker slowapi
pip install pytest pytest-asyncio
pip install ruff mypy
pip install pydantic pydantic-settings python-dateutil

# Try to install psycopg2-binary (PostgreSQL adapter)
print_status "Installing PostgreSQL adapter..."
if ! pip install psycopg2-binary; then
    print_warning "psycopg2-binary failed to install. Trying alternative..."
    if ! pip install psycopg2; then
        print_warning "psycopg2 also failed. This may cause database connection issues."
        print_warning "You may need to install PostgreSQL development headers:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "  brew install postgresql"
        else
            echo "  sudo apt-get install libpq-dev python3-dev"
        fi
    fi
fi

# Try to install pgvector (vector extension)
print_status "Installing pgvector..."
if ! pip install pgvector; then
    print_warning "pgvector failed to install. This may cause vector search issues."
fi

# Try to install alembic (database migrations)
print_status "Installing alembic..."
if ! pip install alembic; then
    print_warning "alembic failed to install. This may cause database migration issues."
fi

# Try to install opentelemetry instrumentations
print_status "Installing OpenTelemetry instrumentations..."
pip install opentelemetry-instrumentation-fastapi || print_warning "FastAPI instrumentation failed"
pip install opentelemetry-instrumentation-sqlalchemy || print_warning "SQLAlchemy instrumentation failed"
pip install opentelemetry-instrumentation-redis || print_warning "Redis instrumentation failed"

print_success "Core dependencies installed successfully!"

# Setup environment file
print_status "Setting up environment file..."
if [ ! -f ".env" ]; then
    cp env.template .env
    
    # Generate JWT secret
    if command -v openssl >/dev/null 2>&1; then
        JWT_SECRET=$(openssl rand -base64 32)
    else
        JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    fi
    
    # Update JWT secret in .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
    else
        sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
    fi
    
    print_success ".env file created with generated JWT secret"
else
    print_status ".env file already exists"
fi

echo ""
echo "🎉 Python setup completed!"
echo "=========================="
echo ""
echo "Next steps:"
echo "1. Edit your .env file and add your OpenAI API key:"
echo "   nano .env"
echo "   # Set: OPENAI_API_KEY=your_actual_api_key_here"
echo ""
echo "2. Make sure Docker and Docker Compose are installed and running"
echo ""
echo "3. Start the AI Voice Policy Assistant:"
echo "   make up"
echo ""
echo "4. To activate the virtual environment in the future:"
echo "   source venv/bin/activate"
echo ""
echo "Note: Some packages may have failed to install due to system dependencies."
echo "If you encounter issues, you may need to install system packages:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  brew install postgresql"
else
    echo "  sudo apt-get install libpq-dev python3-dev build-essential"
fi
echo ""
echo "Need help? Check the README.md file or run 'make help'"
