#!/bin/bash

# Quick fix for setuptools issues in virtual environment

echo "🔧 Fixing setuptools issue..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run install_deps.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "Installing essential build tools..."
pip install --upgrade pip setuptools wheel

echo "✅ Build tools installed. Now trying to install requirements..."

# Try installing requirements again
pip install -r requirements.txt

echo "🎉 Dependencies should now be installed successfully!"
echo ""
echo "To activate the virtual environment in the future:"
echo "source venv/bin/activate"
