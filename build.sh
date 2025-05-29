#!/bin/bash

# Build script for FinSeek AI Multi-Agent System

echo "🤑 Building FinSeek AI - Multi-Agent Finance Assistant"
echo "=================================================="

# Create Docker network if it doesn't exist
echo "📡 Creating Docker network..."
docker network create finance-net 2>/dev/null || echo "Network already exists"

# Build all images
echo "🔨 Building API Agent..."
docker build -t finance/api-agent:latest ./api-agent/

echo "🔨 Building Scraper Agent..."
docker build -t finance/scraper-agent:latest ./scraper-agent/

echo "🔨 Building Retriever Agent..."
docker build -t finance/retriever-agent:latest ./retriever-agent/

echo "🔨 Building Language Agent..."
docker build -t finance/lang-agent:latest ./lang-agent/

echo "🔨 Building Orchestrator..."
docker build -t finance/orchestrator:latest ./orchestrator/

echo "🔨 Building Streamlit App..."
docker build -t finance/streamlit-app:latest ./streamlit-app/

echo "✅ All images built successfully!"
echo ""
echo "🚀 To run the complete system:"
echo "   docker-compose up -d"
echo ""
echo "🎯 Individual container commands:"
echo "   docker run -d --name api-agent --network finance-net -p 8000:8000 finance/api-agent:latest"
echo "   docker run -d --name scraper-agent --network finance-net -p 8001:8001 finance/scraper-agent:latest"
echo "   docker run -d --name retriever-agent --network finance-net -p 8002:8002 finance/retriever-agent:latest"
echo "   docker run -d --name lang-agent --network finance-net -p 8003:8003 finance/lang-agent:latest"
echo "   docker run -d --name orchestrator --network finance-net -p 8004:8004 finance/orchestrator:latest"
echo "   docker run -d --name streamlit-app --network finance-net -p 8501:8501 finance/streamlit-app:latest"
echo ""
echo "🌐 Access URLs:"
echo "   Streamlit App: http://localhost:8501"
echo "   API Agent: http://localhost:8000/docs"
echo "   Scraper Agent: http://localhost:8001/docs"
echo "   Retriever Agent: http://localhost:8002/docs"
echo "   Language Agent: http://localhost:8003/docs"
echo "   Orchestrator: http://localhost:8004/docs" 