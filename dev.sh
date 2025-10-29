#!/bin/bash

# ChatNShop Intent Classification API - Development Startup Script

echo "🔧 Starting ChatNShop Development Environment..."
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start Qdrant only
echo "🔄 Starting Qdrant database..."
docker-compose up qdrant -d

# Wait for Qdrant to be ready
echo "⏳ Waiting for Qdrant to be ready..."
sleep 5

# Check if Qdrant is healthy
if curl -f http://localhost:6333/health > /dev/null 2>&1; then
    echo "✅ Qdrant is ready"
else
    echo "⚠️ Qdrant health check failed, but continuing..."
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" > /dev/null 2>&1; then
    echo "❌ Dependencies not installed. Please run: pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "🎉 Development environment ready!"
echo "=================================="
echo "📡 API will start on: http://localhost:8000"
echo "🗄️ Qdrant available on: http://localhost:6333"
echo ""
echo "🚀 Starting API with hot-reload..."
echo "   (Press Ctrl+C to stop API only)"
echo "   (Qdrant will keep running in background)"
echo ""
echo "🛑 To stop everything:"
echo "   1. Press Ctrl+C (stops API)"
echo "   2. Run: docker-compose down (stops Qdrant)"
echo ""

# Start the API with hot-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
