# FinSeek AI - Multi-Agent Finance Assistant

## 🏢 Overview

FinSeek AI is a sophisticated **multi-agent financial assistant** designed to provide comprehensive portfolio analysis, market insights, and voice-enabled financial advisory services with a focus on **Asia Tech markets**. The system leverages microservices architecture deployed on Azure Kubernetes Service (AKS) to deliver scalable, resilient financial intelligence.

## 🎯 Key Features

- **📊 Real-time Portfolio Analysis** - Dynamic risk assessment and allocation insights
- **🗣️ Voice-Enabled Interface** - Speech-to-Text and Text-to-Speech capabilities
- **📈 Market Data Integration** - Live financial data via Yahoo Finance and Alpha Vantage
- **📄 Document Intelligence** - SEC 10-K filing analysis and retrieval
- **🧠 AI-Powered Insights** - LLM-driven financial advisory with RAG capabilities
- **🌏 Asia Tech Focus** - Specialized coverage of Asian technology markets (TSMC, Samsung, Alibaba, etc.)

---

## 🏗️ System Architecture

### Microservices Overview

FinSeek AI employs a **distributed microservices architecture** with 6 core components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Orchestrator  │    │   API Agent     │
│     (UI)        │◄──►│   (Coordinator) │◄──►│ (Market Data)   │
│   Port: 8501    │    │   Port: 8004    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                        ┌───────┼───────┐
                        ▼       ▼       ▼
            ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
            │  Scraper Agent  │ │ Retriever Agent │ │   Lang Agent    │
            │ (SEC Filings)   │ │  (RAG + Vector) │ │ (LLM + Voice)   │
            │  Port: 8001     │ │   Port: 8002    │ │  Port: 8003     │
            └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Component Details

#### 1. **Streamlit App** (Frontend)
- **Purpose**: User interface and client-side interaction
- **Features**: Portfolio dashboard, voice recording, market visualizations
- **Tech Stack**: Streamlit, audio-recorder-streamlit, pandas
- **External Access**: LoadBalancer service with public IP

#### 2. **Orchestrator** (Coordination Hub)
- **Purpose**: Central coordinator managing inter-service communication
- **Features**: Parallel API calls, resilient error handling, service health monitoring
- **Business Logic**: Market brief generation, voice query processing
- **Tech Stack**: FastAPI, httpx (async HTTP), asyncio

#### 3. **API Agent** (Market Data)
- **Purpose**: Financial market data retrieval and risk analysis
- **Data Sources**: Alpha Vantage API, Yahoo Finance
- **Endpoints**:
  - `/historical-data/{symbol}` - Historical price data
  - `/risk-exposure` - Portfolio risk calculation
  - `/health` - Service health check
- **Tech Stack**: FastAPI, requests, pandas

#### 4. **Scraper Agent** (Document Intelligence)
- **Purpose**: SEC filing retrieval and earnings data
- **Data Sources**: SEC EDGAR database, earnings calendars
- **Endpoints**:
  - `/10k-content` - Full 10-K filing retrieval
  - `/earnings-surprises` - Earnings surprise analysis
  - `/debug-filing` - Filing discovery and debugging
- **Tech Stack**: FastAPI, BeautifulSoup4, sec-cik-mapper, requests

#### 5. **Retriever Agent** (Vector Database & RAG)
- **Purpose**: Document storage, similarity search, portfolio analysis
- **Data Sources**: Pinecone vector database, portfolio CSV data
- **Features**: Semantic search, document embedding, portfolio risk assessment
- **Endpoints**:
  - `/query` - Semantic document search
  - `/upsert` - Document storage
  - `/portfolio-analysis` - Portfolio risk and allocation analysis
- **Tech Stack**: FastAPI, Pinecone, sentence-transformers, pandas

#### 6. **Lang Agent** (LLM & Voice)
- **Purpose**: Natural language processing and voice interface
- **Features**: Speech-to-text, text generation, text-to-speech
- **LLM Integration**: HuggingFace Inference API (DistilGPT-2)
- **Endpoints**:
  - `/stt` - Speech to text conversion
  - `/generate` - LLM text generation
  - `/tts` - Text to speech conversion
