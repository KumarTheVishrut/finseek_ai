#!/bin/bash

# FinSeek AI - Kubernetes Troubleshooting Script for AKS
# This script helps diagnose issues with the FinSeek AI deployment on Azure Kubernetes Service

echo "🤑 FinSeek AI - Kubernetes Troubleshooting"
echo "=========================================="

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

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if connected to AKS cluster
print_status "Checking cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    print_error "Not connected to Kubernetes cluster. Please run 'az aks get-credentials' first."
    exit 1
fi

print_success "Connected to Kubernetes cluster"

# Check namespace
print_status "Checking finseek namespace..."
if kubectl get namespace finseek &> /dev/null; then
    print_success "Namespace 'finseek' exists"
else
    print_warning "Namespace 'finseek' not found"
    echo "Creating namespace..."
    kubectl create namespace finseek
fi

# Check secrets
print_status "Checking secrets..."
if kubectl get secret finseek-secrets -n finseek &> /dev/null; then
    print_success "Secrets exist"
else
    print_error "Secrets not found. You need to create them:"
    echo "kubectl create secret generic finseek-secrets -n finseek \\"
    echo "  --from-literal=huggingface-api-key=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 \\"
    echo "  --from-literal=pinecone-api-key=pcsk_2dDRbj_9dsLDnZTurievR2PHtSNck7Jsw6Nkzi6NC9FTFAGpF47SgoXkrMcTxADkQAzDVS"
fi

# Check ConfigMap
print_status "Checking ConfigMap..."
if kubectl get configmap finseek-config -n finseek &> /dev/null; then
    print_success "ConfigMap exists"
else
    print_error "ConfigMap not found. Creating it..."
    kubectl create configmap finseek-config -n finseek \
        --from-literal=pinecone-environment=us-east-1 \
        --from-literal=pinecone-index=finance-agent
fi

# Check deployments
print_status "Checking deployments status..."
echo ""
kubectl get deployments -n finseek -o wide

echo ""
print_status "Checking services status..."
kubectl get services -n finseek -o wide

echo ""
print_status "Checking pods status..."
kubectl get pods -n finseek -o wide

echo ""
print_status "Checking for failing pods..."
FAILED_PODS=$(kubectl get pods -n finseek --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
if [ "$FAILED_PODS" -gt 0 ]; then
    print_warning "Found $FAILED_PODS non-running pods:"
    kubectl get pods -n finseek --field-selector=status.phase!=Running
    
    echo ""
    print_status "Getting logs for failing pods..."
    kubectl get pods -n finseek --field-selector=status.phase!=Running --no-headers | awk '{print $1}' | while read pod; do
        echo "--- Logs for $pod ---"
        kubectl logs $pod -n finseek --tail=20
        echo ""
    done
else
    print_success "All pods are running"
fi

# Test service connectivity
echo ""
print_status "Testing service connectivity..."

services=("api-agent-service:8000" "scraper-agent-service:8001" "retriever-agent-service:8002" "lang-agent-service:8003" "orchestrator-service:8004")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    print_status "Testing $name..."
    
    # Create a temporary pod to test connectivity
    kubectl run test-connectivity --image=curlimages/curl --rm -i --restart=Never -n finseek -- \
        curl -s -o /dev/null -w "%{http_code}" "http://$service/health" --connect-timeout 5 --max-time 10 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "$name is reachable"
    else
        print_error "$name is not reachable"
    fi
done

# Check portfolio data
echo ""
print_status "Checking portfolio data access..."
if kubectl exec -n finseek deployment/retriever-agent -- ls /app/portfolio.csv &> /dev/null; then
    print_success "Portfolio file found in retriever-agent"
else
    print_warning "Portfolio file not found in retriever-agent"
fi

echo ""
print_status "=== TROUBLESHOOTING SUMMARY ==="
echo "1. To view logs for a specific service:"
echo "   kubectl logs deployment/<service-name> -n finseek -f"
echo ""
echo "2. To restart a service:"
echo "   kubectl rollout restart deployment/<service-name> -n finseek"
echo ""
echo "3. To check service endpoints:"
echo "   kubectl get endpoints -n finseek"
echo ""
echo "4. To port-forward and test locally:"
echo "   kubectl port-forward service/streamlit-app-service 8501:8501 -n finseek"
echo ""
echo "5. Common issues:"
echo "   - Image pull issues: Check if images are built and pushed to registry"
echo "   - Service discovery: Ensure service names match in orchestrator.py"
echo "   - Resource limits: Check if pods are being OOMKilled"
echo "   - Secret/ConfigMap issues: Verify environment variables" 