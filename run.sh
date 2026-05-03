#!/bin/bash

# PR Review Automation System Runner

echo "🚀 Starting PR Review Automation System..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your API keys:"
    echo "   - GROQ_API_KEY"
    echo "   - GITHUB_TOKEN"
    echo "   - WEBHOOK_SECRET"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Run the application
echo "🌟 Starting the server..."
python -m app.main