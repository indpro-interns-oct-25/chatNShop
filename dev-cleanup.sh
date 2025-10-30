#!/bin/bash

# ChatNShop Development Cleanup Script

echo "🧹 Cleaning up development environment..."
echo "======================================="

# Stop Qdrant container
echo "🔄 Stopping Qdrant container..."
docker-compose down

echo "✅ Development cleanup complete!"
echo ""
echo "📊 What was stopped:"
echo "   - Qdrant Docker container"
echo "   - All related Docker services"
echo ""
echo "💡 Next time you run ./dev.sh, Qdrant will start fresh"
