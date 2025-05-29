# 🤑 FinSeek AI - Multi-Agent Finance Assistant

A sophisticated multi-agent finance assistant that delivers spoken market briefs via a Streamlit app. Built with advanced data-ingestion pipelines, vector embeddings for RAG, and orchestrated microservices for comprehensive market intelligence.

## 🏗️ Architecture Overview

### Agent Roles
- **🔗 API Agent** (Port 8000): Polls real-time & historical market data via AlphaVantage/Yahoo Finance
- **🕷️ Scraper Agent** (Port 8001): Crawls financial filings and news using Python loaders
- **🔍 Retriever Agent** (Port 8002): Indexes embeddings in Pinecone and retrieves top-k chunks
- **🧠 LLM Agent** (Port 8003): Synthesizes narrative via language models + STT/TTS pipelines  
- **🎯 Orchestrator** (Port 8004): Coordinates all agents and provides unified API
- **🎛️ Streamlit App** (Port 8501): Beautiful UI with voice I/O and market dashboard

### 🛠️ Technology Stack
- **Microservices**: FastAPI for each agent
- **Orchestration**: Centralized orchestrator with async coordination
- **Voice I/O**: Whisper (STT) + pyttsx3 (TTS)
- **LLM**: Transformers with GPT-2/DialoGPT models
- **Vector Store**: Pinecone for document embeddings
- **Frontend**: Streamlit with audio recording
- **Containerization**: Docker + Docker Compose
- **Deployment**: Kubernetes ready

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Required API Keys (see environment setup)

### 1. Clone and Setup
```bash
git clone <your-repo>
cd finseek_ai
cp environment.env.example .env
# Edit .env with your API keys
```

### 2. Build All Services
```bash
chmod +x build.sh cleanup.sh
./build.sh
```

### 3. Run with Docker Compose
```bash
docker-compose up -d
```

### 4. Access the Application
- **Main App**: http://localhost:8501
- **API Documentation**: 
  - Orchestrator: http://localhost:8004/docs
  - API Agent: http://localhost:8000/docs
  - Other agents: ports 8001-8003

## 🔧 Individual Container Commands

### Build Images
```bash
# API Agent
docker build -t finance/api-agent:latest ./api-agent/

# Scraper Agent  
docker build -t finance/scraper-agent:latest ./scraper-agent/

# Retriever Agent
docker build -t finance/retriever-agent:latest ./retriever-agent/

# Language Agent
docker build -t finance/lang-agent:latest ./lang-agent/

# Orchestrator
docker build -t finance/orchestrator:latest ./orchestrator/

# Streamlit App
docker build -t finance/streamlit-app:latest ./streamlit-app/
```

### Run Individual Containers
```bash
# Create network first
docker network create finance-net

# API Agent
docker run -d --name api-agent \
  --network finance-net \
  -p 8000:8000 \
  -e HUGGINGFACE_API_KEY=${HUGGINGFACE_API_KEY} \
  finance/api-agent:latest

# Scraper Agent
docker run -d --name scraper-agent \
  --network finance-net \
  -p 8001:8001 \
  -e HUGGINGFACE_API_KEY=${HUGGINGFACE_API_KEY} \
  finance/scraper-agent:latest

# Retriever Agent
docker run -d --name retriever-agent \
  --network finance-net \
  -p 8002:8002 \
  -e PINECONE_API_KEY=${PINECONE_API_KEY} \
  -e PINECONE_ENVIRONMENT=${PINECONE_ENVIRONMENT} \
  -e PINECONE_INDEX=${PINECONE_INDEX} \
  finance/retriever-agent:latest

# Language Agent
docker run -d --name lang-agent \
  --network finance-net \
  -p 8003:8003 \
  -e HUGGINGFACE_API_KEY=${HUGGINGFACE_API_KEY} \
  finance/lang-agent:latest

# Orchestrator
docker run -d --name orchestrator \
  --network finance-net \
  -p 8004:8004 \
  finance/orchestrator:latest

# Streamlit App
docker run -d --name streamlit-app \
  --network finance-net \
  -p 8501:8501 \
  -v $(pwd)/streamlit-app:/app \
  finance/streamlit-app:latest
```

## 📊 Portfolio Data

The system uses a portfolio CSV file located at `streamlit-app/portfolio.csv`:

```csv
ticker,quantity,price_per_stock,current_value
GOOGL,68,172.9,11756.2
AAPL,59,200.21,11812.39
JPM,11,265.29,2918.19
MSFT,52,460.69,23955.88
NFLX,90,1211.57,109041.3
```

### Use Case Example
**User Voice Query**: *"What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"*