- **Tech Stack**: FastAPI, HuggingFace API, espeak-ng, requests

---

## 🛠️ Technology Stack

### Core Technologies

| Component | Language | Framework | Database/Storage | External APIs |
|-----------|----------|-----------|------------------|---------------|
| **Frontend** | Python | Streamlit | - | - |
| **Orchestrator** | Python | FastAPI | - | Internal Services |
| **API Agent** | Python | FastAPI | - | Alpha Vantage |
| **Scraper Agent** | Python | FastAPI | - | SEC EDGAR |
| **Retriever Agent** | Python | FastAPI | Pinecone (Vector DB) | Pinecone API |
| **Lang Agent** | Python | FastAPI | - | HuggingFace API |

### Infrastructure Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Cloud Platform                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Azure Kubernetes Service (AKS)             │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │ │
│  │  │   Node 1    │ │   Node 2    │ │   Node 3    │      │ │
│  │  │ (Standard)  │ │ (Standard)  │ │ (Standard)  │      │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │ Load Balancer│ │   Secrets    │ │  ConfigMaps  │       │
│  │  (External)  │ │  Management  │ │   (Config)   │       │
│  └──────────────┘ └──────────────┘ └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Configuration

- **Container Runtime**: Docker (python:3.11-slim base images)
- **Orchestration**: Kubernetes 1.31.8
- **Service Mesh**: Native Kubernetes services
- **Configuration Management**: ConfigMaps and Secrets
- **Storage**: EmptyDir volumes, ConfigMap mounts
- **Networking**: ClusterIP for internal, LoadBalancer for external access

---

## 🌐 Cloud Infrastructure

### Azure Resources

#### Resource Group: `finseek-rg`
- **Location**: Central India
- **Purpose**: Logical container for all FinSeek AI resources

#### AKS Cluster: `finseek-aks`
- **Node Count**: 2 Standard nodes
- **Kubernetes Version**: 1.31.8
- **VM Size**: Standard_DS2_v2
- **Network Plugin**: kubenet
- **DNS**: kube-dns

#### External Services Integration

1. **Pinecone Vector Database**
   - **Environment**: us-east1-gcp
   - **Index**: finance-agent
   - **Dimensions**: 384 (sentence-transformers/all-MiniLM-L6-v2)
   - **Metric**: Cosine similarity

2. **HuggingFace API**
   - **Model**: distilgpt2 (lightweight GPT-2 variant)
   - **Purpose**: Financial text generation
   - **Fallback**: Template-based responses

3. **Alpha Vantage API**
   - **Purpose**: Historical market data
   - **Rate Limits**: 5 calls/minute (free tier)
   - **Data**: Daily/weekly/monthly price series

### Network Architecture

```
Internet
    │
    ▼
┌─────────────────┐
│  Load Balancer  │ (Public IP: 135.235.185.126)
│   (Azure LB)    │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ AKS Cluster     │
│ (Internal Net)  │
│                 │
│ Services:       │
│ • api-agent     │ :8000
│ • scraper-agent │ :8001  
│ • retriever     │ :8002
│ • lang-agent    │ :8003
│ • orchestrator  │ :8004
│ • streamlit     │ :8501
└─────────────────┘
```

---

## 💼 Business Logic & Data Flow

### Core Business Processes

#### 1. **Market Brief Generation**
```
User Query → Orchestrator → Parallel Data Gathering:
├── Portfolio Analysis (Retriever Agent)
├── Risk Exposure (API Agent) 
├── Earnings Data (Scraper Agent)
└── Document Search (Retriever Agent)
     ↓
Context Building → LLM Generation (Lang Agent) → Response
```

#### 2. **Voice Query Processing**
```
Audio Input → STT (Lang Agent) → Market Brief → TTS (Lang Agent) → Audio Output
```

#### 3. **Portfolio Analysis**
```
Portfolio CSV → Risk Calculation → Document Retrieval → Analysis Report
```

### Data Models

