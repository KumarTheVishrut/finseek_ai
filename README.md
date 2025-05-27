# FinSeek AI - Multi-Agent Finance Assistant

A sophisticated multi-agent system that delivers spoken market briefs via a Streamlit interface. The system combines real-time market data, financial document analysis, and natural language processing to provide comprehensive financial insights.

## 🚀 Features

- Real-time market data analysis via Yahoo Finance API
- Document analysis of financial filings
- Voice interface with STT/TTS capabilities
- RAG-powered financial insights
- Multi-agent architecture with specialized components

## 🏗️ Architecture

- **API Agent**: Real-time market data polling
- **Scraper Agent**: Financial document crawling
- **Retriever Agent**: Vector store management and RAG
- **Analysis Agent**: Financial data analysis
- **Language Agent**: HuggingFace-powered text generation
- **Voice Agent**: Speech-to-Text and Text-to-Speech

## 🛠️ Tech Stack

- FastAPI for microservices
- Streamlit for UI
- CrewAI for agent orchestration
- FAISS for vector storage
- HuggingFace Transformers for LLM
- gTTS for voice processing
- LangChain for LLM integration

## 📦 Setup

1. Clone the repository
2. Install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run with Docker Compose:
```bash
docker-compose up --build
```

5. Access the UI at http://localhost:8501

## 🚢 Deployment

### Kubernetes Deployment

1. Create namespace:
```bash
kubectl create namespace finseek
```

2. Create secrets and configmap:
```bash
# Update k8s/config.yaml with your actual values
kubectl apply -f k8s/config.yaml -n finseek
```

3. Deploy services:
```bash
kubectl apply -f k8s/deployment.yaml -n finseek
kubectl apply -f k8s/service.yaml -n finseek
```

4. Check deployment status:
```bash
kubectl get pods -n finseek
kubectl get services -n finseek
```

### Cloud Run Deployment

1. Enable required APIs:
```bash
gcloud services enable cloudbuild.googleapis.com run.googleapis.com
```

2. Set up Cloud Build trigger:
```bash
gcloud builds triggers create github \
  --repo-name=your-repo-name \
  --branch-pattern=main \
  --build-config=cloudbuild.yaml \
  --substitutions=_HUGGINGFACE_API_KEY=your-key,_PINECONE_API_KEY=your-key,_PINECONE_ENVIRONMENT=your-env,_PINECONE_INDEX=your-index
```

3. Deploy manually (if needed):
```bash
gcloud builds submit --config=cloudbuild.yaml
```

### Environment Variables

Required environment variables:
- `HUGGINGFACE_API_KEY`: For HuggingFace model access
- `PINECONE_API_KEY`: For vector storage
- `PINECONE_ENVIRONMENT`: Your Pinecone environment
- `PINECONE_INDEX`: Your Pinecone index name

### Resource Requirements

- API Agent: 512Mi RAM, 1 CPU
- Scraper Agent: 512Mi RAM, 1 CPU
- Retriever Agent: 1Gi RAM, 1 CPU
- Language Agent: 2Gi RAM, 2 CPU
- Streamlit App: 512Mi RAM, 1 CPU

## 📚 Documentation

Detailed documentation for each component is available in the `/docs` directory.

## 🤖 AI Tools Usage

This project was developed with assistance from:
- Claude 3.5 Sonnet for code generation and architecture design
- GitHub Copilot for code completion
- HuggingFace Transformers for LLM capabilities

## 📄 License

MIT License



PINECONE_API_KEY=pcsk_2dDRbj_9dsLDnZTurievR2PHtSNck7Jsw6Nkzi6NC9FTFAGpF47SgoXkrMcTxADkQAzDVS
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_HOST=https://finance-agent-xgjs5rq.svc.aped-4627-b74a.pinecone.io
PINECONE_INDEX=finance-agent
HUGGINGFACE_API_KEY=
