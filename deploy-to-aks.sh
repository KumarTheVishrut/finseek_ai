#!/bin/bash

# FinSeek AI - Azure Kubernetes Service Deployment Script
# This script deploys/updates FinSeek AI on AKS with proper configuration

set -e

echo "🤑 FinSeek AI - AKS Deployment"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed"
    exit 1
fi

if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed"
    exit 1
fi

# Check cluster connection
print_status "Checking AKS cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    print_error "Not connected to AKS cluster"
    echo "Please run: az aks get-credentials --resource-group <your-rg> --name <your-cluster>"
    exit 1
fi

print_success "Connected to AKS cluster"

# Create namespace if it doesn't exist
print_status "Setting up namespace..."
kubectl create namespace finseek --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
print_status "Creating/updating secrets..."
kubectl create secret generic finseek-secrets -n finseek \
    --from-literal=huggingface-api-key=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 \
    --from-literal=pinecone-api-key=pcsk_2dDRbj_9dsLDnZTurievR2PHtSNck7Jsw6Nkzi6NC9FTFAGpF47SgoXkrMcTxADkQAzDVS \
    --dry-run=client -o yaml | kubectl apply -f -

# Create configmap
print_status "Creating/updating configmap..."
kubectl create configmap finseek-config -n finseek \
    --from-literal=pinecone-environment=us-east-1 \
    --from-literal=pinecone-index=finance-agent \
    --dry-run=client -o yaml | kubectl apply -f -

# Generate portfolio data locally and create configmap
print_status "Generating portfolio data..."
python3 generate_portfolio.py

if [ -f "portfolio.csv" ]; then
    print_status "Creating portfolio configmap..."
    kubectl create configmap portfolio-data -n finseek \
        --from-file=portfolio.csv \
        --dry-run=client -o yaml | kubectl apply -f -
    print_success "Portfolio data uploaded to cluster"
else
    print_warning "Portfolio.csv not found, using sample data in retriever-agent"
fi

# Deploy services
print_status "Deploying services..."
kubectl apply -f k8s/services.yaml

# Deploy applications (use optimized deployment)
print_status "Deploying applications..."
kubectl apply -f k8s/deployments-optimized.yaml

# Wait for deployments to be ready
print_status "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment --all -n finseek

# Check deployment status
print_status "Checking deployment status..."
kubectl get pods -n finseek
kubectl get services -n finseek

# Get external IP for streamlit service
print_status "Getting service endpoints..."
echo ""
echo "🌐 Service Endpoints:"
echo "===================="

# Check if streamlit service has external IP
EXTERNAL_IP=$(kubectl get service streamlit-app-service -n finseek -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

if [ "$EXTERNAL_IP" != "pending" ] && [ -n "$EXTERNAL_IP" ]; then
    echo "📊 Streamlit App: http://$EXTERNAL_IP:8501"
    print_success "Streamlit app is accessible at http://$EXTERNAL_IP:8501"
else
    print_warning "External IP is still pending. You can check later with:"
    echo "kubectl get service streamlit-app-service -n finseek"
    echo ""
    echo "Or use port-forwarding to access locally:"
    echo "kubectl port-forward service/streamlit-app-service 8501:8501 -n finseek"
fi

echo ""
echo "🔧 Internal Service URLs (for debugging):"
kubectl get services -n finseek -o custom-columns=NAME:.metadata.name,CLUSTER-IP:.spec.clusterIP,PORT:.spec.ports[0].port

echo ""
print_status "=== DEPLOYMENT SUMMARY ==="
echo "✅ Namespace: finseek"
echo "✅ Secrets: configured"
echo "✅ ConfigMaps: configured"
echo "✅ Services: deployed"
echo "✅ Applications: deployed"
echo ""
echo "🎤 Voice Assistant: Available in the Streamlit app"
echo "💬 Text Analysis: Available in the Streamlit app"
echo "📈 Market Dashboard: Available in the Streamlit app"
echo ""
echo "📊 To troubleshoot issues, run: ./k8s-troubleshoot.sh"
echo "🔄 To restart a service: kubectl rollout restart deployment/<service-name> -n finseek"
echo "📋 To view logs: kubectl logs deployment/<service-name> -n finseek -f"
echo ""
echo "Happy trading! 🚀" 