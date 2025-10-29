#!/bin/bash

# ChatNShop Intent Classification API - Stop Script

echo "🛑 Stopping ChatNShop Intent Classification API..."
echo "================================================="

# Stop services
docker-compose down

echo "✅ Services stopped"
echo "🧹 Cleanup complete"
