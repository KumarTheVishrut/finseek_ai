#!/bin/bash

# FinSeek AI - Complete Startup Script
# This script builds images, creates network, generates portfolio data, and starts all services

set -e

echo "🤑 FinSeek AI - Multi-Agent Finance Assistant Startup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing containers
print_status "Stopping any existing FinSeek containers..."
docker stop finseek-api finseek-scraper finseek-retriever finseek-lang finseek-orchestrator finseek-streamlit 2>/dev/null || true
docker rm finseek-api finseek-scraper finseek-retriever finseek-lang finseek-orchestrator finseek-streamlit 2>/dev/null || true

# Create network if it doesn't exist
print_status "Creating finance-net network..."
docker network create finance-net 2>/dev/null || print_warning "Network finance-net already exists"

# Build all images
print_status "Building Docker images..."
docker build -t finance/api-agent:latest ./api-agent
docker build -t finance/scraper-agent:latest ./scraper-agent
docker build -t finance/retriever-agent:latest ./retriever-agent
docker build -t finance/lang-agent:latest ./lang-agent
docker build -t finance/orchestrator:latest ./orchestrator
docker build -t finance/streamlit-app:latest ./streamlit-app

print_success "All images built successfully!"

# Generate portfolio data
print_status "Generating portfolio data..."
python3 generate_portfolio.py

# Start services in dependency order
print_status "Starting API Agent..."
docker run -d \
    --name finseek-api \
    --network finance-net \
    -p 8000:8000 \
    finance/api-agent:latest

print_status "Waiting for API Agent to be ready..."
sleep 5

print_status "Starting Retriever Agent..."
docker run -d \
    --name finseek-retriever \
    --network finance-net \
    -p 8002:8002 \
    --env-file environment.env \
    -v $(pwd)/portfolio.csv:/app/portfolio.csv:ro \
    finance/retriever-agent:latest

print_status "Starting Language Agent..."
docker run -d \
    --name finseek-lang \
    --network finance-net \
    -p 8003:8003 \
    --env-file environment.env \
    finance/lang-agent:latest

print_status "Starting Scraper Agent..."
docker run -d \
    --name finseek-scraper \
    --network finance-net \
    -p 8001:8001 \
    --env-file environment.env \
    finance/scraper-agent:latest

print_status "Starting Orchestrator..."
docker run -d \
    --name finseek-orchestrator \
    --network finance-net \
    -p 8004:8004 \
    --env-file environment.env \
    finance/orchestrator:latest

print_status "Waiting for orchestrator to be ready..."
sleep 10

print_status "Starting Streamlit App..."
docker run -d \
    --name finseek-streamlit \
    --network finance-net \
    -p 8501:8501 \
    --env-file environment.env \
    -v $(pwd)/streamlit-app:/app \
    finance/streamlit-app:latest

print_success "All services started successfully!"

echo ""
echo "🎉 FinSeek AI is now running!"
echo "================================"
echo "📊 Streamlit App: http://localhost:8501"
echo "🤖 API Agent: http://localhost:8000"
echo "🕷️  Scraper Agent: http://localhost:8001"
echo "🔍 Retriever Agent: http://localhost:8002"
echo "🧠 Language Agent: http://localhost:8003"
echo "🎭 Orchestrator: http://localhost:8004"
echo ""
echo "🎤 Voice Assistant: Available in the Streamlit app"
echo "💬 Text Analysis: Available in the Streamlit app"
echo "📈 Market Dashboard: Available in the Streamlit app"
echo ""
echo "To stop all services, run:"
echo "docker stop finseek-api finseek-scraper finseek-retriever finseek-lang finseek-orchestrator finseek-streamlit"
echo ""
echo "To view logs for a service, run:"
echo "docker logs <service-name> -f"
echo ""
echo "Happy trading! 🚀" 