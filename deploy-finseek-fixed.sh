#!/bin/bash

echo "🚀 FinSeek AI Deployment - Fixed Business Logic"
echo "=============================================="

# Set variables
RESOURCE_GROUP="finseek-rg"
AKS_CLUSTER="finseek-aks"
NAMESPACE="finseek"

# Step 1: Connect to AKS
echo "📡 Connecting to AKS cluster..."
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER

# Step 2: Ensure namespace exists
echo "📁 Setting up namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Step 3: Create secrets
echo "🔐 Creating secrets..."
kubectl create secret generic finseek-secrets \
  --from-literal=pinecone-api-key="pcsk_2dDRbj_9dsLDnZTurievR2PHtSNck7Jsw6Nkzi6NC9FTFAGpF47SgoXkrMcTxADkQAzDVS" \
  --from-literal=huggingface-api-key="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" \
  --namespace $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Step 4: Create config map
echo "⚙️ Creating config map..."
kubectl create configmap finseek-config \
  --from-literal=pinecone-environment="us-east1-gcp" \
  --from-literal=pinecone-index="finance-agent" \
  --namespace $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Step 5: Generate and create portfolio data
echo "📊 Creating portfolio data..."
python3 > /tmp/portfolio.csv << 'EOF'
import pandas as pd

# Asia Tech Focus Portfolio
portfolio_data = {
    "ticker": ["2330.TW", "005930.KS", "9988.HK", "ASML", "TSM", "NVDA"],
    "quantity": [1000, 500, 800, 200, 300, 150],
    "price_per_stock": [95.50, 52.30, 89.20, 720.45, 142.80, 265.40],
    "current_value": [95500, 26150, 71360, 144090, 42840, 39810]
}

df = pd.DataFrame(portfolio_data)
df.to_csv('/tmp/portfolio.csv', index=False)
print("ticker,quantity,price_per_stock,current_value")
print("2330.TW,1000,95.50,95500")
print("005930.KS,500,52.30,26150") 
print("9988.HK,800,89.20,71360")
print("ASML,200,720.45,144090")
print("TSM,300,142.80,42840")
print("NVDA,150,265.40,39810")
EOF

kubectl create configmap portfolio-data \
  --from-file=portfolio.csv=/tmp/portfolio.csv \
  --namespace $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Step 6: Create code ConfigMaps
echo "📦 Creating code ConfigMaps..."

# API Agent
kubectl create configmap api-agent-code \
  --from-file=api-agent/ \
  --namespace $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Scraper Agent  
kubectl create configmap scraper-agent-code \
  --from-file=scraper-agent/ \
  --namespace $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Retriever Agent
kubectl create configmap retriever-agent-code \
  --from-file=retriever-agent/ \
  --namespace $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Lang Agent (lightweight)
kubectl create configmap lang-agent-code \
  --from-file=lang-agent/ \
  --namespace $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Orchestrator (resilient)
kubectl create configmap orchestrator-code \
  --from-file=orchestrator/ \
  --namespace $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Streamlit App
kubectl create configmap streamlit-app-code \
  --from-file=streamlit-app/ \
  --namespace $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Step 7: Apply services
echo "🌐 Creating services..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: api-agent-service
  namespace: $NAMESPACE
spec:
  selector:
    app: api-agent
  ports:
  - port: 8000
    targetPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: scraper-agent-service
  namespace: $NAMESPACE
spec:
  selector:
    app: scraper-agent
  ports:
  - port: 8001
    targetPort: 8001
---
apiVersion: v1
kind: Service
metadata:
  name: retriever-agent-service
  namespace: $NAMESPACE
spec:
  selector:
    app: retriever-agent
  ports:
  - port: 8002
    targetPort: 8002
---
apiVersion: v1
kind: Service
metadata:
  name: lang-agent-service
  namespace: $NAMESPACE
spec:
  selector:
    app: lang-agent
  ports:
  - port: 8003
    targetPort: 8003
---
apiVersion: v1
kind: Service
metadata:
  name: orchestrator-service
  namespace: $NAMESPACE
spec:
  selector:
    app: orchestrator
  ports:
  - port: 8004
    targetPort: 8004
---
apiVersion: v1
kind: Service
metadata:
  name: streamlit-app-service
  namespace: $NAMESPACE
spec:
  type: LoadBalancer
  selector:
    app: streamlit-app
  ports:
  - port: 8501
    targetPort: 8501
EOF

# Step 8: Deploy applications
echo "🚀 Deploying applications..."
kubectl apply -f k8s/fixed-working-deployment.yaml

# Step 9: Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment --all -n $NAMESPACE

# Step 10: Get status
echo "📊 Deployment Status:"
kubectl get pods -n $NAMESPACE

echo "🌐 Service Status:"
kubectl get services -n $NAMESPACE

# Step 11: Get external IP
echo "🔗 Getting external access info..."
EXTERNAL_IP=$(kubectl get service streamlit-app-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -n "$EXTERNAL_IP" ]; then
    echo "✅ FinSeek AI is accessible at: http://$EXTERNAL_IP:8501"
else
    echo "⏳ Waiting for external IP to be assigned..."
    echo "Run: kubectl get service streamlit-app-service -n $NAMESPACE"
fi

echo ""
echo "🎉 FinSeek AI deployment completed!"
echo ""
echo "To monitor the deployment:"
echo "  kubectl get pods -n $NAMESPACE -w"
echo ""
echo "To check logs:"
echo "  kubectl logs -n $NAMESPACE deployment/orchestrator"
echo "  kubectl logs -n $NAMESPACE deployment/api-agent"
echo ""
echo "To test business logic:"
echo "  kubectl run test --rm -i --image=curlimages/curl -n $NAMESPACE -- curl -s http://api-agent-service:8000/health" 