#!/bin/bash

# AI Voice Policy Assistant - Complete Setup Script
# This script will install all necessary dependencies and set up your environment

set -e  # Exit on any error

echo "🚀 AI Voice Policy Assistant - Complete Setup Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            echo "ubuntu"
        elif command_exists yum; then
            echo "centos"
        elif command_exists dnf; then
            echo "fedora"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Function to install Docker on macOS
install_docker_macos() {
    print_status "Installing Docker Desktop for macOS..."
    
    if ! command_exists brew; then
        print_status "Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    if ! command_exists docker; then
        print_status "Installing Docker Desktop via Homebrew..."
        brew install --cask docker
        print_warning "Docker Desktop has been installed. Please start it from Applications and ensure it's running."
        print_warning "You may need to log out and back in, or restart your computer."
        read -p "Press Enter after Docker Desktop is running..."
    fi
}

# Function to install Docker on Ubuntu/Debian
install_docker_ubuntu() {
    print_status "Installing Docker on Ubuntu/Debian..."
    
    # Update package index
    sudo apt-get update
    
    # Install prerequisites
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    print_warning "Docker has been installed. You may need to log out and back in for group changes to take effect."
}

# Function to install Docker on CentOS/RHEL/Fedora
install_docker_centos() {
    print_status "Installing Docker on CentOS/RHEL/Fedora..."
    
    if command_exists dnf; then
        # Fedora
        sudo dnf -y install dnf-plugins-core
        sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
        sudo dnf -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
    else
        # CentOS/RHEL
        sudo yum install -y yum-utils
        sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo yum -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
    fi
    
    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    print_warning "Docker has been installed. You may need to log out and back in for group changes to take effect."
}

# Function to install Docker
install_docker() {
    local os=$(detect_os)
    
    if command_exists docker; then
        print_success "Docker is already installed"
        return
    fi
    
    case $os in
        "macos")
            install_docker_macos
            ;;
        "ubuntu")
            install_docker_ubuntu
            ;;
        "centos"|"fedora")
            install_docker_centos
            ;;
        *)
            print_error "Unsupported operating system: $os"
            print_error "Please install Docker manually from https://docs.docker.com/get-docker/"
            exit 1
            ;;
    esac
}

# Function to install Docker Compose
install_docker_compose() {
    if command_exists docker-compose; then
        print_success "Docker Compose is already installed"
        return
    fi
    
    if command_exists docker && docker compose version >/dev/null 2>&1; then
        print_success "Docker Compose plugin is available"
        return
    fi
    
    print_status "Installing Docker Compose..."
    
    # Install Docker Compose plugin
    if command_exists docker; then
        # Try to install via Docker's plugin system
        if docker compose version >/dev/null 2>&1; then
            print_success "Docker Compose plugin is working"
        else
            print_warning "Docker Compose plugin not available, installing standalone version..."
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
    else
        print_error "Docker must be installed before Docker Compose"
        exit 1
    fi
}

# Function to check Python version
check_python() {
    if command_exists python3; then
        local version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
        local major=$(echo $version | cut -d. -f1)
        local minor=$(echo $version | cut -d. -f2)
        
        if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
            print_success "Python $version is compatible"
            return 0
        else
            print_error "Python $version is not compatible. Need Python 3.11+"
            return 1
        fi
    else
        print_error "Python 3.11+ is not installed"
        return 1
    fi
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Setting up Python virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
}

# Function to create environment file
setup_env() {
    if [ ! -f ".env" ]; then
        print_status "Creating .env file from template..."
        cp env.template .env
        
        # Generate JWT secret
        local jwt_secret=$(openssl rand -base64 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        
        # Update JWT secret in .env file
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/JWT_SECRET=.*/JWT_SECRET=$jwt_secret/" .env
        else
            # Linux
            sed -i "s/JWT_SECRET=.*/JWT_SECRET=$jwt_secret/" .env
        fi
        
        print_success ".env file created with generated JWT secret"
        print_warning "Please edit .env file and add your OpenAI API key: OPENAI_API_KEY=your_key_here"
    else
        print_status ".env file already exists"
    fi
}

# Function to verify Docker is running
verify_docker() {
    print_status "Verifying Docker is running..."
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop (macOS) or Docker service (Linux)"
        print_error "On Linux, you may need to log out and back in after installation"
        exit 1
    fi
    
    print_success "Docker is running"
}

# Function to test the setup
test_setup() {
    print_status "Testing the setup..."
    
    # Test Docker
    if docker --version >/dev/null 2>&1; then
        print_success "✓ Docker is working"
    else
        print_error "✗ Docker is not working"
        return 1
    fi
    
    # Test Docker Compose
    if docker-compose --version >/dev/null 2>&1 || docker compose version >/dev/null 2>&1; then
        print_success "✓ Docker Compose is working"
    else
        print_error "✗ Docker Compose is not working"
        return 1
    fi
    
    # Test Python virtual environment
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        print_success "✓ Python virtual environment is ready"
    else
        print_error "✗ Python virtual environment is not ready"
        return 1
    fi
    
    print_success "Setup verification completed successfully!"
}

# Function to show next steps
show_next_steps() {
    echo ""
    echo "🎉 Setup completed successfully!"
    echo "=================================="
    echo ""
    echo "Next steps:"
    echo "1. Edit your .env file and add your OpenAI API key:"
    echo "   nano .env"
    echo "   # Set: OPENAI_API_KEY=your_actual_api_key_here"
    echo ""
    echo "2. Start the AI Voice Policy Assistant:"
    echo "   make up"
    echo ""
    echo "3. Access the services:"
    echo "   - API: http://localhost:8000"
    echo "   - Voice Interface: http://localhost:8000/ws/audio"
    echo "   - Grafana: http://localhost:3000 (admin/admin)"
    echo "   - API Docs: http://localhost:8000/docs"
    echo ""
    echo "4. To stop everything:"
    echo "   make down"
    echo ""
    echo "5. For development mode:"
    echo "   make dev"
    echo ""
    echo "Need help? Check the README.md file or run 'make help'"
}

# Main execution
main() {
    echo "Starting setup process..."
    echo ""
    
    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -f "requirements.txt" ]; then
        print_error "Please run this script from the ai-document-assistant directory"
        exit 1
    fi
    
    # Install Docker
    install_docker
    
    # Install Docker Compose
    install_docker_compose
    
    # Verify Docker is running
    verify_docker
    
    # Check Python
    if ! check_python; then
        print_error "Please install Python 3.11+ and run this script again"
        exit 1
    fi
    
    # Install Python dependencies
    install_python_deps
    
    # Setup environment
    setup_env
    
    # Test setup
    test_setup
    
    # Show next steps
    show_next_steps
}

# Run main function
main "$@"
