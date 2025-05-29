#!/bin/bash

# Azure Kubernetes Service Deployment Script for FinSeek AI
# This script deploys the multi-agent finance assistant to AKS

echo "🚀 Deploying FinSeek AI to Azure Kubernetes Service"
echo "=================================================="

# Variables
RESOURCE_GROUP="finseek-rg"
CLUSTER_NAME="finseek-aks"
LOCATION="eastus"
ACR_NAME="finseekacr$(date +%s)"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first."
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install it first."
    exit 1
fi

echo "1️⃣ Creating Resource Group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

echo "2️⃣ Creating Azure Container Registry..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic

echo "3️⃣ Creating AKS Cluster with Spot Instances (Ultra Cheap!)..."
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --priority Spot \
  --spot-max-price 0.06 \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 4 \
  --attach-acr $ACR_NAME \
  --generate-ssh-keys \
  --tier Free

echo "4️⃣ Getting AKS Credentials..."
az aks get-credentials --resource-group $RESOURCE_GROUP --name $CLUSTER_NAME

echo "5️⃣ Building and Pushing Images to ACR..."
az acr login --name $ACR_NAME

# Build and push all images
echo "Building API Agent..."
docker build -t $ACR_NAME.azurecr.io/finance/api-agent:latest ./api-agent/
docker push $ACR_NAME.azurecr.io/finance/api-agent:latest

echo "Building Scraper Agent..."
docker build -t $ACR_NAME.azurecr.io/finance/scraper-agent:latest ./scraper-agent/
docker push $ACR_NAME.azurecr.io/finance/scraper-agent:latest

echo "Building Retriever Agent..."
docker build -t $ACR_NAME.azurecr.io/finance/retriever-agent:latest ./retriever-agent/
docker push $ACR_NAME.azurecr.io/finance/retriever-agent:latest

echo "Building Language Agent..."
docker build -t $ACR_NAME.azurecr.io/finance/lang-agent:latest ./lang-agent/
docker push $ACR_NAME.azurecr.io/finance/lang-agent:latest

echo "Building Orchestrator..."
docker build -t $ACR_NAME.azurecr.io/finance/orchestrator:latest ./orchestrator/
docker push $ACR_NAME.azurecr.io/finance/orchestrator:latest

echo "Building Streamlit App..."
docker build -t $ACR_NAME.azurecr.io/finance/streamlit-app:latest ./streamlit-app/
docker push $ACR_NAME.azurecr.io/finance/streamlit-app:latest

echo "6️⃣ Updating Kubernetes manifests with ACR images..."
# Update the deployment file with ACR image names
sed -i "s|finance/|$ACR_NAME.azurecr.io/finance/|g" k8s/deployments-optimized.yaml

echo "7️⃣ Deploying to Kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployments-optimized.yaml
kubectl apply -f k8s/services.yaml

echo "8️⃣ Waiting for deployment to complete..."
kubectl wait --for=condition=available --timeout=300s deployment --all -n finseek

echo "9️⃣ Getting external IP..."
echo "Waiting for LoadBalancer IP..."
kubectl get service streamlit-app-service -n finseek --watch

echo "✅ Deployment complete!"
echo ""
echo "🌐 Access your application:"
echo "   kubectl get service streamlit-app-service -n finseek"
echo ""
echo "📊 Monitor your deployment:"
echo "   kubectl get pods -n finseek"
echo "   kubectl logs -f deployment/streamlit-app -n finseek"
echo ""
echo "💰 Estimated monthly cost: $60-80 (with spot instances)"
echo ""
echo "🧹 To cleanup everything:"
echo "   az group delete --name $RESOURCE_GROUP --yes --no-wait" 