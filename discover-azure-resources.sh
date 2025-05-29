#!/bin/bash

# FinSeek AI - Azure Resource Discovery Script
# This script helps find existing Azure resources for FinSeek AI deployment

echo "🔍 Discovering Azure Resources for FinSeek AI"
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

# Check if Azure CLI is available
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not available"
    exit 1
fi

# Get current subscription
print_status "Current Azure subscription:"
az account show --query '{subscriptionId: id, name: name, tenantId: tenantId}' --output table

echo ""
print_status "Available resource groups:"
echo "=========================="
az group list --query '[].{Name:name, Location:location, ProvisioningState:properties.provisioningState}' --output table

echo ""
print_status "Looking for AKS clusters..."
echo "=========================="
AKS_CLUSTERS=$(az aks list --query '[].{Name:name, ResourceGroup:resourceGroup, Location:location, KubernetesVersion:kubernetesVersion, NodeCount:agentPoolProfiles[0].count}' --output table)

if [ -z "$AKS_CLUSTERS" ] || [[ "$AKS_CLUSTERS" == *"No items"* ]]; then
    print_warning "No AKS clusters found in current subscription"
    echo ""
    print_status "Would you like to create a new AKS cluster? Here's a sample command:"
    echo "az aks create --resource-group myResourceGroup --name myAKSCluster --node-count 2 --enable-addons monitoring --generate-ssh-keys"
else
    print_success "Found AKS clusters:"
    echo "$AKS_CLUSTERS"
    echo ""
    print_status "To connect to an AKS cluster, use:"
    echo "az aks get-credentials --resource-group <RESOURCE_GROUP> --name <CLUSTER_NAME>"
fi

echo ""
print_status "Looking for Container Registries (ACR)..."
echo "========================================"
ACR_REGISTRIES=$(az acr list --query '[].{Name:name, ResourceGroup:resourceGroup, Location:location, LoginServer:loginServer}' --output table)

if [ -z "$ACR_REGISTRIES" ] || [[ "$ACR_REGISTRIES" == *"No items"* ]]; then
    print_warning "No Azure Container Registries found"
    echo ""
    print_status "For FinSeek AI, you might want to create one:"
    echo "az acr create --resource-group myResourceGroup --name myFinSeekACR --sku Basic"
else
    print_success "Found Container Registries:"
    echo "$ACR_REGISTRIES"
fi

echo ""
print_status "Looking for Storage Accounts..."
echo "=============================="
az storage account list --query '[].{Name:name, ResourceGroup:resourceGroup, Location:location, Kind:kind}' --output table

echo ""
print_status "Current kubectl context (if any):"
echo "================================"
if command -v kubectl &> /dev/null; then
    kubectl config current-context 2>/dev/null || print_warning "No kubectl context set"
    echo ""
    kubectl config get-contexts 2>/dev/null || print_warning "No kubectl contexts available"
else
    print_warning "kubectl not found"
fi

echo ""
print_status "🎯 Quick Actions:"
echo "================="
echo "1. To connect to an AKS cluster:"
echo "   az aks get-credentials --resource-group <RG_NAME> --name <CLUSTER_NAME>"
echo ""
echo "2. To list all resources in a resource group:"
echo "   az resource list --resource-group <RG_NAME> --output table"
echo ""
echo "3. To check if FinSeek is already deployed:"
echo "   kubectl get namespaces | grep finseek"
echo "   kubectl get pods -n finseek"
echo ""
echo "4. To create FinSeek AI deployment:"
echo "   ./deploy-to-aks.sh" 