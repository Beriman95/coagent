#!/bin/bash
# CoAgent Setup Script

echo "🚀 CoAgent Setup"
echo "================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment template
if [ ! -f .env ]; then
    echo ""
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "✅ .env created - PLEASE EDIT IT WITH YOUR CREDENTIALS!"
else
    echo ""
    echo "⚠️  .env already exists, skipping..."
fi

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p chroma_db
mkdir -p logs

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'source .venv/bin/activate' to activate virtual environment"
echo "3. Run 'python mvp/coagent_mvp.py' to start CoAgent"
echo "4. Run 'python admin/app.py' to start Admin UI"
echo ""
