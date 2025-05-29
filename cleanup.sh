#!/bin/bash

# Cleanup script for FinSeek AI Multi-Agent System

echo "🧹 Cleaning up FinSeek AI - Multi-Agent Finance Assistant"
echo "======================================================="

# Stop and remove containers
echo "🛑 Stopping containers..."
docker stop api-agent scraper-agent retriever-agent lang-agent orchestrator streamlit-app 2>/dev/null || true

echo "🗑️  Removing containers..."
docker rm api-agent scraper-agent retriever-agent lang-agent orchestrator streamlit-app 2>/dev/null || true

# Remove images (optional - uncomment if you want to remove images too)
echo "🗑️  Removing images..."
docker rmi finance/api-agent:latest finance/scraper-agent:latest finance/retriever-agent:latest finance/lang-agent:latest finance/orchestrator:latest finance/streamlit-app:latest 2>/dev/null || true

# Remove network
echo "🗑️  Removing network..."
docker network rm finance-net 2>/dev/null || true

# Clean up dangling images and volumes
echo "🧽 Cleaning up dangling resources..."
docker system prune -f

echo "✅ Cleanup completed!"
echo ""
echo "🔄 To rebuild everything:"
echo "   ./build.sh" 