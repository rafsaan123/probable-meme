#!/bin/bash

# Start BTEB Results API Server
echo "🚀 Starting BTEB Results API Server..."

# Check if virtual environment exists
if [ ! -d "api_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv api_env
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source api_env/bin/activate

# Install requirements
echo "📥 Installing API requirements..."
pip install -r api_requirements.txt

# Start the API server
echo "🌐 Starting API server on http://localhost:3001"
echo "📡 Available endpoints:"
echo "  POST /api/search-result - Search for student results"
echo "  GET  /api/regulations/<program> - Get available regulations"
echo "  GET  /health - Health check"
python api_server.py