**AI Response**: *"Today, your Asia tech allocation is 22% of AUM, up from 18% yesterday. TSMC beat estimates by 4%, Samsung missed by 2%. Regional sentiment is neutral with a cautionary tilt due to rising yields."*

## 🎯 Features

### Voice Interface
- 🎤 **Real-time voice recording** with Streamlit audio recorder
- 🔊 **Speech-to-text** using OpenAI Whisper
- 🗣️ **Text-to-speech** responses with pyttsx3
- 📱 **Mobile-friendly** voice interactions

### Market Intelligence
- 📈 **Real-time market data** from multiple sources
- 📰 **News & sentiment analysis** from web scraping
- 🏢 **Earnings surprises** tracking
- 🌏 **Regional focus** (Asia, US, Europe, Global)

### Portfolio Management
- 💼 **Portfolio analysis** with risk exposure
- 📊 **Real-time valuations** and allocations  
- 🎯 **Performance metrics** and insights
- 📋 **Holdings breakdown** with visualizations

### RAG Intelligence
- 🔍 **Vector similarity search** with Pinecone
- 📚 **Document retrieval** from financial filings
- 🧠 **Context-aware responses** using embeddings
- 🔗 **Multi-source data fusion**

## 🛡️ Environment Variables

Create a `.env` file with:

```bash
# Required
HUGGINGFACE_API_KEY=your_huggingface_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=us-east1-gcp
PINECONE_INDEX=finance-agent

# Optional  
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
OPENAI_API_KEY=your_openai_key
```

## 🔄 API Endpoints

### Orchestrator (Port 8004)
- `POST /voice-query` - Process voice input end-to-end
- `POST /market-brief` - Generate text-based market analysis
- `GET /portfolio` - Get portfolio analysis
- `POST /upsert-documents` - Add documents to vector store

### Individual Agent APIs
- **API Agent** (8000): `/market-data`, `/risk-exposure`
- **Scraper Agent** (8001): `/earnings-surprises`, `/news`
- **Retriever Agent** (8002): `/query`, `/upsert`, `/portfolio-analysis`  
- **Lang Agent** (8003): `/stt`, `/generate`, `/tts`

## 🧹 Cleanup

Stop and remove all containers:
```bash
./cleanup.sh
```

Or manually:
```bash
docker-compose down
docker system prune -f
```

## 🏗️ Project Structure

```
finseek_ai/
├── api-agent/           # Market data API service
├── scraper-agent/       # Web scraping service  
├── retriever-agent/     # Vector search & RAG
├── lang-agent/          # LLM + Voice processing
├── orchestrator/        # Service coordination
├── streamlit-app/       # Frontend application
├── k8s/                 # Kubernetes deployments
├── docs/                # Documentation
├── docker-compose.yml   # Multi-service orchestration
├── build.sh            # Build all images
├── cleanup.sh          # Cleanup script
└── README.md           # This file
```

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000-8004 and 8501 are available
2. **API keys**: Verify all required environment variables are set
3. **Pinecone connection**: Check your Pinecone API key and environment
4. **Audio permissions**: Browser needs microphone access for voice features
5. **Container networking**: Ensure Docker network `finance-net` exists

### Logs
```bash
# View orchestrator logs
docker logs orchestrator

# View all service logs
docker-compose logs -f
```

### Health Checks
- http://localhost:8000/health (API Agent)
- http://localhost:8001/health (Scraper Agent)  
- http://localhost:8002/health (Retriever Agent)
- http://localhost:8003/health (Lang Agent)
- http://localhost:8004/health (Orchestrator)

## 🌟 Performance Features

- **Async operations** for parallel data gathering
- **Caching** for frequent API calls
- **Connection pooling** for database operations
- **Graceful error handling** with fallbacks
- **Health monitoring** for all services
- **Horizontal scaling** ready with Kubernetes

## 📈 Future Enhancements

- [ ] **Real-time WebSocket** connections
- [ ] **Advanced voice commands** with intent recognition
- [ ] **Multi-language support** for global markets
- [ ] **Custom alerts** and notifications
- [ ] **Advanced portfolio optimization** algorithms
- [ ] **Integration with brokers** for live trading

## 📝 License

Open source - feel free to use and modify for your needs.

---

**🤑 FinSeek AI** - Your AI-powered financial intelligence assistant with voice interaction and multi-agent architecture.

PINECONE_API_KEY=pcsk_2dDRbj_9dsLDnZTurievR2PHtSNck7Jsw6Nkzi6NC9FTFAGpF47SgoXkrMcTxADkQAzDVS
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_HOST=https://finance-agent-xgjs5rq.svc.aped-4627-b74a.pinecone.io
PINECONE_INDEX=finance-agent
HUGGINGFACE_API_KEY=
