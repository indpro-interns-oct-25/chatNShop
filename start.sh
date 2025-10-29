#!/bin/bash

# ChatNShop Intent Classification API - Production Startup Script

echo "🚀 Starting ChatNShop Intent Classification API..."
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

echo "✅ Docker is running"
echo "✅ docker-compose is available"

# Start services
echo "🔄 Starting services with docker-compose..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check Qdrant
if curl -f http://localhost:6333/health > /dev/null 2>&1; then
    echo "✅ Qdrant is healthy"
else
    echo "⚠️ Qdrant health check failed"
fi

# Check API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Intent Classification API is healthy"
else
    echo "⚠️ API health check failed"
fi

echo ""
echo "🎉 ChatNShop Intent Classification API is running!"
echo "=================================================="
echo "📡 API URL: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo "🗄️ Qdrant: http://localhost:6333"
echo ""
echo "🧪 Test the API:"
echo "curl -X POST \"http://localhost:8000/classify\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"text\": \"add to cart\"}'"
echo ""
echo "🛑 To stop: docker-compose down"
echo "📊 To view logs: docker-compose logs -f"