#### Portfolio Structure
```python
{
    "ticker": "2330.TW",           # Taiwan Semiconductor
    "quantity": 1000,              # Number of shares
    "price_per_stock": 95.50,      # Current price (USD)
    "current_value": 95500,        # Total position value
    "allocation_pct": 23.4         # Portfolio percentage
}
```

#### Risk Exposure Model
```python
{
    "risk_exposure": 16.8,         # Percentage risk
    "tickers_analyzed": ["2330.TW", "005930.KS"],
    "asia_tech_exposure": 2,       # Count of Asia tech stocks
    "risk_level": "Medium"         # Risk classification
}
```

### API Endpoints Summary

| Service | Endpoint | Method | Purpose |
|---------|----------|--------|---------|
| **API Agent** | `/historical-data/{symbol}` | GET | Historical price data |
| | `/risk-exposure` | GET | Portfolio risk calculation |
| **Scraper Agent** | `/10k-content` | GET | SEC filing retrieval |
| | `/earnings-surprises` | GET | Earnings analysis |
| **Retriever Agent** | `/query` | POST | Document search |
| | `/portfolio-analysis` | GET | Portfolio insights |
| **Lang Agent** | `/stt` | POST | Speech to text |
| | `/generate` | POST | Text generation |
| | `/tts` | POST | Text to speech |
| **Orchestrator** | `/market-brief` | POST | Comprehensive analysis |
| | `/voice-query` | POST | Voice processing |
| | `/service-status` | GET | Health monitoring |

---

## 🚀 Deployment Process

### Prerequisites
- Azure CLI installed and authenticated
- kubectl configured for AKS access
- Access to Azure subscription with AKS permissions

### Deployment Steps

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd finseek_ai
   ```

2. **Azure Setup**
   ```bash
   # Connect to AKS
   az aks get-credentials --resource-group finseek-rg --name finseek-aks
   ```

3. **Deploy FinSeek AI**
   ```bash
   chmod +x deploy-finseek-fixed.sh
   ./deploy-finseek-fixed.sh
   ```

4. **Verify Deployment**
   ```bash
   kubectl get pods -n finseek
   kubectl get services -n finseek
   ```

### Configuration Management

#### Secrets (Kubernetes Secrets)
```yaml
finseek-secrets:
  - pinecone-api-key: "pcsk_..."
  - huggingface-api-key: "hf_..."
```

#### Configuration (ConfigMaps)
```yaml
finseek-config:
  - pinecone-environment: "us-east1-gcp"
  - pinecone-index: "finance-agent"

portfolio-data:
  - portfolio.csv: # Asia tech portfolio data
```

#### Code Deployment (ConfigMaps)
Each service has its code mounted via ConfigMaps:
- `api-agent-code`
- `scraper-agent-code` 
- `retriever-agent-code`
- `lang-agent-code`
- `orchestrator-code`
- `streamlit-app-code`

---

## 🔧 Development & Maintenance

### Local Development

1. **Prerequisites**
   ```bash
   python 3.11+
   pip install -r requirements.txt
   ```

2. **Environment Setup**
   ```bash
   cp environment.env.example environment.env
   # Edit environment.env with your API keys
   ```

3. **Run Services Locally**
   ```bash
   # Terminal 1 - API Agent
   cd api-agent && uvicorn api:app --port 8000
   
   # Terminal 2 - Scraper Agent  
   cd scraper-agent && uvicorn scraper_agent:app --port 8001
   
   # Continue for other services...
   ```

### Monitoring & Troubleshooting

#### Health Checks
```bash
# Check all service health
kubectl run test --rm -i --image=curlimages/curl -n finseek -- \
  curl -s http://orchestrator-service:8004/service-status
```

#### Log Analysis
```bash
# View orchestrator logs
kubectl logs -n finseek deployment/orchestrator -f

# View all service logs
for service in api-agent scraper-agent retriever-agent lang-agent orchestrator; do
  echo "=== $service ==="
  kubectl logs -n finseek deployment/$service --tail=10
done
```

#### Performance Monitoring
```bash
# Resource usage
kubectl top pods -n finseek
kubectl top nodes

