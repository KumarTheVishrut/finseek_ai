#!/bin/bash

# FinSeek AI - Azure Cloud Shell Setup Script
# This script sets up the project in Azure Cloud Shell for AKS deployment

echo "🤑 Setting up FinSeek AI in Azure Cloud Shell"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if we're in Cloud Shell
if [ -z "$AZUREPS_HOST_ENVIRONMENT" ] && [ -z "$ACC_CLOUD" ]; then
    print_warning "This script is designed for Azure Cloud Shell"
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --user yfinance pandas requests

# Create project structure
print_status "Creating project structure..."
mkdir -p finseek_ai/{api-agent,scraper-agent,retriever-agent,lang-agent,orchestrator,streamlit-app,k8s,portfolio}

# Create main files with content
print_status "Creating core project files..."

# Generate portfolio script
cat > finseek_ai/generate_portfolio.py << 'EOF'
#!/usr/bin/env python3
import yfinance as yf
import pandas as pd
import random

def generate_portfolio():
    print("🤑 Generating FinSeek AI Portfolio...")
    
    # Asia tech focus tickers
    tickers = ["2330.TW", "005930.KS", "9988.HK", "ASML", "TSM", "BABA", "NVDA", "AAPL", "GOOGL", "MSFT"]
    
    portfolio = []
    selected_tickers = random.sample(tickers, 6)
    
    for ticker in selected_tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
            
            if price is None:
                hist = stock.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                else:
                    continue

            quantity = random.randint(10, 100)
            current_value = round(price * quantity, 2)
            
            holding = {
                "ticker": ticker,
                "quantity": quantity,
                "price_per_stock": round(price, 2),
                "current_value": current_value
            }
            portfolio.append(holding)
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            continue
    
    # Save to CSV
    df = pd.DataFrame(portfolio)
    df.to_csv("portfolio.csv", index=False)
    df.to_csv("streamlit-app/portfolio.csv", index=False)
    
    total_value = sum(holding['current_value'] for holding in portfolio)
    print(f"✅ Generated portfolio with {len(portfolio)} holdings")
    print(f"💰 Total Portfolio Value: ${total_value:,.2f}")
    return True

if __name__ == "__main__":
    generate_portfolio()
EOF

# Create environment file
cat > finseek_ai/environment.env << 'EOF'
# FinSeek AI - Multi-Agent Finance Assistant
# Environment Variables Configuration

# Hugging Face API Key (required for all agents)
HUGGINGFACE_API_KEY=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

# Pinecone Configuration (required for retriever agent)
PINECONE_API_KEY=pcsk_2dDRbj_9dsLDnZTurievR2PHtSNck7Jsw6Nkzi6NC9FTFAGpF47SgoXkrMcTxADkQAzDVS
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX=finance-agent

# Alpha Vantage API Key (for market data)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# OpenAI API Key (optional, for advanced LLM features)
OPENAI_API_KEY=your_openai_api_key_here
EOF

# Create Kubernetes namespace
cat > finseek_ai/k8s/namespace.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: finseek
EOF

# Create quick deploy script
cat > finseek_ai/quick-deploy.sh << 'EOF'
#!/bin/bash
echo "🚀 Quick Deploy to AKS..."

# Generate portfolio data
python3 generate_portfolio.py

# Create namespace
kubectl create namespace finseek --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
kubectl create secret generic finseek-secrets -n finseek \
    --from-literal=huggingface-api-key=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 \
    --from-literal=pinecone-api-key=pcsk_2dDRbj_9dsLDnZTurievR2PHtSNck7Jsw6Nkzi6NC9FTFAGpF47SgoXkrMcTxADkQAzDVS \
    --dry-run=client -o yaml | kubectl apply -f -

# Create configmap
kubectl create configmap finseek-config -n finseek \
    --from-literal=pinecone-environment=us-east-1 \
    --from-literal=pinecone-index=finance-agent \
    --dry-run=client -o yaml | kubectl apply -f -

# Create portfolio configmap
if [ -f "portfolio.csv" ]; then
    kubectl create configmap portfolio-data -n finseek \
        --from-file=portfolio.csv \
        --dry-run=client -o yaml | kubectl apply -f -
fi

echo "✅ Basic setup complete!"
echo "📊 Next steps:"
echo "1. Upload your Docker images or apply deployment manifests"
echo "2. Run: kubectl apply -f k8s/"
echo "3. Check status: kubectl get pods -n finseek"
EOF

chmod +x finseek_ai/generate_portfolio.py finseek_ai/quick-deploy.sh

print_success "Project structure created!"
print_status "Next steps:"
echo "1. cd finseek_ai"
echo "2. Upload your Dockerfiles and source code to each service directory"
echo "3. Upload your Kubernetes manifests to k8s/ directory"
echo "4. Run: ./quick-deploy.sh"
echo ""
print_status "Or if you have the complete project:"
echo "1. git clone your repository or upload files"
echo "2. chmod +x *.sh"
echo "3. ./deploy-to-aks.sh" 