# Service connectivity test
./k8s-troubleshoot.sh
```

### Scaling & Optimization

#### Horizontal Pod Autoscaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orchestrator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orchestrator
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### Resource Optimization
- **API Agent**: 256Mi memory, 100m CPU (lightweight data processing)
- **Lang Agent**: 256Mi memory, 200m CPU (LLM API calls)
- **Retriever Agent**: 1Gi memory, 500m CPU (vector operations)
- **Orchestrator**: 512Mi memory, 300m CPU (coordination logic)

---

## 🛡️ Security Considerations

### API Security
- **Authentication**: Service-to-service via Kubernetes service discovery
- **API Keys**: Stored in Kubernetes Secrets
- **Network Policies**: Default deny with explicit allow rules
- **TLS**: HTTPS for external LoadBalancer

### Data Protection
- **Secrets Management**: Kubernetes native secrets with base64 encoding
- **Portfolio Data**: Stored in ConfigMaps (non-sensitive sample data)
- **Vector Database**: Pinecone with API key authentication
- **External APIs**: HTTPS connections with timeout limits

### Access Control
- **RBAC**: Kubernetes role-based access control
- **Namespace Isolation**: All resources in `finseek` namespace
- **Service Accounts**: Minimal privilege principle

---

## 📈 Performance & Scalability

### Current Performance Metrics
- **Response Time**: < 5 seconds for market brief generation
- **Throughput**: 10-15 concurrent users supported
- **Availability**: 99.5% uptime target
- **Error Rate**: < 2% with graceful degradation

### Scalability Features
- **Microservices**: Independent scaling per component
- **Async Processing**: Non-blocking I/O for API calls
- **Caching**: Response caching for static data
- **Circuit Breakers**: Resilient failure handling

### Resource Requirements
```
Minimum Cluster Size: 2 nodes (Standard_DS2_v2)
Total Memory: ~3Gi allocated
Total CPU: ~1.2 cores allocated
Storage: Minimal (ConfigMaps only)
Network: Standard Azure networking
```

---

## 🔮 Future Enhancements

### Short-term Roadmap
- **Real-time Data Streaming**: WebSocket connections for live market data
- **Advanced Portfolio Optimization**: Modern Portfolio Theory implementation
- **Enhanced Voice Interface**: Improved STT/TTS with cloud services
- **Mobile App**: React Native or Flutter mobile client

### Long-term Vision
- **Multi-region Deployment**: Global availability with regional data
- **Advanced AI Models**: Fine-tuned financial LLMs
- **Regulatory Compliance**: SOX, GDPR, and financial regulations
- **Institutional Features**: Multi-tenant support, advanced analytics

### Technology Evolution
- **Cloud Native**: Migration to Azure Container Apps or Service Mesh
- **Event-Driven Architecture**: Apache Kafka for real-time data streams
- **Machine Learning Pipeline**: MLOps for model training and deployment
- **Advanced Analytics**: Time series forecasting, sentiment analysis

---

## 📞 Support & Contact

### Documentation
- **API Documentation**: Available at `http://<service>:port/docs` (FastAPI auto-docs)
- **Architecture Diagrams**: Located in `/docs` directory
- **Deployment Guides**: Step-by-step in this README

### Troubleshooting
- **Common Issues**: Check logs with `kubectl logs`
- **Service Discovery**: Verify with `kubectl get services -n finseek`
- **Health Checks**: Use `/health` endpoints for all services

### Development Team
- **Architecture**: Multi-agent microservices design
- **DevOps**: Azure AKS with Kubernetes orchestration
- **AI/ML**: LLM integration with financial domain expertise
- **Frontend**: Streamlit-based user interface

---

## 📄 License & Usage

This project is designed for educational and demonstration purposes, showcasing modern cloud-native financial technology architecture with AI integration.

**Key Technologies Demonstrated:**
- Microservices Architecture
- Kubernetes Orchestration  
- Azure Cloud Platform
- AI/ML Integration
- Financial Data Processing
- Voice Interface Development

---

*FinSeek AI - Transforming Financial Advisory with AI-Powered Multi-Agent Systems* 🚀
